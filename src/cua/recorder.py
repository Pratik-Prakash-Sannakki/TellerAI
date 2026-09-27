"""The recorder's COMPILE half: events + declared inputs -> Capability.

Ported from ``notebooks/03_recorder.py``'s ``OFFLINE`` cells (Part A, COMPILE) -- pure Python, no
Playwright import, no browser. This module never imports the CAPTURE half's browser-facing tool
wrappers (``extract_value``, ``open_path``, ``finish_business_outcome``, the ``.coroutine``
event-logging wrapper, the deep-agents/TypeSafe wiring): those remain agent-side code that the
``cua discover`` CLI command orchestrates directly against ``cua.agent``, per this port's own
scoping (a real, importable CAPTURE API was deliberately not built here -- see REPORT.md's Cuts
section and DECISIONS.md's Phase 9 packaging decision).

Every function below is an unmodified port of the notebook's own COMPILE logic -- see
DECISIONS.md sections M/P/Q/S/U (D41-D49, superseded; D70-D76 the v2 rebuild; D82-D84 the
human-entry fix; D86 the dead-end-risky-click fix; D90 the auto-declared-input fix) for the full
design history each rule below encodes.
"""

from __future__ import annotations

import json
import pathlib
import re

from pydantic import ValidationError

from cua.config import APP_ID, BASE, SESSION_EXPIRED_TEXT
from cua.schema import (
    Capability,
    Checkpoint,
    Click,
    Condition,
    Extract,
    InputParam,
    LabeledValueLocator,
    LabelLocator,
    Navigate,
    OutcomeRule,
    OutputParam,
    RoleLocator,
    Select,
    StructureLocator,
    Target,
    TextLocator,
    TypeText,
    Within,
    from_yaml,
    to_yaml,
)

__all__ = [
    "CompileError",
    "norm_url",
    "path_only",
    "contains_literal",
    "substitute",
    "same_value",
    "classify_status",
    "value_matches_type",
    "derive_target",
    "ACTION_TOOLS",
    "NAV_TOOLS",
    "STATE_TOOLS",
    "UNSTRUCTURED_HANDOFF_TOOLS",
    "HUMAN_ENTRY_WHY",
    "clean_events",
    "drop_detours",
    "drop_dead_end_risky_clicks",
    "trim_tail",
    "split_login",
    "synthesize_human_entries",
    "build_steps",
    "find_leftovers",
    "relogin_rule",
    "rule_from_probe",
    "compile_run",
    "save_capability",
    "show",
    "ARTIFACTS",
    "REPO",
]


def _find_repo() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents, *here.parents]:
        if (p / "artifacts").exists() and (p / "notebooks").exists():
            return p
    return pathlib.Path.cwd()


REPO = _find_repo()
ARTIFACTS = REPO / "artifacts"
SCRATCH = REPO / "notebooks" / "scratch"       # git-ignored. Raw events go here, never into artifacts/


# ---------- small helpers (urls, literals, status) ----------
class CompileError(Exception):
    """The recording cannot become a valid capability. `.problems` lists every reason."""

    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("; ".join(self.problems))


def norm_url(url: str, base: str = BASE) -> str:
    """Relative path + query. Drops the host, the base path, ;jsessionid=... and the fragment.
    Session ids never reach an event. CAPTURE calls this before an event is ever appended; COMPILE
    trusts that every before/after url is already normalized."""
    from urllib.parse import urlparse

    if not url or url == "about:blank":
        return url or ""
    u, b = urlparse(url), urlparse(base)
    path = re.sub(r";[^?#/]*", "", u.path)
    if u.hostname == b.hostname and path.startswith(b.path):
        path = path[len(b.path):] or "/"
    elif u.hostname != b.hostname:
        return f"{u.scheme}://{u.hostname}{path}"          # off-site: keep the host so compile refuses it
    return path + (f"?{u.query}" if u.query else "")


def path_only(url: str) -> str:
    return url.split("?")[0]


def _literal_re(lit: str):
    """The literal, but not inside a longer word or number: '5' is not found in '$50' or '1.5',
    'id' not in 'account_id'."""
    return re.compile(r"(?<![A-Za-z0-9_])(?<!\d[.,])" + re.escape(lit) + r"(?![A-Za-z0-9_])(?![.,]\d)")


def contains_literal(text: str, lit: str) -> bool:
    return bool(lit) and bool(_literal_re(lit).search(text or ""))


