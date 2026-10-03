"""Value masking: ``norm``, ``is_sensitive``, ``hide_secrets``, ``redactor``, ``mask_png``, plus
account-id masking (``IdMask``, ``safe_redactor``) and ``no_session`` for logged URLs.

Moved unchanged from the notebooks. ``redactor`` is discovery's (with ``mask=``); replay's own
variant differs only in its number pattern -- whole numbers only, never the '1' in 'rung1' -- so it
is ``REPLAY_NUMBER``, passed as ``redactor(values, number=REPLAY_NUMBER)``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

import numpy as np
from numpy.typing import NDArray

from cua.vision.look import Box, decode, encode

if TYPE_CHECKING:
    from cua.config import SiteProfile

NUMBER = re.compile(r"\$?\d[\d,]*(?:\.\d+)?")  # discovery
REPLAY_NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?(?!\w)")  # whole numbers only

OcrFn = Callable[[NDArray[np.uint8]], list[tuple[str, Box]]]


def _num(text: str) -> str:
    n = text.lstrip("$").replace(",", "")
    return n.rstrip("0").rstrip(".") if "." in n else n


def redactor(
    values: set[str], mask: str = "***", number: re.Pattern[str] = NUMBER
) -> Callable[[str], str]:
    """text -> text with every value masked. Numbers match however they are written
    ('100000' = '$100,000.00'); words match whole, case-insensitively ('IL' never hits 'Bill'),
    with any spacing between their words ('1 Main' also hits OCR's '1Main')."""
    nums = {_num(v) for v in values if number.fullmatch(v.strip())}
    words = sorted(
        (v for v in values if len(v.strip()) > 1 and not number.fullmatch(v.strip())),
        key=len,
        reverse=True,
    )
    spaced = (r"\s*".join(map(re.escape, w.split())) for w in words)  # '1Main' is '1 Main'
    word_re = re.compile("|".join(rf"(?<!\w){w}(?!\w)" for w in spaced), re.I) if words else None

    def redact(text: str) -> str:
        text = number.sub(lambda m: mask if _num(m.group()) in nums else m.group(), text)
        return word_re.sub(mask, text) if word_re else text

    return redact


def norm(text: str | None) -> str:
    return " ".join((text or "").casefold().split()).rstrip(".:!?").strip()


def is_sensitive(label: str, sensitive_words: Iterable[str]) -> bool:
    return any(w in label.casefold() for w in sensitive_words)


def hide_secrets(text: str, secrets: Mapping[str, str]) -> str:
    """Each secret value -> ``<name>``. ``secrets`` maps a secret NAME to its value."""
    for name, value in secrets.items():
        if value:
            text = text.replace(value, f"<{name}>")
    return text


@dataclass(frozen=True)
class IdMask:
    """An account id keeps only its last ``visible`` digits: '#98765' -> '#***765'.

    An id is a run of at least ``min_digits`` digits standing on its own. Deliberately NOT an id:
    an amount ('$12345', '-$12345', '12345.50', '12,345'), digits glued to a letter or a digit
    run inside a word (a timestamp '20261002T005633Z', a hash or session token 'ab12345c'),
    digits after a '-' (a model name '...-4-5-20250929'), and anything shorter (step indexes,
    pixels, a viewport). An all-digit hash or epoch stamp would be masked: harmless."""

    min_digits: int = 5
    visible: int = 3

    @classmethod
    def for_site(cls, site: SiteProfile) -> IdMask:
        return cls(site.id_min_digits, site.id_visible_digits)

    @property
    def pattern(self) -> re.Pattern[str]:
        return re.compile(
            rf"(?<![^\W_])(?<![$\-])(?<!\d[.,])\d{{{self.min_digits},}}(?![^\W_])(?![.,]\d)"
        )

    def __call__(self, text: str) -> str:
        return self.pattern.sub(lambda m: "***" + m.group()[-self.visible :], text)

    def name(self, text: str) -> str:
        """For a name or a path (``[a-z0-9_]`` only): the last digits, no stars."""
        return self.pattern.sub(lambda m: m.group()[-self.visible :], text)

    def spans(self, text: str) -> list[tuple[int, int]]:
        """The hidden characters of each id: (start, end) before its visible digits."""
        return [(m.start(), m.end() - self.visible) for m in self.pattern.finditer(text)]


def safe_redactor(
    values: set[str],
    secrets: Mapping[str, str],
    ids: IdMask,
    number: re.Pattern[str] = NUMBER,
) -> Callable[[str], str]:
    """Secrets masked whole, then ids to their last digits, then the run's values. Ids come before
    the values so an account the goal named still shows its last digits; secrets come first so a
    digits-only secret is never half shown."""
    hide = redactor({v for v in secrets.values() if v}, number=number)
    rest = redactor({v for v in values if v not in secrets.values()}, number=number)
    return lambda text: rest(ids(hide(text)))


def no_session(url: str, query: bool = False) -> str:
    """The URL without its ``;jsessionid=...`` (a session token) and, unless ``query``, without
    its query (it may hold a value)."""
    parts = urlsplit(url)
    path = parts.path.split(";")[0]
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query if query else "", ""))


