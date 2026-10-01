"""Values a send carries that the human never gave, and the dropdown choices to correct them.

From discovery.py 700-721 / replay.py 368-385. The only side difference is the given text:
discovery's is ``" ".join([goal, *given])``, replay's ``" ".join(given)`` -- the caller
(``SendState.given_text()``) supplies it. ``dropdown_options`` is one sync function (discovery's
was async over the same stash, with the same result).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence

from cua.safety.redact import is_sensitive

Dropdown = Mapping[str, object]


def _norm_num(n: str) -> str:
    return n.rstrip("0").rstrip(".") if "." in n else n  # 10.00 == 10


def mismatches(sent: dict[str, str], given_text: str, sensitive_words: Iterable[str]) -> list[str]:
    """Numbers being sent that the human never gave, e.g. account 1450 vs 1400.
    Only digit groups are compared: they are what a wrong transfer is made of, on any site."""
    given = set(re.findall(r"\d+(?:\.\d+)?", given_text))
    wanted = {_norm_num(n) for n in given}
    words = frozenset(sensitive_words)
    return [
        k
        for k, v in sent.items()
        if not is_sensitive(k, words)
        and any(_norm_num(n) not in wanted for n in re.findall(r"\d+(?:\.\d+)?", v))
    ]


def dropdown_options(
    fields: dict[str, str],
    keys: list[str],
    dropdowns: Sequence[Dropdown],
    hide: Callable[[str], str],
) -> list[list[str]]:
    """For each key: the options of the page dropdown whose CURRENT value is exactly this value,
    else [] (a plain box). Each dropdown is used once, so '1' in five fields never grabs one twice.
    From the pre-action read: the guard never touches the page while it holds a request."""
    free = [dict(d) for d in dropdowns]
    out: list[list[str]] = []
    for k in keys:
        hit = next((d for d in free if fields[k] and fields[k] in (d["value"], d["text"])), None)
        if hit:
            free.remove(hit)
        opts: list[str] = list(hit["options"]) if hit else []  # type: ignore[call-overload]
        out.append([hide(o) for o in opts] if hit and len(opts) > 1 else [])
    return out