def substitute(text: str, inputs: dict[str, str]) -> str:
    """Replace declared literals with {{name}}. Longest literal first, so a longer value is never
    partially shadowed by a shorter one sharing a prefix."""
    for name, lit in sorted(inputs.items(), key=lambda kv: -len(kv[1])):
        if lit:
            text = _literal_re(lit).sub(lambda _m, n=name: "{{" + n + "}}", text)
    return text


def _canon(s: str) -> str:
    s = s.strip().lower().replace("$", "").replace(",", "")
    if re.fullmatch(r"-?[1-9]\d*(\.\d+)?|-?0(\.\d+)?", s):
        return f"{float(s):.2f}"                # $20.00 == 20 == 20.0. Ids with a leading zero stay text.
    return s


def same_value(a: str, b: str) -> bool:
    return _canon(a) == _canon(b)


def classify_status(message: str) -> str:
    """Bucket a tool result's own text by the EXACT prefixes agent.ipynb's tools return (read
    directly from STEP 3's code, not guessed). Shared by CAPTURE (to fill event["status"]) and by
    fixtures/tests (so a fixture's status matches what a real run would actually produce)."""
    t = (message or "").strip()
    if t.startswith("DENIED"):
        return "denied"
    if t.startswith("DECLINED"):
        return "declined"
    if t.startswith("BLOCKED"):
        return "blocked"
    if t.startswith("SKIP:"):
        return "skip"
    if t.startswith("NOT YET:"):
        return "not_yet"
    if t.startswith("STOP:"):
        return "stop"
    if (t.startswith("UNKNOWN SECRET") or t.startswith("REFUSED:") or "FAILED for" in t
            or t.startswith("CLICK FAILED") or t.startswith("TYPE FAILED") or t.startswith("SELECT FAILED")):
        return "failed"
    if t.startswith("A human"):
        return "handoff"
    return "ok"


VALUE_TYPES = {"string": r"\S.*", "integer": r"-?\d+", "number": r"-?[\d,]*\.?\d+",
               "currency": r"-?\$?-?[\d,]+(\.\d{2})?", "boolean": r"true|false|yes|no"}


def value_matches_type(value: str, value_type: str) -> bool:
    """Same shape as replay's own `matches_value_type` (cua.replay) -- used at CAPTURE time so
    `extract_value` catches a type mismatch while the browser is still open, not later."""
    return value_type in VALUE_TYPES and bool(re.fullmatch(VALUE_TYPES[value_type], value.strip(), re.I))


# ---------- locator derivation (D8, D42, D63, D68) ----------
ACCESSIBLE = {"aria", "label", "value", "text", "attr_acc"}   # name sources a role locator can really match


def _sub(s: str | None, inputs: dict[str, str]) -> str | None:
    return substitute(s, inputs) if s else s


def _within_from_container(container: dict | None, inputs: dict[str, str]):
    if not container:
        return None
    return Within(role=container["role"], name=_sub(container.get("name"), inputs))


def _refuse_if_duplicate_label(label: str, label_count: int, strategy: str) -> None:
    """D68: `label` and `labeled_value` locators have no `within` slot in the schema. A duplicated
    label cannot be scoped, so it must be refused, not silently saved ambiguous."""
    if label_count and label_count > 1:
        raise CompileError(
            f"label {label!r} is used by {label_count} elements on this page. The schema has no "
            f"`within` scope for a {strategy!r} locator (D68), so this cannot be saved "
            "unambiguously. Pick a different element, or one with a real accessible name."
        )


