"""Loading a saved capability (schema v2) and the inputs it needs.

Moved unchanged from notebooks/replay/replay.py (``PLACEHOLDER`` 767, ``load_capability``
770-789, ``load_outcomes`` 792-797, ``seen_outcome`` 800-806, ``given_inputs`` 809-815,
``fill`` 818-820, ``secret_name`` 823-825, ``step_inputs`` 828-831). The notebook's globals
(``CFG``, ``SECRETS``) become explicit parameters: ``site: SiteProfile`` and ``cfg:
BrowserConfig``. ``ask_inputs`` (834-847) and ``ask_option`` (850-857) take ``ctx`` first: the
``CONTROL`` global is ``ctx.control``, ``CFG.sensitive_words`` is ``ctx.bcfg.sensitive_words``.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from cua.config import OUTCOME_STATUSES, BrowserConfig, SiteProfile, resolve_secret
from cua.safety.hosts import host_allowed
from cua.safety.redact import is_sensitive
from cua.schema import Capability, Stop

if TYPE_CHECKING:
    from cua.replay.context import Ctx

PLACEHOLDER = re.compile(r"\{\{\s*(secret:)?(\w+)\s*\}\}")


def _secret_is_set(name: str, site: SiteProfile) -> bool:
    """True if `name` is a known secret with a non-empty value in `.env` (D32: never read here
    directly -- `resolve_secret` is the only thing that touches the env var's value)."""
    try:
        resolve_secret(name, site)
    except (KeyError, RuntimeError):
        return False
    return True


def _missing_crops(cap: Capability, folder: Path) -> list[str]:
    crops = [
        s.target.template  # type: ignore[union-attr]
        for s in cap.steps
        if getattr(s, "target", None) and s.target.template  # type: ignore[union-attr]
    ]
    return [c for c in crops if not (folder / c).is_file()]


def load_capability(
    path: str | Path, site: SiteProfile, cfg: BrowserConfig
) -> tuple[Capability, Path]:
    """The capability and the folder its crop paths are relative to."""
    path = Path(path)
    text = path.read_text()
    data = yaml.safe_load(text)
    data.pop("outcomes", None)  # replay's own optional key; the schema stays discovery's
    cap = Capability.model_validate(data)
    if tuple(cap.viewport) != cfg.viewport or cap.device_scale_factor != 1:
        raise Stop(
            "FAILED",
            f"recorded at {cap.viewport} x{cap.device_scale_factor}, "
            f"replay runs at {cfg.viewport} x1 (Q10)",
        )
    if not host_allowed(cap.base_url, site):
        raise Stop("FAILED", "base_url host is not allowed")
    refs = PLACEHOLDER.findall(text)
    if unknown := {n for s, n in refs if not s} - {p.name for p in cap.inputs}:
        raise Stop("FAILED", f"undeclared inputs {sorted(unknown)}")
    if unset := sorted({n for s, n in refs if s and not _secret_is_set(n, site)}):
        raise Stop("FAILED", f"secrets not set in .env: {unset}")
    if lost := _missing_crops(cap, path.parent):
        raise Stop("FAILED", f"missing crops {lost}")
    return cap, path.parent


def load_outcomes(path: str | Path, site: SiteProfile) -> list[dict[str, str]]:
    """The capability's own `outcomes:` [{text, status, meaning}], else the site's defaults."""
    data = yaml.safe_load(Path(path).read_text())
    rules = data.get("outcomes") or [dataclasses.asdict(o) for o in site.outcomes]
    if bad := [r for r in rules if r.get("status") not in OUTCOME_STATUSES]:
        raise Stop("FAILED", f"outcomes with an unknown status: {bad}")
    return rules


def seen_outcome(before: str, after: str, rules: list[dict[str, str]]) -> dict[str, str] | None:
    """The first rule whose text (whole words, any case) appeared on screen with this step."""
    for rule in rules:
        hit = re.compile(rf"(?<!\w){re.escape(rule['text'])}(?!\w)", re.I)
        if hit.search(after) and not hit.search(before):
            return rule
    return None


def given_inputs(cap: Capability, inputs: dict[str, str]) -> dict[str, str]:
    """The caller's values, by the capability's own input names (any case). Any other key stops."""
    names = {p.name.casefold(): p.name for p in cap.inputs}
    if bad := [k for k in inputs if k.casefold() not in names]:
        accepts = ", ".join(p.name for p in cap.inputs) or "none"
        raise Stop("STUCK", f"not a permissible input: {', '.join(bad)}. Accepts: {accepts}.")
    return {names[k.casefold()]: v for k, v in inputs.items() if v}


def fill(text: str, values: dict[str, str]) -> str:
    """Put inputs into `{{name}}`. `{{secret:x}}` stays as it is: secrets go in only when typed."""
    return PLACEHOLDER.sub(lambda m: m[0] if m[1] else values[m[2]], text)


def secret_name(value: str) -> str | None:
    m = PLACEHOLDER.fullmatch(value.strip())
    return m[2] if m and m[1] else None


def step_inputs(cap: Capability) -> list[str]:
    """Every `{{input}}` the steps use, in step order, once each."""
    found = (
        n for st in cap.steps for sec, n in PLACEHOLDER.findall(st.model_dump_json()) if not sec
    )
    return list(dict.fromkeys([*found, *(p.name for p in cap.inputs)]))


def _ask_rows(ctx: Ctx, cap: Capability, names: list[str]) -> list[tuple[str, bool]]:
    about = {p.name: p.description for p in cap.inputs}
    picks = {
        m[2]
        for st in cap.steps
        if st.action == "select" and (m := PLACEHOLDER.fullmatch(st.option))
    }
    note = " (must match an option on the page)"
    words = ctx.bcfg.sensitive_words
    return [
        (f"{n}: {about.get(n, '')}" + (note if n in picks else ""), is_sensitive(n, words))
        for n in names
    ]


async def ask_inputs(
    ctx: Ctx, cap: Capability, given: dict[str, str] | None = None
) -> dict[str, str]:
    """R8: ONE form before step 1 for every input the caller did not give. Nothing is
    pre-filled."""
    given = dict(given or {})
    names = [n for n in step_inputs(cap) if n not in given]
    if not names:
        return given
    got = await ctx.control.form("Replay needs these inputs:", _ask_rows(ctx, cap, names))
    got = got or [""] * len(names)
    if blank := [n for n, v in zip(names, got, strict=False) if not v]:
        raise Stop("STUCK", f"inputs not given: {blank}")
    return given | dict(zip(names, got, strict=False))


async def ask_option(ctx: Ctx, cap: Capability, name: str, options: list[str]) -> str:
    """The one mid-run prompt: the given value is not a live option. Choose one, blank first."""
    about = next((p.description for p in cap.inputs if p.name == name), "")
    got = await ctx.control.form(
        "That value is not an option here:", [(f"{name}: {about}", False)], [""], [["", *options]]
    )
    if not got or got[0] not in options:
        raise Stop("STUCK", f"no option chosen for {name}")
    return got[0]