def _glyphs(img: NDArray[np.uint8], b: Box) -> list[tuple[int, int]]:
    """The box's ink column runs, left to right (x ranges): one per glyph when glyphs are apart.
    Ink is darker than the middle of the box's own grey range."""
    grey = img[b.y1 : b.y2, b.x1 : b.x2].min(axis=2).astype(int)
    if grey.size == 0:
        return []
    ink = (grey < (int(grey.max()) + int(grey.min())) // 2).any(axis=0)
    edges = np.diff(np.concatenate([[0], ink.astype(int), [0]]))
    starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
    return [(b.x1 + int(x), b.x1 + int(y)) for x, y in zip(starts, ends, strict=True)]


def _hidden_x(
    img: NDArray[np.uint8], b: Box, text: str, cut: tuple[int, int]
) -> tuple[int, int] | None:
    """The x range of the id's hidden digits, found by counting glyphs from the box's right end
    (OCR gives no per-character boxes). None when the glyphs cannot be told apart (no ink, or two
    touching digits read as one wide run): the caller then blacks out the whole box."""
    first, tail = (len(text[i:].replace(" ", "")) for i in cut)
    runs = _glyphs(img, b)
    if tail == 0 or len(runs) < first:
        return None
    widths = sorted(r[1] - r[0] for r in runs)
    if max(r[1] - r[0] for r in runs[-first:]) > 1.5 * widths[len(widths) // 2]:
        return None
    return runs[-first][0], runs[-tail][0]


def _black(img: NDArray[np.uint8], b: Box, text: str, cut: tuple[int, int] | None) -> None:
    """The whole box, or (``cut``) the id's digits before its last visible ones."""
    span = _hidden_x(img, b, text, cut) if cut else None
    if span is None:
        img[b.y1 : b.y2, b.x1 : b.x2] = 0
        return
    img[b.y1 : b.y2, span[0] : span[1]] = 0


def mask_png(
    png: bytes, redact: Callable[[str], str], ocr_fn: OcrFn, ids: IdMask | None = None
) -> bytes:
    """Black out every OCR box whose text holds a run value or secret. With ``ids``, a box whose
    only hit is an account id keeps its last digits visible: the rest of the id is blacked out,
    up to its last digits' glyphs found from the box's right end (the whole box when they cannot
    be told apart). A clean image is written as is. ``ocr_fn`` is the caller's OCR
    (``lambda img: ocr(img, min_score)``)."""
    img = decode(png)
    hit = False
    for text, box in ocr_fn(img):
        shown = ids(text) if ids else text  # what an id-only box may still show
        whole = redact(text) not in (text, shown)  # a value or a secret: the whole box
        cuts: list[tuple[int, int] | None] = (
            [None] if whole else list(ids.spans(text) if ids else [])
        )
        for cut in cuts:
            _black(img, box, text, cut)
        hit = hit or bool(cuts)
    return encode(img) if hit else png