def derive_target(el: dict, inputs: dict[str, str], warnings: list[str]) -> Target:
    """Descriptor -> Target(primary, fallback). role+name (high, only when the name is a REAL
    accessible name) > label, text (medium) > structure inside a container (low). data-cua-ref is
    never used. A page-wide index is never produced (structure always needs a real `within`).

    Duplicate names (D68): a role/text locator whose name is not unique on the page is scoped with
    `within` when a container was captured; if no container was captured, it is saved unscoped and
    flagged in `warnings` rather than silently invented. A duplicated `label` cannot be scoped at
    all (no `within` slot on that strategy) and is refused outright.
    """
    name = _sub(el.get("name"), inputs)
    label = _sub(el.get("label"), inputs)
    text = _sub(el.get("text"), inputs)
    role = el.get("role")
    name_source = el.get("name_source")
    container = el.get("container")
    name_count = el.get("name_count") or 1
    label_count = el.get("label_count") or 1
    data_dependent = any("{{" in s for s in (name, label, text) if s)

    role_ok = bool(name) and name_source in ACCESSIBLE and role not in (None, "generic")
    scoped_note = " Scoped to its container: this name repeats elsewhere on the page."
    candidates: list = []

    if role_ok:
        within = None
        if name_count > 1:
            within = _within_from_container(container, inputs)
            if within is None:
                warnings.append(f"role={role!r} name={name!r} is not unique on the page and no "
                                 "container was captured to scope it; saved unscoped")
        candidates.append(RoleLocator(
            role=role, name=name, within=within, stability="high",
            note="Accessible role and name; the most stable signal we have." + (scoped_note if within else ""),
        ))

    if label:
        _refuse_if_duplicate_label(label, label_count, "label")
        candidates.append(LabelLocator(
            label=label, stability="medium",
            note="Label text next to the field; unlikely to change independently of the field itself.",
        ))

    if text and text != label and not (role_ok and text == name):
        within = None
        if name_count > 1:
            within = _within_from_container(container, inputs)
            if within is None:
                warnings.append(f"text={text!r} is not unique on the page and no container was "
                                 "captured to scope it; saved unscoped")
        candidates.append(TextLocator(
            text=text, within=within, stability="medium",
            note="Visible text; a reasonable backup if the accessible name ever changes." + (scoped_note if within else ""),
        ))

    if container and el.get("nth") and el.get("tag") and not data_dependent:
        candidates.append(StructureLocator(
            tag=el["tag"], within=_within_from_container(container, inputs), nth=el["nth"], stability="low",
            note="Position inside its container, counting all elements of that tag; last resort only.",
        ))

    if not candidates:
        raise CompileError(f"cannot identify element role={role!r} name={el.get('name')!r}: "
                            "no accessible name, label, text, or container")

    primary, fallback = candidates[0], (candidates[1] if len(candidates) > 1 else None)
    return Target(primary=primary, fallback=fallback)


def _refuse_if_header_value(label: str, value_header: bool) -> None:
    """D101: a `labeled_value` extract step whose CAPTURED resolution is itself a table/grid HEADER
    cell -- a structural DOM signal (`<th>`, `role=columnheader`, or a `<thead>` ancestor; see
    `notebooks/03_recorder.py` BROWSER 8's `READ_LABELED_JS`) -- can never be a genuine per-row/
    per-record value: a header cell names a column for every row, it is never one record's own
    data. This is the general shape of D89/D97/D100's recurring bug (there: label `Balance`/
    `Balance*`, whose 'next cell' was the `Available Amount` column header, not any account's own
    balance) -- refused here regardless of what specific words a given site's own headers happen to
    use; this function never looks at the label's or value's TEXT, only at the `value_header`
    structural flag captured with the event.

    `value_header` is missing (`False` by default) for any event captured before this flag existed,
    or from a capture path that does not yet compute it -- this degrades to a silent no-op in that
    case, same as before this fix, rather than ever guessing from absent data."""
    if value_header:
        raise CompileError(
            f"labeled_value target label={label!r}: the value this locator resolved to at capture "
            "time is itself a table/grid header cell, not real row data (D101, the general form of "
            "D89/D97/D100's recurring bug). Pick a label whose value is genuine data -- e.g. a "
            "footer/total row, or a non-tabular detail field -- not a column header."
        )


def _extract_target(label: str, label_count: int, value_header: bool = False) -> Target:
    _refuse_if_duplicate_label(label, label_count, "labeled_value")
    _refuse_if_header_value(label, value_header)
    return Target(primary=LabeledValueLocator(
        label=label, stability="medium",
        note="Label text is stable across releases; a labeled-value read does not depend on page position.",
    ))


# ---------- clean-up (D23, D43) ----------
ACTION_TOOLS = {"click", "type_text", "type_secret", "select_option", "extract_value", "open_path"}
NAV_TOOLS = {"click", "open_path"}
STATE_TOOLS = {"type_text", "type_secret", "select_option", "extract_value"}


def _key(e: dict):
    el = e.get("el") or {}
    c = el.get("container") or {}
    return (e["tool"], el.get("role"), el.get("name"), el.get("tag"), c.get("role"), el.get("nth"),
            e.get("value"), e.get("label"), (e.get("args") or {}).get("path"))


def clean_events(events: list[dict]):
    """Keep only actions that worked and mattered. Returns (kept, dropped). dropped = [(i, tool, reason)].
    Any status other than 'ok' covers DENIED/BLOCKED/SKIP/NOT YET/failed in one rule."""
    dropped, kept = [], []
    for e in events:
        if e["tool"] not in ACTION_TOOLS:
            dropped.append((e["i"], e["tool"], "not an action"))
        elif e.get("status") != "ok":
            dropped.append((e["i"], e["tool"], f"did not work ({e.get('status')})"))
        elif kept and _key(kept[-1]) == _key(e) and kept[-1]["before"]["url"] == e["before"]["url"]:
            dropped.append((e["i"], e["tool"], "repeat of the previous action"))
        else:
            kept.append(e)
    return kept, dropped


def drop_detours(kept: list[dict], dropped: list):
    """A click/open_path that changed the page, then a later one that returned to the page it
    left, with nothing typed, chosen, or extracted in between: both are a dead end. Remove them.

    D86: a `risky` (approved) click is eligible for this exact same check, same as any other click
    -- it is no longer blanket-excluded just because it is risky. This function's shape -- an
    unbroken run of NAV_TOOL events returning to the exact URL a NAV_TOOL event left -- still
    cannot see a same-page, same-URL failed submission with real typing in between; that different
    shape is `drop_dead_end_risky_clicks`'s job, right below."""
    out, i = [], 0
    while i < len(kept):
        e, end = kept[i], None
        if e["tool"] in NAV_TOOLS and e["after"]["url"] != e["before"]["url"]:
            for j in range(i + 1, len(kept)):
                k = kept[j]
                if k["tool"] not in NAV_TOOLS:
                    break
                if k["after"]["url"] == e["before"]["url"]:
                    end = j
                    break
        if end is None:
            out.append(e)
            i += 1
        else:
            for x in kept[i:end + 1]:
                dropped.append((x["i"], x["tool"], f"dead end: left {path_only(e['before']['url'])} and came back"))
            i = end + 1
    return out


def drop_dead_end_risky_clicks(kept: list[dict], dropped: list) -> list[dict]:
    """D86: remove a risky click proven, by real evidence, to be a dead end. Never silently
    guesses: ambiguous same-target risky clicks (more than one shows a real page-state change)
    raise CompileError naming both events rather than picking one."""
    by_target: dict[tuple, list[int]] = {}
    for idx, e in enumerate(kept):
        if e["tool"] == "click" and e.get("approved"):
            by_target.setdefault(_key(e), []).append(idx)

    to_drop: set[int] = set()
    for target, idxs in by_target.items():
        if len(idxs) < 2:
            continue
        changed = [idx for idx in idxs
                   if (kept[idx]["before"]["url"], kept[idx]["before"]["heading"])
                   != (kept[idx]["after"]["url"], kept[idx]["after"]["heading"])]
        no_op = [idx for idx in idxs if idx not in changed]
        if len(changed) > 1:
            names = " and ".join(f"event {kept[i]['i']} ({kept[i]['tool']})" for i in changed)
            raise CompileError(
                f"a risky click on {target[1]} {target[2]!r} shows a real page-state change more "
                f"than once in this run ({names}). Cannot tell which one is the genuine point of "
                "no return without guessing -- refusing to compile. Review the run by hand."
            )
        for idx in no_op:
            if idx != idxs[-1]:
                to_drop.add(idx)

    for idx in sorted(to_drop):
        e = kept[idx]
        dropped.append((e["i"], e["tool"],
                         "dead end: risky click had no effect and the same target was clicked again later"))
    return [e for n, e in enumerate(kept) if n not in to_drop]


def _meaningful(e: dict) -> bool:
    return e["tool"] in STATE_TOOLS or bool(e.get("approved")) or bool((e.get("el") or {}).get("submit"))


def trim_tail(task: list[dict], dropped: list):
    """Link clicks after the last meaningful action changed nothing the capability needs."""
    last = max((n for n, e in enumerate(task) if _meaningful(e)), default=None)
    if last is None:
        return task
    for e in task[last + 1:]:
        dropped.append((e["i"], e["tool"], "after the last meaningful step"))
    return task[:last + 1]


def split_login(kept: list[dict]):
    """D32/D45: everything up to and including the first click after the last type_secret is login."""
    secret_idx = [n for n, e in enumerate(kept) if e["tool"] == "type_secret"]
    if not secret_idx:
        return [], kept
    for n in range(secret_idx[-1] + 1, len(kept)):
        if kept[n]["tool"] == "click":
            return kept[:n + 1], kept[n + 1:]
    raise CompileError("secrets were typed but no click followed. The login click is missing.")


# D82: only a GENUINELY unstructured handoff -- one where we have no idea, in advance, which
# element(s) a human touched -- is refused here. `ask_human` is free-form; a take-over click (the
# `choice == "t"` path inside `click()`, D56-D62) is the same. `request_value`/
# `request_missing_values` are NOT unstructured: both open a KNOWN, specific ref (or list of refs)
# before handing off, so CAPTURE's own wrapper for those two tools reads `current_value(ref)`
# right after hand-back and turns whatever is now non-empty into a proper `type_text`/
# `select_option` event via `synthesize_human_entries` below.
UNSTRUCTURED_HANDOFF_TOOLS = {"ask_human", "click"}


def _refuse_bad_run(events: list[dict]) -> None:
    """Top-level refusals, BEFORE any cleanup runs. A run that hit the login attempt guard, used a
    genuinely unstructured human handoff (ask_human, or a take-over click, D82), gave up, or was
    declined must never become a capability at all."""
    if any(e.get("status") == "stop" for e in events):
        raise CompileError(
            "this run hit the login attempt guard (D69: 'STOP: login failed...'). "
            "Refusing to compile any capability from it."
        )
    if any(e.get("status") == "handoff" and e.get("tool") in UNSTRUCTURED_HANDOFF_TOOLS for e in events):
        raise CompileError(
            "a human took over with no specific field known (ask_human, or taking over a risky "
            "click) during this run. There is no way to know what they did, so that step cannot "
            "be recorded. Put every value in the goal as a declared input, approve (rather than "
            "take over) any risky click, and run again."
        )
    fin = next((e for e in events if e["tool"] == "finish"), None)
    if fin and (fin.get("summary") or "").startswith(("STUCK:", "DECLINED:")):
        raise CompileError(f"this run did not complete: {fin['summary']!r}. Refusing to compile a capability from it.")
    terminal = [e for e in events if e["tool"] in {"finish", "finish_business_outcome"} and e.get("status", "ok") == "ok"]
    if terminal and terminal[-1]["tool"] == "finish_business_outcome":
        raise CompileError("this run ended with a business outcome. It is a probe: use rule_from_probe(), not compile_run().")


# ---------- synthesize_human_entries: a human-entered value becomes a proper event (D82, D83) ----------
HUMAN_ENTRY_WHY = "Value entered by a human during discovery; the agent did not have this value."
SELECT_ROLES = {"combobox", "select"}   # DESCRIBE_JS's own role vocabulary (D42) for a dropdown


def synthesize_human_entries(i_start: int, before_url: str, before_heading: str, after_url: str,
                              after_heading: str, entries: list[dict]) -> list[dict]:
    """Turn what a human filled in during a request_value/request_missing_values handoff into
    proper events, the SAME shape the CAPTURE wrapper produces for a real tool call.

    `entries`: `[{"ref": int, "el": <descriptor dict, same shape DESCRIBE_JS returns>,
    "value_after": str}, ...]` -- one entry per ref that was OPENED for the human (i.e. every ref
    `allow_refs` named). `value_after` is whatever `current_value(ref)` reads right after
    hand-back.

    An entry whose `value_after` is still empty means the human declined to fill that field: it is
    SKIPPED, not synthesized. Every synthesized entry becomes exactly one event, numbered
    sequentially from `i_start` (skipped entries do not consume a number), with `tool` chosen by
    the element's own `role`: a `combobox`/`select` becomes a `select_option`-shaped event;
    anything else becomes a `type_text`-shaped event. `status` is always `"ok"` and
    `human_entered: True` plus a `why` note (D84) mark it as human-sourced so `build_steps` can
    carry that note onto the compiled step.

    Pure: no browser, no network, no page access -- everything it needs is already in `entries`."""
    out: list[dict] = []
    i = i_start
    for entry in entries:
        value = (entry.get("value_after") or "").strip()
        if not value:
            continue   # the human declined to fill this one; nothing to synthesize
        el = entry.get("el") or {}
        is_select = (el.get("role") or "").lower() in SELECT_ROLES
        tool = "select_option" if is_select else "type_text"
        args = {"ref": entry["ref"], **({"option": value} if is_select else {"text": value})}
        out.append({
            "i": i, "tool": tool, "args": args,
            "message": f"Synthesized from a human handoff: {'chose' if is_select else 'typed'} into [{entry['ref']}].",
            "status": "ok",
            "before": {"url": before_url, "heading": before_heading},
            "after": {"url": after_url, "heading": after_heading},
            "approved": False, "el": el, "value": value,
            "human_entered": True, "why": HUMAN_ENTRY_WHY,
        })
        i += 1
    return out


# ---------- parameterisation and per-step assembly (D8, D9, D10, D29, D33, D38, D90) ----------
SENSITIVE_WORDS = ("ssn", "password", "social")
HUMAN_INPUT_PATTERN = r"^.{1,80}$"   # D90: generic and permissive on purpose -- see D90's reasoning


def _slugify_label(label: str | None) -> str:
    """'Address:' -> 'address', 'Zip Code:' -> 'zip_code', 'Phone #:' -> 'phone'. Lowercase, runs
    of non-alphanumeric characters collapsed to one underscore, leading/trailing underscores
    stripped. A label with no letters at all yields '' (D90 refuses on that)."""
    return re.sub(r"[^a-z0-9]+", "_", (label or "").lower()).strip("_")


def _declare_human_input(label: str | None, value: str, specs: dict, used_names: set, where: str) -> str:
    """D90: a human-entered value that matches no already-declared input gets its OWN new declared
    input, named from the field's own label -- never from its value. Collisions -- two labels
    producing the same slug, or a slug matching an already-declared input name -- are
    disambiguated with a deterministic `_2`, `_3`, ... suffix. A field with no usable label at all
    (D67's known gap) refuses compilation naming the event."""
    slug = _slugify_label(label)
    if not slug:
        raise CompileError(
            f"{where}: a human-entered value has no usable label to name a declared input after "
            "(D67's known gap). Refusing to guess a name -- declare this value as an input up "
            "front instead, or capture it from a labeled field."
        )
    name, n = slug, 2
    while name in used_names:
        name = f"{slug}_{n}"
        n += 1
    used_names.add(name)
    clean_label = (label or slug).strip().rstrip(":").strip()
    specs[name] = {
        "value": value, "type": "string",
        "description": f"{clean_label}, entered by a human during discovery -- provide the real value for each run.",
        "pattern": HUMAN_INPUT_PATTERN,
    }
    return name


def _params(text: str, inputs: dict[str, str], constants: list[dict], where: str, *,
            human_entered: bool = False, label: str | None = None,
            specs: dict | None = None, used_names: set | None = None) -> str:
    """A typed or chosen value. Whole-value match -> {{name}}. Otherwise substitute inside.

    No match at all: an AGENT's own value is kept and reported as a constant, unchanged from
    before (D29/D44). A HUMAN-entered value (D82/D83) is different -- the agent never had this
    value, so it must always become a declared input the caller supplies for real on every future
    run, never a frozen literal (D90).

    `inputs` here only ever holds the inputs already declared BEFORE this run started (a snapshot
    `build_steps` takes once, at the top, from the caller's own `specs`) -- an input this function
    itself auto-declares is deliberately never added back into `inputs`, only into `specs`."""
    for name, lit in inputs.items():
        if same_value(text, lit):
            return "{{" + name + "}}"
    out = substitute(text, inputs)
    if out != text:
        return out
    if human_entered:
        name = _declare_human_input(label, text, specs, used_names, where)
        return "{{" + name + "}}"
    constants.append({"where": where, "value": text})
    return text


def _amount_input(specs: dict) -> str | None:
    money = [n for n, s in specs.items() if s.get("type") in ("currency", "number")]
    if len(money) == 1:
        return money[0]
    named = [n for n in money if "amount" in n]
    return named[0] if named else None


def build_steps(events: list[dict], specs: dict, warnings: list[str], constants: list):
    """Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page, and where
    the URL changed without a click.

    D90: `specs` is mutated in place whenever a human-entered value matches no already-declared
    input -- a new one is appended, named from the field's own label. `_cap` reads `specs` again
    after this returns, so the new input flows into the compiled `Capability.inputs` and into the
    leftover-literal check exactly like an originally-declared one. `inputs` (the name->value
    snapshot used for matching) is deliberately NOT updated as new inputs are declared."""
    inputs = {n: s["value"] for n, s in specs.items()}
    used_names = set(specs.keys())
    steps, outputs, secrets, paths = [], [], [], []
    prev_after = None
    for e in events:
        tool, where = e["tool"], f"event {e['i']} ({e['tool']})"
        before_url, after_url = e["before"]["url"], e["after"]["url"]
        paths += [before_url, after_url]
        if tool == "open_path":
            steps.append(Navigate(path=substitute(e["args"]["path"], inputs), why="Opened directly by the agent."))
        elif prev_after is None or before_url != prev_after:
            steps.append(Navigate(
                path=substitute(before_url, inputs),
                why="Start page of this capability." if prev_after is None else "The page changed without a click.",
            ))
        prev_after = after_url
        el = e.get("el") or {}
        if tool == "click":
            risky = bool(e.get("approved"))
            steps.append(Click(
                target=derive_target(el, inputs, warnings), risk="risky" if risky else "safe",
                amount_input=_amount_input(specs) if risky else None,
                why="Point of no return. A human approved it in discovery. Replay decides by policy." if risky else None,
            ))
        elif tool in ("type_text", "type_secret"):
            field = f"{el.get('name') or ''} {el.get('label') or ''}".lower()
            if tool == "type_text" and any(w in field for w in SENSITIVE_WORDS):
                raise CompileError(f"{where}: typed into a sensitive field ({el.get('label') or el.get('name')}). Refusing to record it.")
            if tool == "type_secret":
                name = e["value"]
                if name not in secrets:
                    secrets.append(name)
                value = "{{secret:" + name + "}}"
            else:
                value = _params(e["value"], inputs, constants, f"{where} into {el.get('label') or el.get('name')!r}",
                                 human_entered=e.get("human_entered", False), label=el.get("label"),
                                 specs=specs, used_names=used_names)
            steps.append(TypeText(target=derive_target(el, inputs, warnings), value=value,
                                   why=HUMAN_ENTRY_WHY if e.get("human_entered") else None))
        elif tool == "select_option":
            if el.get("options") and e["value"] not in el["options"]:
                raise CompileError(f"{where}: option {e['value']!r} is not in the dropdown's options")
            steps.append(Select(
                target=derive_target(el, inputs, warnings),
                option=_params(e["value"], inputs, constants, f"{where} in {el.get('label') or el.get('name')!r}",
                                human_entered=e.get("human_entered", False), label=el.get("label"),
                                specs=specs, used_names=used_names),
                why=HUMAN_ENTRY_WHY if e.get("human_entered") else None,
            ))
        elif tool == "extract_value":
            label = substitute(e["label"], inputs)
            desc = substitute(
                e.get("description") or f"The value shown next to '{e['label']}'.",
                inputs,
            )
            steps.append(Extract(
                target=_extract_target(label, e.get("label_count", 1), e.get("value_header", False)),
                save_as=e["save_as"],
            ))
            outputs.append(OutputParam(
                name=e["save_as"], type=e.get("value_type", "string"),
                description=desc,
            ))
    return steps, outputs, secrets, paths


def find_leftovers(cap: Capability, inputs: dict) -> list[str]:
    """D29/D44: no declared literal may survive anywhere in the capability, except in the
    `inputs` docs. The message names the input and the place, never the value."""
    data = cap.model_dump(mode="json", exclude_none=True)
    data.pop("inputs", None)
    found: list[str] = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(o, list):
            for n, v in enumerate(o):
                walk(v, f"{path}[{n}]")
        elif isinstance(o, str):
            found.extend(f"input {name!r} still appears as a literal in {path}" for name, lit in inputs.items() if contains_literal(o, lit))

    walk(data, "")
    return found


def _checkpoint_from_last(events: list[dict]) -> Checkpoint:
    last = events[-1]
    heading = (last["after"].get("heading") or "").strip()
    if not heading:
        raise CompileError("the final kept step's page has no heading, so the checkpoint has no text signal (D9 needs both)")
    url = last["after"]["url"]
    return Checkpoint(url_contains=path_only(url).rsplit("/", 1)[-1] or "/", text_present=heading)


def _cap(name: str, description: str, events: list[dict], specs: dict, rules: list,
         constants: list, warnings: list[str], base_url: str) -> Capability:
    steps, outputs, secrets, paths = build_steps(events, specs, warnings, constants)
    inputs_literals = {n: s["value"] for n, s in specs.items()}
    text = json.dumps([s.model_dump(mode="json") for s in steps])
    used = {n for n in specs if "{{" + n + "}}" in text}
    used |= {s.amount_input for s in steps if getattr(s, "amount_input", None)}   # a risky click's amount_input counts as using that input, even with no separate typed step
    cap = Capability(
        name=name, version=1, status="draft", description=description, base_url=base_url,
        risk_level="risky" if any(s.action == "click" and s.risk == "risky" for s in steps) else "safe",
        inputs=[InputParam(name=n, type=s.get("type", "string"), description=s.get("description", n),
                           pattern=s.get("pattern")) for n, s in specs.items() if n in used],
        outputs=outputs, secrets=secrets, steps=steps,
        checkpoint=_checkpoint_from_last(events), outcome_rules=list(rules),
    )
    bad = find_leftovers(cap, inputs_literals)
    if bad:
        raise CompileError(bad)
    return cap


def relogin_rule() -> OutcomeRule:
    return OutcomeRule(when=Condition(text_present=SESSION_EXPIRED_TEXT), kind="recoverable", action="relogin",
                       message="The session expired. Run the login capability again and continue.")


def rule_from_probe(events: list[dict], probe_inputs: dict[str, str]) -> OutcomeRule:
    """D10/D47: a bad-input run ended with finish_business_outcome(outcome, proof_text). Turn it
    into a business rule. The bad value is cut out of the proof text so the rule matches any input."""
    fin = next((e for e in reversed(events) if e["tool"] == "finish_business_outcome" and e.get("status") == "ok"), None)
    if not fin:
        raise CompileError("this run has no successful finish_business_outcome(outcome, proof_text). It is not a probe.")
    pieces = [fin["proof"]]
    for lit in probe_inputs.values():
        pieces = [x for p in pieces for x in _literal_re(lit).split(p)]
    text = max((p.strip(" :#.-,") for p in pieces), key=len, default="")
    if len(text) < 6:
        raise CompileError("the proof text is too short once the probe's input value is removed. Ask for a longer message from the page.")
    return OutcomeRule(when=Condition(text_present=text), kind="business", outcome=fin["outcome"],
                       message=f"Seen in a bad-input probe. The application answered: {text}")


def _check_specs(specs: dict) -> None:
    problems = []
    for n, s in specs.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", n):
            problems.append(f"input name {n!r} must be lower snake_case")
        if not s.get("value"):
            problems.append(f"input {n!r} has no declared value")
        elif s.get("pattern") and not re.search(s["pattern"], s["value"]):
            problems.append(f"input {n!r}: its declared value does not match its own pattern")
    if problems:
        raise CompileError(problems)


def compile_run(events: list[dict], spec: dict, *, extra_rules=(), base_url: str = BASE) -> dict:
    """The whole pipeline. Returns {"login": Capability|None, "task": Capability, "report": {...}}.
    spec = {name, description, inputs: {name: {value, type, description, pattern?}}}"""
    _refuse_bad_run(events)
    # D90: a shallow copy, not the caller's own dict -- `build_steps` may append newly
    # auto-declared inputs into `specs`, and this must never leak back into the caller's `spec`
    # object (a caller may reuse the same `spec` dict across more than one `compile_run` call).
    specs = dict(spec["inputs"])
    _check_specs(specs)

    kept, dropped = clean_events(events)
    kept = drop_detours(kept, dropped)
    kept = drop_dead_end_risky_clicks(kept, dropped)   # D86
    login_ev, task_ev = split_login(kept)
    task_ev = trim_tail(task_ev, dropped)
    if not task_ev:
        raise CompileError("nothing left to record after the login. The run did nothing that matters.")

    constants: list = []
    warnings: list[str] = []
    try:
        login = None
        if login_ev:
            login = _cap(f"login_{APP_ID}", f"Log in to {APP_ID} with the stored credentials.",
                         login_ev, {}, [], constants, warnings, base_url)
            leak = find_leftovers(login, {n: s["value"] for n, s in specs.items()})
            if leak:
                raise CompileError(leak)
        rules = [*extra_rules] + ([relogin_rule()] if login else [])
        task = _cap(spec["name"], spec["description"], task_ev, specs, rules, constants, warnings, base_url)
    except ValidationError as err:
        raise CompileError([f"schema: {'; '.join(x['msg'] for x in err.errors())}"]) from err
    except ValueError as err:
        raise CompileError(f"schema: {err}") from err

    unused = [f"declared input {n!r} is never used in the steps" for n in specs if n not in {i.name for i in task.inputs}]
    report = {"dropped": dropped, "constants": constants, "warnings": warnings + unused}
    return {"login": login, "task": task, "report": report}


# ---------- save (only after validation) and show ----------
def save_capability(cap: Capability, out_dir: pathlib.Path = ARTIFACTS, *, forbidden=()) -> pathlib.Path:
    """Validate, guard against secret values, write. Never overwrites a verified capability."""
    cap = Capability.model_validate(cap.model_dump(mode="json"))
    text = to_yaml(cap)
    for v in forbidden:
        if v and _literal_re(v).search(text):
            raise CompileError("a stored secret value would be written into the file. Nothing was saved.")   # value never printed
    path = pathlib.Path(out_dir) / f"{cap.name}.yaml"
    if path.exists() and from_yaml(path.read_text()).status == "verified":
        raise CompileError(f"{path.name} is already verified. Refusing to overwrite it with a draft.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# DRAFT written by the recorder (src/cua port). A reviewer must read it before it is verified.\n" + text)
    return path


def show(result: dict) -> None:
    for key in ("login", "task"):
        if result[key]:
            print(f"----- {key}: {result[key].name} -----")
            print(to_yaml(result[key]))
    rep = result["report"]
    print("----- report -----")
    print("dropped:")
    for i, tool, why in rep["dropped"]:
        print(f"  event {i} {tool}: {why}")
    print("constants (typed values that match no declared input, kept as literals):", rep["constants"] or "none")
    print("warnings:", rep["warnings"] or "none")
