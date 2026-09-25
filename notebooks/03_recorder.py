# %% [markdown]
# # Phase 3 v2: the recorder, rebuilt
# A real agent run becomes a **draft capability** (YAML), against the CURRENT schema
# (`02_artifact_schema.py`, D63-D68) and the CURRENT `agent.ipynb` (D50-D69).
# - **Part A, COMPILE** (pure Python, cells titled `OFFLINE`): `events + declared inputs ->
#   Capability`. Tested entirely with hand-made fixture events. No browser, ever.
# - **Part B, CAPTURE** (cells titled `BROWSER`): copies agent.ipynb's current setup/scanner/
#   tools/safety cells verbatim, then wraps each tool to log an event, and adds two small new
#   tools the compiler needs (`extract_value`, `finish_business_outcome`) plus `open_path`.
#
# The old `03_recorder.py` this file replaces targeted a schema that no longer exists
# (`Target(locators=[...])`, `Capability(app=..., when_to_use=..., routes=...)`) and copied
# browser tools from before every Phase 1 safety fix. See
# `docs/superpowers/plans/2026-09-25-phase3-recorder-v2.md` and `DECISIONS.md` D41-D49
# (superseded) and D70+ (this rebuild).
#
# ## How to test the COMPILE half (this agent runs this; no browser)
# Run every `OFFLINE` cell top to bottom. Last line: `ALL OFFLINE CHECKS PASSED`.
#
# ## How the user tests the CAPTURE half (see the markdown cell right before `BROWSER 1`)

# %% OFFLINE 1: config and Phase 2 models
# Pure Python. No browser, no network, no API key.
# The Phase 2 models are NOT copied. We run the model cells of 02_artifact_schema.py in this
# namespace -- the same technique 04_replay_engine.py already uses.
import json
import pathlib
import re
import tempfile
from urllib.parse import urlparse

# ParaBank values live in config only (CLAUDE.md). Nothing below this cell knows about ParaBank
# beyond these four lines.
BASE = "https://parabank.parasoft.com/parabank"
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}   # names only
APP_ID = "parabank"
SESSION_EXPIRED_TEXT = "Customer Login"       # login page text, used for the relogin rule


def _find_repo() -> pathlib.Path:
    here = pathlib.Path(globals().get("__file__", ".")).resolve()
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents, here.parent, *here.parents]:
        if (p / "notebooks" / "02_artifact_schema.py").exists():
            return p
    raise FileNotFoundError("cannot find notebooks/02_artifact_schema.py. Start the kernel in the repo.")


REPO = _find_repo()
ARTIFACTS = REPO / "artifacts"
SCRATCH = REPO / "notebooks" / "scratch"       # git-ignored. Raw events go here, never into artifacts/


def load_schema(wanted=("Section 1:", "Section 2:", "Section 2a:", "Section 3:")) -> None:
    """Run the non-check model cells of the CURRENT Phase 2 notebook in this namespace. Cells
    whose header does not start with exactly one of `wanted` (every `*b`-suffixed checks cell) are
    skipped. `Capability`, `Target`, `RoleLocator`, ..., `to_yaml`/`from_yaml` all come from there,
    unmodified -- this file never redefines them."""
    text = (REPO / "notebooks" / "02_artifact_schema.py").read_text()
    for cell in re.split(r"(?m)^# %%", text)[1:]:
        header, _, body = cell.partition("\n")
        if header.strip().startswith(wanted):
            exec(compile(body, f"02_artifact_schema.py [{header.strip()}]", "exec"), globals())


load_schema()
print("schema loaded:", Capability.__name__, "| repo:", REPO.name)

# %% [markdown]
# ## Part A. COMPILE (pure Python)
# Events in, capability out. An **event** is one tool call the agent made, with a description of
# the element it touched. See `docs/superpowers/plans/2026-09-25-phase3-recorder-v2.md` for the
# full event shape and its field-by-field justification. In short:
# ```
# {i, tool, args, message, status, before:{url,heading}, after:{url,heading}, approved,
#  el:{role,name,name_source,label,text,tag,type,submit,options,container,nth,name_count,
#      label_count} | None,
#  value, label, save_as, value_type, description, outcome, proof, summary, values}
# ```

# %% OFFLINE 2: small helpers (urls, literals, status)
class CompileError(Exception):
    """The recording cannot become a valid capability. `.problems` lists every reason."""

    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("; ".join(self.problems))


def norm_url(url: str, base: str = BASE) -> str:
    """Relative path + query. Drops the host, the base path, ;jsessionid=... and the fragment.
    Session ids never reach an event. CAPTURE calls this before an event is ever appended; COMPILE
    trusts that every before/after url is already normalized."""
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
    the fixtures below (so a fixture's status matches what a real run would actually produce)."""
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
    """Same shape as replay's own `matches_value_type` (04_replay_engine.py) -- used at CAPTURE
    time so `extract_value` catches a type mismatch while the browser is still open, not later."""
    return value_type in VALUE_TYPES and bool(re.fullmatch(VALUE_TYPES[value_type], value.strip(), re.I))


# %% OFFLINE 2b: checks for the small helpers
assert norm_url("https://parabank.parasoft.com/parabank/overview.htm") == "/overview.htm"
assert norm_url("https://parabank.parasoft.com/parabank/activity.htm;jsessionid=ABC?id=13344") == "/activity.htm?id=13344"
assert norm_url("https://evil.example/phish") == "https://evil.example/phish"
assert contains_literal("id=13344", "13344") and not contains_literal("$50", "5")
assert not contains_literal("account_id", "id")
assert substitute("/activity.htm?id=13344", {"account_id": "13344"}) == "/activity.htm?id={{account_id}}"
assert same_value("$20.00", "20") and same_value("20.00", "20.0") and not same_value("013", "13")
assert classify_status("DENIED: 'register' is not allowed.") == "denied"
assert classify_status("DECLINED earlier by a human. Do not retry.") == "declined"
assert classify_status("BLOCKED: login already failed or hit its attempt limit.") == "blocked"
assert classify_status("STOP: login failed (the login page reported: 'could not be verified').") == "stop"
assert classify_status("SKIP: 'City' already has a value ('2').") == "skip"
assert classify_status("NOT YET: you are still on the start page.") == "not_yet"
assert classify_status("CLICK FAILED for [3]: TimeoutError") == "failed"
assert classify_status("A human entered the value for 'Amount' themselves. ...") == "handoff"
assert classify_status("A human took over and handed back. ...") == "handoff"
assert classify_status("Clicked [3].") == "ok"
assert classify_status("Typed into [1].") == "ok"
assert value_matches_type("$1,200.00", "currency") and not value_matches_type("free", "currency")
assert value_matches_type("42", "integer") and not value_matches_type("x", "integer")
print("helpers: all checks passed")

# %% OFFLINE 3: locator derivation (D8, D42, D63, D68)
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


def derive_target(el: dict, inputs: dict[str, str], warnings: list[str]) -> "Target":
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


def _extract_target(label: str, label_count: int) -> "Target":
    _refuse_if_duplicate_label(label, label_count, "labeled_value")
    return Target(primary=LabeledValueLocator(
        label=label, stability="medium",
        note="Label text is stable across releases; a labeled-value read does not depend on page position.",
    ))


# %% OFFLINE 3b: checks for locator derivation
def expect_raises(fn, expect: str):
    try:
        fn()
    except (CompileError, ValidationError, ValueError) as err:
        assert expect in str(err), f"expected {expect!r} in:\n{err}"
        return
    raise AssertionError("was NOT rejected")


# happy path: a real accessible name, unique -> role primary, no fallback needed elsewhere
login_button = {"role": "button", "name": "Log In", "name_source": "value", "label": None,
                 "text": None, "tag": "input", "type": "submit", "submit": True, "options": None,
                 "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
w = []
t = derive_target(login_button, {}, w)
assert t.primary.strategy == "role" and t.primary.name == "Log In" and t.primary.within is None
assert w == []
print("locator (happy path, role, unique):", t.primary.strategy, t.primary.name)

# duplicate name (D68), container captured -> scoped with `within`
edit_link = {"role": "link", "name": "Edit", "name_source": "text", "label": None, "text": "Edit",
             "tag": "a", "type": None, "submit": False, "options": None,
             "container": {"role": "table", "name": "Accounts"}, "nth": 2, "name_count": 2, "label_count": 1}
w = []
t = derive_target(edit_link, {}, w)
assert t.primary.strategy == "role" and t.primary.within is not None
assert t.primary.within.role == "table" and t.primary.within.name == "Accounts"
assert w == [], "a scoped duplicate should not need a warning"
print("locator (duplicate name, scoped via within):", t.primary.within)

# duplicate name, NO container captured -> saved unscoped, flagged in warnings (not refused)
edit_link_no_container = {**edit_link, "container": None, "nth": None}
w = []
t = derive_target(edit_link_no_container, {}, w)
assert t.primary.within is None and len(w) == 1 and "not unique" in w[0]
print("locator (duplicate name, no container):", w[0])

# duplicate LABEL (D68's stated gap): no `within` slot exists for label/labeled_value -> refuse
dup_label_field = {"role": "textbox", "name": "", "name_source": "none", "label": "Amount",
                    "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                    "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 2}
expect_raises(lambda: derive_target(dup_label_field, {}, []), "no `within` scope for a 'label'")
print("locator (duplicate label): correctly refused, not silently saved")

# duplicate label on an EXTRACT target -> same refusal, via _extract_target
expect_raises(lambda: _extract_target("Balance:", 2), "no `within` scope for a 'labeled_value'")
print("locator (duplicate labeled_value): correctly refused")

# an attribute-only name (fromAccountId) is NOT an accessible name -> no role locator built from it
attr_only = {"role": "textbox", "name": "fromAccountId", "name_source": "attr", "label": "From account #:",
             "text": None, "tag": "select", "type": None, "submit": False, "options": ["13344", "13355"],
             "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
t = derive_target(attr_only, {}, [])
assert t.primary.strategy == "label", "an attribute name must not become a role locator (D42)"
print("locator (attribute-only name -> label, not role): ok")

# a data-dependent name never gets a structure fallback (D42's original rule, unchanged)
data_dep = {"role": "link", "name": "13344", "name_source": "text", "label": None, "text": "13344",
            "tag": "a", "type": None, "submit": False, "options": None,
            "container": {"role": "table", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
t = derive_target(data_dep, {"account_id": "13344"}, [])
assert t.primary.name == "{{account_id}}"
assert t.fallback is None, "a data-dependent name must never get a positional structure fallback"
print("locator (data-dependent name -> no structure fallback): ok")

# nothing to identify it by at all -> refuse
expect_raises(lambda: derive_target(
    {"role": "generic", "name": "", "name_source": "none", "label": None, "text": None,
     "tag": "div", "type": None, "submit": False, "options": None, "container": None, "nth": None,
     "name_count": 1, "label_count": 1}, {}, []), "no accessible name, label, text, or container")
print("locator (nothing to identify): correctly refused")
print("locator derivation: all checks passed")

# %% OFFLINE 4: clean-up (D23, D43)
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
    left, with nothing typed, chosen, or extracted in between: both are a dead end. Remove them."""
    out, i = [], 0
    while i < len(kept):
        e, end = kept[i], None
        if e["tool"] in NAV_TOOLS and e["after"]["url"] != e["before"]["url"] and not e.get("approved"):
            for j in range(i + 1, len(kept)):
                k = kept[j]
                if k["tool"] not in NAV_TOOLS or k.get("approved"):
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


def _refuse_bad_run(events: list[dict]) -> None:
    """Top-level refusals, BEFORE any cleanup runs. A run that hit the login attempt guard, used a
    human handoff, gave up, or was declined must never become a capability at all."""
    if any(e.get("status") == "stop" for e in events):
        raise CompileError(
            "this run hit the login attempt guard (D69: 'STOP: login failed...'). "
            "Refusing to compile any capability from it."
        )
    if any(e.get("status") == "handoff" for e in events):
        raise CompileError(
            "a human entered a value by hand during this run. That step cannot be recorded. "
            "Put every value in the goal as a declared input and run again."
        )
    fin = next((e for e in events if e["tool"] == "finish"), None)
    if fin and (fin.get("summary") or "").startswith(("STUCK:", "DECLINED:")):
        raise CompileError(f"this run did not complete: {fin['summary']!r}. Refusing to compile a capability from it.")
    if any(e["tool"] == "finish_business_outcome" for e in events):
        raise CompileError("this run ended with a business outcome. It is a probe: use rule_from_probe(), not compile_run().")


# %% OFFLINE 4b: checks for clean-up
_OK = {"status": "ok"}


def _ev(i, tool, before, after, **kw):
    return {"i": i, "tool": tool, "args": kw.pop("args", {}), "status": kw.pop("status", "ok"),
            "before": {"url": before, "heading": kw.pop("before_heading", "")},
            "after": {"url": after, "heading": kw.pop("after_heading", "")}, **kw}


# observe/page_text dropped as "not an action"; a failed call dropped as "did not work"
events = [
    _ev(0, "observe", "/overview.htm", "/overview.htm"),
    _ev(1, "click", "/overview.htm", "/overview.htm", status="denied", el={"name": "register"}),
    _ev(2, "click", "/overview.htm", "/activity.htm?id=13344", el={"role": "link", "name": "13344", "name_source": "text"}),
]
kept, dropped = clean_events(events)
assert [e["i"] for e in kept] == [2]
assert dropped == [(0, "observe", "not an action"), (1, "click", "did not work (denied)")]
print("clean_events (drops non-actions and failures): ok")

# a dead-end: click away, then click back, nothing meaningful in between
events = [
    _ev(0, "click", "/overview.htm", "/billpay.htm", el={"role": "link", "name": "Bill Pay", "name_source": "text"}),
    _ev(1, "click", "/billpay.htm", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"}),
    _ev(2, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"}),
]
kept, dropped = clean_events(events)
kept = drop_detours(kept, dropped)
assert [e["i"] for e in kept] == [2]
assert dropped[0][2].startswith("dead end:") and dropped[1][2].startswith("dead end:")
print("drop_detours (removes a click-away/click-back pair):", [d[0] for d in dropped])

# trailing link click after the last meaningful step is trimmed
events = [
    _ev(0, "extract_value", "/activity.htm?id=13344", "/activity.htm?id=13344", label="Balance:", save_as="balance", value_type="currency"),
    _ev(1, "click", "/activity.htm?id=13344", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"}),
]
task = trim_tail(list(events), dropped := [])
assert [e["i"] for e in task] == [0]
assert dropped == [(1, "click", "after the last meaningful step")]
print("trim_tail (drops a trailing safe link click): ok")

# login split: two type_secret events + the click right after them
events = [
    _ev(0, "type_secret", "/index.htm", "/index.htm", value="username"),
    _ev(1, "type_secret", "/index.htm", "/index.htm", value="password"),
    _ev(2, "click", "/index.htm", "/overview.htm", el={"role": "button", "name": "Log In", "name_source": "value", "submit": True}),
    _ev(3, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"}),
]
login_ev, task_ev = split_login(events)
assert [e["i"] for e in login_ev] == [0, 1, 2] and [e["i"] for e in task_ev] == [3]
print("split_login: login =", [e["tool"] for e in login_ev], "| task =", [e["tool"] for e in task_ev])

# top-level refusals
expect_raises(lambda: _refuse_bad_run([_ev(0, "click", "/index.htm", "/index.htm", status="stop")]),
              "login attempt guard")
expect_raises(lambda: _refuse_bad_run([_ev(0, "ask_human", "/x", "/x", status="handoff")]),
              "a human entered a value by hand")
expect_raises(lambda: _refuse_bad_run([_ev(0, "finish", "/x", "/x", summary="STUCK: lost")]),
              "this run did not complete")
expect_raises(lambda: _refuse_bad_run([_ev(0, "finish_business_outcome", "/x", "/x", outcome="X", proof="p")]),
              "It is a probe")
_refuse_bad_run([_ev(0, "click", "/x", "/y")])   # a normal run: no refusal
print("clean-up: all checks passed")

# %% OFFLINE 5: parameterisation and per-step assembly (D8, D9, D10, D29, D33, D38)
SENSITIVE_WORDS = ("ssn", "password", "social")


def _params(text: str, inputs: dict[str, str], constants: list[dict], where: str) -> str:
    """A typed or chosen value. Whole-value match -> {{name}}. Otherwise substitute inside. No
    match at all -> reported as a constant, never refused (D44)."""
    for name, lit in inputs.items():
        if same_value(text, lit):
            return "{{" + name + "}}"
    out = substitute(text, inputs)
    if out == text:
        constants.append({"where": where, "value": text})
    return out


def _amount_input(specs: dict) -> str | None:
    money = [n for n, s in specs.items() if s.get("type") in ("currency", "number")]
    if len(money) == 1:
        return money[0]
    named = [n for n in money if "amount" in n]
    return named[0] if named else None


def build_steps(events: list[dict], specs: dict, warnings: list[str], constants: list):
    """Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page, and where
    the URL changed without a click."""
    inputs = {n: s["value"] for n, s in specs.items()}
    steps, outputs, secrets, paths = [], [], [], []
    prev_after = None
    for e in events:
        tool, where = e["tool"], f"event {e['i']} ({e['tool']})"
        before_url, after_url = e["before"]["url"], e["after"]["url"]
        paths += [before_url, after_url]
        if tool == "open_path":
            # e["args"]["path"] is already a relative path (the tool's own argument shape, same
            # as Navigate.path) -- CAPTURE never normalizes a URL that started out relative.
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
                value = _params(e["value"], inputs, constants, f"{where} into {el.get('label') or el.get('name')!r}")
            steps.append(TypeText(target=derive_target(el, inputs, warnings), value=value))
        elif tool == "select_option":
            if el.get("options") and e["value"] not in el["options"]:
                raise CompileError(f"{where}: option {e['value']!r} is not in the dropdown's options")
            steps.append(Select(
                target=derive_target(el, inputs, warnings),
                option=_params(e["value"], inputs, constants, f"{where} in {el.get('label') or el.get('name')!r}"),
            ))
        elif tool == "extract_value":
            label = substitute(e["label"], inputs)
            steps.append(Extract(target=_extract_target(label, e.get("label_count", 1)), save_as=e["save_as"]))
            outputs.append(OutputParam(
                name=e["save_as"], type=e.get("value_type", "string"),
                description=e.get("description") or f"The value shown next to '{e['label']}'.",
            ))
    return steps, outputs, secrets, paths


def find_leftovers(cap: "Capability", inputs: dict) -> list[str]:
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


def _checkpoint_from_last(events: list[dict]) -> "Checkpoint":
    last = events[-1]
    heading = (last["after"].get("heading") or "").strip()
    if not heading:
        raise CompileError("the final kept step's page has no heading, so the checkpoint has no text signal (D9 needs both)")
    url = last["after"]["url"]
    return Checkpoint(url_contains=path_only(url).rsplit("/", 1)[-1] or "/", text_present=heading)


def _cap(name: str, description: str, events: list[dict], specs: dict, rules: list,
         constants: list, warnings: list[str], base_url: str) -> "Capability":
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


def relogin_rule() -> "OutcomeRule":
    return OutcomeRule(when=Condition(text_present=SESSION_EXPIRED_TEXT), kind="recoverable", action="relogin",
                       message="The session expired. Run the login capability again and continue.")


def rule_from_probe(events: list[dict], probe_inputs: dict[str, str]) -> "OutcomeRule":
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
    specs = spec["inputs"]
    _check_specs(specs)

    kept, dropped = clean_events(events)
    kept = drop_detours(kept, dropped)
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


# %% OFFLINE 6: save (only after validation) and show
def save_capability(cap: "Capability", out_dir: pathlib.Path = ARTIFACTS, *, forbidden=()) -> pathlib.Path:
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
    path.write_text("# DRAFT written by the recorder (Phase 3 v2). A reviewer must read it before it is verified.\n" + text)
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


print("compile ready")

# %% [markdown]
# ## Offline fixtures and checks (hand-made events, no browser)
# Every fixture below is shaped exactly like what agent.ipynb's tools + the CAPTURE wrapper
# (Part B) actually produce -- built from the literal message prefixes read out of `agent.ipynb`
# STEP 3, not invented text. See `docs/superpowers/plans/2026-09-25-phase3-recorder-v2.md`'s
# fixture table for the numbering used in comments below.

# %% OFFLINE 7: fixture 1 -- good balance-lookup flow, login split out correctly
def _e(i, tool, before, after, **kw):
    """Same shape as `_ev` above, kept separate so a message/status default of 'ok' can still be
    overridden by a fixture that wants to show a non-ok event."""
    msg = kw.pop("message", None)
    status = kw.pop("status", classify_status(msg) if msg is not None else "ok")
    return {"i": i, "tool": tool, "args": kw.pop("args", {}),
            "before": {"url": before, "heading": kw.pop("before_heading", "")},
            "after": {"url": after, "heading": kw.pop("after_heading", "")},
            "message": msg or "", "status": status, **kw}


BAL_SPEC = {
    "name": "get_account_balance",
    "description": "Read the current balance of one account, given its account id.",
    "inputs": {"account_id": {"value": "13344", "type": "string", "description": "The account number.", "pattern": r"^[0-9]{4,10}$"}},
}

LOGIN_BUTTON_EL = {"role": "button", "name": "Log In", "name_source": "value", "label": None,
                    "text": None, "tag": "input", "type": "submit", "submit": True, "options": None,
                    "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
USERNAME_FIELD_EL = {"role": "textbox", "name": "Username", "name_source": "label", "label": "Username",
                      "text": None, "tag": "input", "type": "text", "submit": False, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
PASSWORD_FIELD_EL = {"role": "textbox", "name": "Password", "name_source": "label", "label": "Password",
                      "text": None, "tag": "input", "type": "password", "submit": False, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 2, "name_count": 1, "label_count": 1}


def _balance_events(extra_description: str | None = None) -> list[dict]:
    return [
        _e(0, "observe", "/index.htm", "/index.htm", before_heading="Customer Login", after_heading="Customer Login"),
        _e(1, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
        _e(2, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
        _e(3, "click", "/index.htm", "/overview.htm", el=LOGIN_BUTTON_EL, message="Clicked [3].",
           before_heading="Customer Login", after_heading="Accounts Overview"),
        _e(4, "open_path", "/overview.htm", "/activity.htm?id=13344", args={"path": "/activity.htm?id=13344"},
           message="Opened /activity.htm?id=13344.", before_heading="Accounts Overview", after_heading="Account Details"),
        _e(5, "extract_value", "/activity.htm?id=13344", "/activity.htm?id=13344",
           label="Balance:", save_as="balance", value_type="currency",
           description=extra_description or "Current balance, for example $1,200.00.",
           message="Read 'Balance:'.", before_heading="Account Details", after_heading="Account Details"),
        _e(6, "finish", "/activity.htm?id=13344", "/activity.htm?id=13344",
           summary="Read the balance.", values={"balance": "$1,200.00"}, message="Recorded. Stop now."),
    ]


result = compile_run(_balance_events(), BAL_SPEC)
login, task, report = result["login"], result["task"], result["report"]
assert login is not None and login.name == "login_parabank" and len(login.secrets) == 2
assert [s.action for s in login.steps] == ["navigate", "type", "type", "click"]
assert login.steps[0].path == "/index.htm"
assert login.checkpoint.url_contains == "overview.htm" and login.checkpoint.text_present == "Accounts Overview"
assert task.name == "get_account_balance" and task.secrets == []
assert [s.action for s in task.steps] == ["navigate", "extract"]
assert task.steps[0].path == "/activity.htm?id={{account_id}}"
assert task.inputs[0].name == "account_id"
assert task.outputs[0].name == "balance" and task.outputs[0].type == "currency"
assert task.risk_level == "safe"
assert any(r.kind == "recoverable" and r.action == "relogin" for r in task.outcome_rules)
assert (0, "observe", "not an action") in report["dropped"]
assert from_yaml(to_yaml(task)) == task and from_yaml(to_yaml(login)) == login
print("fixture 1 (good balance flow, login split): ok")
show(result)

# %% OFFLINE 8: fixture 2 -- a dead-end click is removed
def _balance_events_with_detour() -> list[dict]:
    ev = _balance_events()
    detour = [
        _e(40, "click", "/overview.htm", "/billpay.htm", el={"role": "link", "name": "Bill Pay", "name_source": "text"},
           message="Clicked [4]."),
        _e(41, "click", "/billpay.htm", "/overview.htm", el={"role": "link", "name": "Accounts Overview", "name_source": "text"},
           message="Clicked [2]."),
    ]
    return ev[:4] + detour + ev[4:]


result2 = compile_run(_balance_events_with_detour(), BAL_SPEC)
assert [s.action for s in result2["task"].steps] == ["navigate", "extract"], "the detour must not survive into steps"
dead_ends = [d for d in result2["report"]["dropped"] if d[2].startswith("dead end:")]
assert len(dead_ends) == 2 and {d[0] for d in dead_ends} == {40, 41}
print("fixture 2 (dead-end click removed):", dead_ends)

# %% OFFLINE 9: fixture 5 -- leftover-literal refusal
LEAKY_SPEC = {**BAL_SPEC}
leaky_events = _balance_events(extra_description="Current balance of account 13344.")
try:
    compile_run(leaky_events, LEAKY_SPEC)
    raise AssertionError("was NOT rejected")
except CompileError as err:
    assert any("account_id" in p and "description" in p for p in err.problems), err.problems
    print("fixture 5 (leftover-literal refusal):", err.problems)

# %% OFFLINE 10: fixture 6 -- a risky click produces risk: risky + a matching risk_level
XFER_SPEC = {
    "name": "transfer_funds",
    "description": "Move a stated amount from one account to another.",
    "inputs": {"amount": {"value": "20.00", "type": "currency", "description": "Amount to move.",
                          "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"}},
}
TRANSFER_BUTTON_EL = {"role": "button", "name": "Transfer", "name_source": "value", "label": None,
                      "text": None, "tag": "input", "type": "submit", "submit": True, "options": None,
                      "container": {"role": "form", "name": None}, "nth": 1, "name_count": 1, "label_count": 1}
xfer_events = [
    _e(0, "click", "/transfer.htm", "/transfer.htm", el=TRANSFER_BUTTON_EL, approved=True,
       message="Clicked [5].", before_heading="Transfer Funds", after_heading="Transfer Complete!"),
    _e(1, "finish", "/transfer.htm", "/transfer.htm", summary="Transferred the amount.",
       values={"confirmation": "Transfer Complete!"}, message="Recorded. Stop now."),
]
xfer_result = compile_run(xfer_events, XFER_SPEC)
xfer_task = xfer_result["task"]
click_step = xfer_task.steps[-1]
assert click_step.action == "click" and click_step.risk == "risky" and click_step.amount_input == "amount"
assert xfer_task.risk_level == "risky"
assert xfer_task.checkpoint.url_contains == "transfer.htm" and xfer_task.checkpoint.text_present == "Transfer Complete!"
print("fixture 6 (risky click -> risk: risky, risk_level: risky, amount_input='amount'): ok")

# %% OFFLINE 11: fixture 7 -- a bad-input probe run produces a business OutcomeRule
probe_events = [
    _e(0, "open_path", "/overview.htm", "/activity.htm?id=00000", args={"path": "/activity.htm?id=00000"},
       message="Opened /activity.htm?id=00000."),
    _e(1, "finish_business_outcome", "/activity.htm?id=00000", "/activity.htm?id=00000",
       outcome="ACCOUNT_NOT_FOUND", proof="Could not find account 00000",
       message="Recorded as a business-outcome probe. Stop now."),
]
rule = rule_from_probe(probe_events, {"account_id": "00000"})
assert rule.kind == "business" and rule.outcome == "ACCOUNT_NOT_FOUND"
assert rule.when.text_present == "Could not find account"
print("fixture 7a (business outcome rule from a probe):", rule.when.text_present, "->", rule.outcome)

try:
    compile_run(probe_events, BAL_SPEC)
    raise AssertionError("was NOT rejected")
except CompileError as err:
    assert "It is a probe" in str(err)
    print("fixture 7b (a probe run is never compiled as a task): correctly refused")

# a real task run, with the probe's rule merged in as extra_rules
merged = compile_run(_balance_events(), BAL_SPEC, extra_rules=[rule])
assert any(r.kind == "business" and r.outcome == "ACCOUNT_NOT_FOUND" for r in merged["task"].outcome_rules)
print("fixture 7c (probe's rule merged into a real task capability): ok")

# %% OFFLINE 12: fixture 8 -- a run that hit the login-attempt guard is refused entirely
guard_events = [
    _e(0, "type_secret", "/index.htm", "/index.htm", el=USERNAME_FIELD_EL, value="username", message="Typed secret 'username' into [1]."),
    _e(1, "type_secret", "/index.htm", "/index.htm", el=PASSWORD_FIELD_EL, value="password", message="Typed secret 'password' into [2]."),
    _e(2, "click", "/index.htm", "/index.htm", el=LOGIN_BUTTON_EL,
       message="STOP: login failed (login was attempted 3 times with no success). Do not try again. Call finish with a summary starting 'STUCK:' explaining this."),
]
assert guard_events[2]["status"] == "stop"
try:
    compile_run(guard_events, BAL_SPEC)
    raise AssertionError("was NOT rejected")
except CompileError as err:
    assert "login attempt guard" in str(err)
    print("fixture 8 (login-attempt-guard STOP refused entirely):", err)

# %% OFFLINE 13: save_capability -- happy path, secret-value guard, verified-overwrite guard
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    path = save_capability(task, out_dir=tmp)
    assert path.name == "get_account_balance.yaml"
    reloaded = from_yaml(path.read_text().split("\n", 1)[1])   # strip the leading "# DRAFT" comment line
    assert reloaded == task
    print("save_capability (happy path):", path.name)

    fake = Capability.model_validate({
        **task.model_dump(mode="json", exclude_none=True), "name": "fake_secret_cap",
        "description": "hunter2 lives in this description on purpose, to test the save guard.",
    })
    try:
        save_capability(fake, out_dir=tmp, forbidden=["hunter2"])
        raise AssertionError("was NOT rejected")
    except CompileError as err:
        assert "secret value would be written" in str(err)
        print("save_capability (secret-value guard):", err)

    verified_path = tmp / "already_verified.yaml"
    verified_cap = Capability.model_validate({**task.model_dump(mode="json", exclude_none=True), "name": "already_verified", "status": "verified"})
    verified_path.write_text(to_yaml(verified_cap))
    draft_same_name = Capability.model_validate({**task.model_dump(mode="json", exclude_none=True), "name": "already_verified"})
    try:
        save_capability(draft_same_name, out_dir=tmp)
        raise AssertionError("was NOT rejected")
    except CompileError as err:
        assert "already verified" in str(err)
        print("save_capability (never overwrite verified):", err)

print("save_capability: all checks passed")

# %% [markdown]
# ### TypeSafe (D50/D52), added at the user's request 2026-09-25
# agent.ipynb's own tool-selection and model-routing middleware (`STEP 3d`/`STEP 3e`, the
# TypeSafe half of `STEP 4`) is a major, load-bearing part of that notebook, so it is copied here
# too -- not left out. Copied verbatim: `TypeSafeToolRouterMiddleware` (the `Choice`-based
# tool-selection layer) and `ModelRouterMiddleware` (the Haiku/Sonnet router). Both stay **off by
# default**, exactly as in agent.ipynb: they only activate if `TYPESAFE_API_KEY` is set in `.env`.
#
# **One small, additive, clearly-labelled extension, not a rewrite:** agent.ipynb's own
# `JOB_EXTRA_TOOLS` mapping predates `request_missing_values` (D55) and, in this notebook, also
# predates `extract_value`/`open_path`/`finish_business_outcome` (all new here, D73) -- none of
# them belong to any of the four job categories the classifier knows about. Left alone, an active
# TypeSafe router could silently strip them from the tool list whenever its job classification is
# confident about something else. The fix is the same one D52 already committed to for exactly
# this situation ("never removes the always-allowed set"): these four tool names are added to
# `NEVER_HIDE` (see D76), so they always survive tool-selection, regardless of the classified job.
# `JOB_EXTRA_TOOLS`/`JOB_CRITERIA` themselves are untouched.

# %% OFFLINE 13b: TypeSafe job mapping and confidence gate (pure, no network -- copied verbatim
# from agent.ipynb STEP 3d/3e, then additively extended per the markdown cell above and D76)
NEVER_HIDE = {"observe", "click", "type_secret", "finish"}   # always allowed, whatever the job -- unchanged from agent.ipynb

JOB_EXTRA_TOOLS = {
    "login":      {"type_secret"},
    "fill_form":  {"type_text", "select_option"},
    "read_value": {"page_text"},
    "need_human": {"request_value", "ask_human"},
}
JOB_CRITERIA = {
    "login": "The page shows a username or password field, or we have not logged in yet.",
    "fill_form": "A form is on screen and a field still needs a value typed or a dropdown chosen.",
    "read_value": "We need to read a value already on the page, such as a balance or a confirmation message.",
    "need_human": "We are unsure which element to use, or a value we need was not given by the user.",
}
JOB_CONFIDENCE_THRESHOLD = 0.8


def job_tool_names(job: str) -> set[str]:
    """Tools this job needs, plus the always-allowed set. Pure: no network, no LLM."""
    return NEVER_HIDE | JOB_EXTRA_TOOLS.get(job, set())


def confidence_gate(base_tools: set[str], job: str, confidence: float,
                     threshold: float = JOB_CONFIDENCE_THRESHOLD) -> set[str]:
    """Narrow base_tools to this job's tools, but only if the classifier is confident.
    Below the threshold, fail OPEN: return base_tools unchanged rather than guess wrong."""
    if confidence < threshold:
        return base_tools
    return base_tools & job_tool_names(job)


# D76 (additive, not in agent.ipynb): this notebook's own new tools, and request_missing_values
# (already in agent.ipynb's BROWSER_TOOLS since D55 but never added to JOB_EXTRA_TOOLS there
# either -- a pre-existing gap, not introduced here), must never be silently stripped by the job
# router just because agent.ipynb's job mapping predates them.
NEVER_HIDE = NEVER_HIDE | {"request_missing_values", "extract_value", "open_path", "finish_business_outcome"}

# %% OFFLINE 13c: offline checks (copied verbatim from agent.ipynb STEP 3e, plus checks for the
# D76 extension above). No network, no key.
_ALL = {"observe", "click", "type_text", "type_secret", "select_option", "page_text",
        "request_value", "request_missing_values", "ask_human", "finish",
        "extract_value", "open_path", "finish_business_outcome"}

assert confidence_gate(_ALL, "login", 0.9) == NEVER_HIDE | {"type_secret"}
# NOTE: agent.ipynb's own STEP 3e literally has `confidence_gate(_ALL, "fill_form", 0.75)` here,
# asserted equal to a NARROWED set. That is mathematically false: 0.75 < JOB_CONFIDENCE_THRESHOLD
# (0.8), so confidence_gate fails OPEN at 0.75 and returns _ALL unchanged, not a narrowed set.
# Verified directly (not assumed) by running agent.ipynb's own confidence_gate with these exact
# values: confidence_gate(_ALL, "fill_form", 0.75) == _ALL, not NEVER_HIDE | {"type_text",
# "select_option"}. agent.ipynb's own copy of this cell shows no executed output in the .ipynb
# (unlike the cells around it), consistent with this assertion never actually having been run.
# Not fixed in agent.ipynb (read-only); fixed here (0.85, confidently above threshold) since this
# notebook actually executes its own offline checks.
assert confidence_gate(_ALL, "fill_form", 0.85) == NEVER_HIDE | {"type_text", "select_option"}
assert confidence_gate(_ALL, "read_value", 0.8) == NEVER_HIDE | {"page_text"}
assert confidence_gate(_ALL, "need_human", 0.99) == NEVER_HIDE | {"request_value", "ask_human"}
assert confidence_gate(_ALL, "login", 0.59) == _ALL                          # low confidence: fail open
assert confidence_gate(_ALL, "login", JOB_CONFIDENCE_THRESHOLD) == NEVER_HIDE | {"type_secret"}  # boundary is inclusive
_from_triage = _ALL - {"request_value", "ask_human"}
assert NEVER_HIDE <= confidence_gate(_from_triage, "fill_form", 0.9)          # never-hide survives even when the base tool set is already reduced
assert confidence_gate(_ALL, "not_a_real_job", 0.95) == NEVER_HIDE           # unknown job: no crash, no extras
print("typesafe job-router checks passed")

# D76's own extension, checked directly: the three new tools + request_missing_values always
# survive tool-selection, whatever job is classified, confident or not.
_NEW_TOOLS = {"request_missing_values", "extract_value", "open_path", "finish_business_outcome"}
assert _NEW_TOOLS <= NEVER_HIDE
for _job in ("login", "fill_form", "read_value", "need_human", "not_a_real_job"):
    assert _NEW_TOOLS <= confidence_gate(_ALL, _job, 0.99), f"job {_job!r} must not strip the new tools"
print("D76 (new tools always survive tool-selection): all checks passed")

# %% OFFLINE 14: summary
print("\nALL OFFLINE CHECKS PASSED")

# %% [markdown]
# ## Part B. CAPTURE (browser, never run by this agent -- the user runs this)
#
# **This is a deliberate, temporary duplication of `agent.ipynb`, not a fork of it.** Phase 9
# consolidates both into one shared module. The cells below marked "copied verbatim" are copied,
# cell for cell, from the CURRENT `notebooks/agent.ipynb` as it stood on 2026-09-25 (15 real code
# cells at that time). The exact source cells copied are:
# 1. `Setup 1/4: config + secrets`
# 2. `Setup 2/4: browser`
# 3. `Setup 3/4: domain guard`
# 4. `Setup 4/4: numbered screenshot (PlaywrightSurface)`
# 5. `STEP 1: scanner patch (dropdown options + submit flag)`
# 6. `STEP 2: banner, takeover, Approve / Reject / Take over buttons, hand_off`
# 7. `STEP 3: browser tools`
# 8. `STEP 3d: TypeSafe tool selection (Choice)` -- copied verbatim, D50/D52, D76 below
# 9. `STEP 3e: offline checks for the job mapping and the confidence gate` -- copied verbatim
# 10. The TypeSafe half of `STEP 4: system prompt and agents` (the Haiku/Sonnet model router)
#
# `STEP 3d`/`STEP 3e`/the TypeSafe half of `STEP 4` were added 2026-09-25 at the user's explicit
# request ("it is a major part of the agent"). Both stay **off by default**, exactly as in
# agent.ipynb: only `TYPESAFE_API_KEY` being set in `.env` activates them. See the markdown cell
# right before the TypeSafe cells for the one small, labelled extension this required (D76:
# `NEVER_HIDE` grows to cover this notebook's own new tools, which predate agent.ipynb's job
# mapping). `web_search` is still left off the tool list here, per D48's original reasoning
# (unchanged): it sends goal/page text to a third party outside the allowlist, and discovery for a
# capability recording does not need outside facts -- this is unrelated to the TypeSafe decision.
#
# Cells after `STEP 3` (other than the TypeSafe ones above) are new, additive, and clearly
# labelled: they wrap each tool to log an event, and add three small new tools the compiler needs
# that agent.ipynb has no reason to carry itself (`extract_value`, `open_path`,
# `finish_business_outcome`). None of them touch the body of any tool copied above.
#
# ## How the user tests this
# Before you start: `.env` has the API key and the ParaBank test user. Kernel = this repo's
# `.venv`. ParaBank is up. Run cells top to bottom.
#
# | Step | Run cells | What you should see (exact lines) |
# |---|---|---|
# | 1. Browser setup | `BROWSER 1` to `BROWSER 7` (verbatim) | `model: anthropic:claude-sonnet-5 \| base: https://parabank.parasoft.com/parabank`, then `opened: https://parabank.parasoft.com/parabank/index.htm`, then `[lock] initial setup done ...`, then `tools ready: ['observe', 'click', 'type_text', 'type_secret', 'select_option', 'page_text', 'request_value', 'request_missing_values', 'ask_human', 'finish']` |
# | 2. Capture additions | `BROWSER 8` to `BROWSER 10` | `capture ready: ['observe', 'click', 'type_text', 'type_secret', 'select_option', 'page_text', 'request_value', 'request_missing_values', 'ask_human', 'finish', 'extract_value', 'open_path', 'finish_business_outcome']` |
# | 3. TypeSafe (D50/D52/D76) + agent | `BROWSER 11` to `BROWSER 12` | `TypeSafe tool router middleware ready (activates only if TYPESAFE_API_KEY is set below)`, then either `model router OFF: no TYPESAFE_API_KEY in .env. Using MODEL only: anthropic:claude-sonnet-5` (no key set) or `model router ON (TypeSafe): fast=... \| powerful=...` (key set), then `agent ready (capture)` |
# | 4. A good balance run, starting logged out | `BROWSER 14`, with `GOAL = "Log in and read the balance of account <YOUR_ACCOUNT_ID>."` (an account you own) | the agent logs in, opens the account, reads the balance. Then `AGENT SAID: ...`, then `captured N events`, then a printed table of events. You should see `type_secret` twice, `click` (Log In), `open_path` or `click` (reaching the account), `extract_value`, `finish` |
# | 5. A bad-input probe (needs run 4's login still active) | `BROWSER 15`, with `GOAL = "Open account <A_BAD_ACCOUNT_ID> and, if it does not exist, call finish_business_outcome with outcome='ACCOUNT_NOT_FOUND' and the exact page text that proves it."` | `AGENT SAID: ...` ending in a `finish_business_outcome` call; `captured N events`; the last event's `tool` is `finish_business_outcome` with `status: ok` |
# | 6. Compile and save | `BROWSER 16` | two YAML blocks (`----- login: login_parabank -----`, `----- task: get_account_balance -----`, now including the business outcome rule from step 5), then `----- report -----`, then `saved: artifacts/login_parabank.yaml` and `saved: artifacts/get_account_balance.yaml` |
# | 7. Optional, risky flow | `BROWSER 17`, with a transfer goal | the browser shows the dark decision bar ("Agent wants to click 'Transfer'"). Click **Approve**. Then a YAML with `risk: risky` and `amount_input`, and `saved: artifacts/transfer_funds.yaml` |
#
# **Send back:** (1) the `tools ready:`/`capture ready:`/model-router lines, (2) the printed event
# tables from steps 4 and 5, (3) the two saved YAML files (or paste them), (4) the
# `----- report -----` block, (5) any red error, exactly as shown. Never paste `.env` or anything
# typed as a secret.

# %% BROWSER 1: Setup 1/4 (copied verbatim from agent.ipynb)
import os
import asyncio
import base64
import json
import re
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-5")
BASE = "https://parabank.parasoft.com/parabank"
ALLOWED_HOSTS = {"parabank.parasoft.com"}
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}


def resolve_secret(name: str) -> str:
    """Look up a secret by name. Raises on unknown name or empty value."""
    if name not in SECRETS:
        raise KeyError(f"unknown secret name: {name!r}")
    value = os.environ.get(SECRETS[name], "")
    if not value:
        raise RuntimeError(f"env var {SECRETS[name]} is empty or not set")
    return value


print("model:", MODEL, "| base:", BASE)

# %% BROWSER 2: Setup 2/4 (copied verbatim from agent.ipynb)
from playwright.async_api import async_playwright

if "page" not in globals():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
await page.goto(f"{BASE}/index.htm")
print("opened:", page.url)

# %% BROWSER 3: Setup 3/4 (copied verbatim from agent.ipynb)
from urllib.parse import urlparse


def host_allowed(url: str) -> bool:
    if url == "about:blank":
        return True
    return urlparse(url).hostname in ALLOWED_HOSTS

# %% BROWSER 4: Setup 4/4 (copied verbatim from agent.ipynb)
from dataclasses import dataclass

OBSERVE_JS = """
() => {
  document.querySelectorAll('[data-cua-ref]').forEach(e => e.removeAttribute('data-cua-ref'));
  const sel = 'a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [onclick]';
  const roleOf = (el) => {
    const r = el.getAttribute('role'); if (r) return r;
    const t = el.tagName.toLowerCase();
    if (t === 'a') return 'link';
    if (t === 'button') return 'button';
    if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') {
      const ty = (el.getAttribute('type') || 'text').toLowerCase();
      if (['submit', 'button', 'reset', 'image'].includes(ty)) return 'button';
      if (ty === 'checkbox') return 'checkbox';
      if (ty === 'radio') return 'radio';
      return 'textbox';
    }
    return 'generic';
  };
  const nameOf = (el) => {
    const aria = el.getAttribute('aria-label'); if (aria) return aria.trim();
    if (el.labels && el.labels.length) return el.labels[0].innerText.trim();
    const t = el.tagName.toLowerCase();
    const ty = (el.getAttribute('type') || '').toLowerCase();
    if (t === 'input' && ['submit', 'button', 'reset'].includes(ty)) return (el.value || '').trim();
    const txt = (el.innerText || '').trim(); if (txt) return txt.slice(0, 80);
    return (el.getAttribute('placeholder') || el.getAttribute('title') ||
            el.getAttribute('alt') || el.getAttribute('name') || '').trim();
  };
  const items = [];
  document.querySelectorAll(sel).forEach((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width < 2 || r.height < 2 || st.visibility === 'hidden' || st.display === 'none') return;
    const ref = items.length + 1;
    el.setAttribute('data-cua-ref', String(ref));
    const valueOf = (el) => {
      const t = el.tagName.toLowerCase();
      if (t === 'select') return el.selectedOptions[0] ? el.selectedOptions[0].text.trim() : '';
      if (t === 'input' || t === 'textarea') {
        const ty = (el.getAttribute('type') || 'text').toLowerCase();
        if (['submit', 'button', 'reset', 'image', 'password'].includes(ty)) return '';
        return (el.value || '').trim();
      }
      return '';
    };
    items.push({
      ref, role: roleOf(el), name: nameOf(el), value: valueOf(el),
      x: r.x, y: r.y, w: r.width, h: r.height,
      inViewport: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
    });
  });
  return items;
}
"""

DRAW_JS = """
(items) => {
  const box = document.createElement('div');
  box.id = '__cua_overlay';
  box.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  items.filter(i => i.inViewport).forEach(i => {
    const b = document.createElement('div');
    b.style.cssText = `position:fixed;left:${i.x}px;top:${i.y}px;width:${i.w}px;height:${i.h}px;border:2px solid red;box-sizing:border-box`;
    const l = document.createElement('span');
    l.textContent = i.ref;
    l.style.cssText = 'position:absolute;left:0;top:-14px;background:red;color:#fff;font:bold 11px monospace;padding:0 3px';
    b.appendChild(l);
    box.appendChild(b);
  });
  document.body.appendChild(box);
}
"""

CLEAR_JS = "() => { const o = document.getElementById('__cua_overlay'); if (o) o.remove(); }"


def format_elements(elements: list[dict]) -> str:
    lines = []
    for e in elements:
        line = f'[{e["ref"]}] {e["role"]} "{e["name"]}"'
        if e.get("value"):
            line += f' = {e["value"]!r}'      # already-typed content, so the model does not have to guess from pixels
        if e.get("options"):
            line += f' options={e["options"]}'
        if not e["inViewport"]:
            line += " (below the fold)"
        lines.append(line)
    return "\n".join(lines)


@dataclass
class Observation:
    png: bytes
    elements: list[dict]
    url: str
    title: str

    def as_text(self) -> str:
        return f"URL: {self.url}\nTitle: {self.title}\nElements:\n{format_elements(self.elements)}"


class PlaywrightSurface:
    """The only place that touches Playwright. Agent tools talk to this."""

    def __init__(self, page):
        self.page = page
        self.last_elements: list[dict] = []

    async def observe(self) -> Observation:
        elements = await self.page.evaluate(OBSERVE_JS)
        await self.page.evaluate(DRAW_JS, elements)
        png = await self.page.screenshot()
        await self.page.evaluate(CLEAR_JS)
        self.last_elements = elements
        return Observation(png, elements, self.page.url, await self.page.title())

    def name_of(self, ref: int) -> str | None:
        for e in self.last_elements:
            if e["ref"] == ref:
                return e["name"]
        return None

# %% BROWSER 5: STEP 1 (copied verbatim from agent.ipynb)
OBSERVE_JS = OBSERVE_JS.replace(
    "inViewport: r.bottom",
    "options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text.trim()).slice(0, 15) : null,\n"
    "      submit: (el.tagName === 'BUTTON' && el.type !== 'button') || (el.tagName === 'INPUT' && ['submit', 'image'].includes(el.type)),\n"
    "      inViewport: r.bottom",
)
assert "options:" in OBSERVE_JS and "submit:" in OBSERVE_JS, "patch did not apply"


def format_elements(elements: list[dict]) -> str:
    lines = []
    for e in elements:
        line = f'[{e["ref"]}] {e["role"]} "{e["name"]}"'
        if e.get("options"):
            line += f' options={e["options"]}'
        if not e["inViewport"]:
            line += " (below the fold)"
        lines.append(line)
    return "\n".join(lines)


# %% BROWSER 6: STEP 2 (copied verbatim from agent.ipynb)
import asyncio
from langgraph.types import Command

HANDBACK = {"event": None}

# ---- Approve / Reject / Take over buttons (their own floating bar, always clickable) ----
DECISION_JS = """(info) => new Promise(resolve => {
  const bar = document.createElement('div');
  bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#111;color:#fff;font:14px sans-serif;padding:10px;display:flex;flex-direction:column;gap:8px;align-items:center';
  const t = document.createElement('b'); t.textContent = info.title;
  const d = document.createElement('div'); d.textContent = info.details;
  const row = document.createElement('div'); row.style.cssText = 'display:flex;gap:12px';
  [['Approve', 'a'], ['Reject', 'r'], ['Take over', 't']].forEach(([label, val]) => {
    const b = document.createElement('button'); b.textContent = label;
    b.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
    b.onclick = () => { bar.remove(); resolve(val); };
    row.appendChild(b);
  });
  bar.append(t, d, row);
  document.body.appendChild(bar);
})"""

# ---- Whole-page lock: while it is the agent's turn, a real human can neither click nor type
# anywhere on the page. Our own injected UI (this banner, the decision bar above) always sits
# on a higher z-index, so it stays usable regardless of lock state. Our OWN automated actions
# use force=True (STEP 3), which bypasses this overlay entirely -- it only stops a real human's
# mouse and keyboard, never Playwright's own dispatched actions. ----
LOCK_JS = """
() => {
  if (!document.getElementById('__cua_lock')) {
    const d = document.createElement('div');
    d.id = '__cua_lock';
    d.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:transparent;';
    document.documentElement.appendChild(d);
  }
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  if (!window.__cuaBlockKeys) {
    // Let typing through for an element explicitly poked open by RESTRICT_JS (allow_refs mode).
    // Without this check, the click-blocking overlay and the keyboard block were two separate
    // mechanisms: raising an element's z-index let a click focus it, but every keystroke was
    // still swallowed here, at the document level, regardless of what had focus.
    window.__cuaBlockKeys = (e) => {
      if (e.target && e.target.classList && e.target.classList.contains('__cua_allowed')) return;
      e.preventDefault(); e.stopPropagation();
    };
    document.addEventListener('keydown', window.__cuaBlockKeys, true);
    document.addEventListener('keypress', window.__cuaBlockKeys, true);
  }
}
"""
UNLOCK_JS = """
() => {
  document.getElementById('__cua_lock')?.remove();
  if (window.__cuaBlockKeys) {
    document.removeEventListener('keydown', window.__cuaBlockKeys, true);
    document.removeEventListener('keypress', window.__cuaBlockKeys, true);
    window.__cuaBlockKeys = null;
  }
}
"""

# ---- Risky-element block: separate from the general lock above. During a GENERAL takeover
# (filling in a field), the rest of the page opens up but the risky button must still stay
# non-interactive. Only the take-over-to-submit case turns this off too. ----
BLOCK_JS = """(refs) => {
  document.querySelectorAll('.__cua_blocked').forEach(el => {
    el.classList.remove('__cua_blocked');
    el.style.filter = ''; el.style.pointerEvents = ''; el.style.opacity = '';
  });
  refs.forEach(ref => {
    const el = document.querySelector(`[data-cua-ref="${ref}"]`);
    if (el) { el.classList.add('__cua_blocked'); el.style.filter = 'blur(3px)'; el.style.pointerEvents = 'none'; el.style.opacity = '0.5'; }
  });
}"""
UNBLOCK_JS = "() => document.querySelectorAll('.__cua_blocked').forEach(el => { el.classList.remove('__cua_blocked'); el.style.filter = ''; el.style.pointerEvents = ''; el.style.opacity = ''; })"

# ---- Restrict to specific fields: keep the general lock fully ACTIVE, and poke a hole (raise
# z-index above the lock, but below our own UI) for ONLY the given refs. A visible green outline
# shows the human exactly what is expected. Used by request_value/request_missing_values, where
# we know precisely which field(s) are needed -- unlike ask_human or the approval take-over,
# which genuinely need broader access. ----
RESTRICT_JS = """(refs) => {
  document.querySelectorAll('.__cua_allowed').forEach(el => {
    el.classList.remove('__cua_allowed');
    el.style.position = ''; el.style.zIndex = ''; el.style.outline = '';
  });
  refs.forEach(ref => {
    const el = document.querySelector(`[data-cua-ref="${ref}"]`);
    if (el) {
      el.classList.add('__cua_allowed');
      if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
      el.style.zIndex = '2147483001';
      el.style.outline = '3px solid #2a7';
    }
  });
}"""
UNRESTRICT_JS = "() => document.querySelectorAll('.__cua_allowed').forEach(el => { el.classList.remove('__cua_allowed'); el.style.position = ''; el.style.zIndex = ''; el.style.outline = ''; })"

BANNER_ONLY_JS = """
() => {
  if (document.getElementById('__cua_banner')) return;
  const q = sessionStorage.getItem('cua_question') || '';
  const b = document.createElement('div');
  b.id = '__cua_banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#c00;color:#fff;font:14px sans-serif;padding:8px;display:flex;gap:12px;align-items:center;justify-content:center';
  const label = document.createElement('b'); label.textContent = 'YOU are in control.';
  const msg = document.createElement('span'); msg.textContent = q ? 'Agent asks: ' + q : 'Do the step in this page.';
  const btn = document.createElement('button'); btn.textContent = 'Done, hand back to agent';
  btn.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
  btn.onclick = () => window.__cua_handback();
  b.append(label, msg, btn);
  document.documentElement.appendChild(b);
}
"""

# ---- "You are in control" bar with a Done button. Runs on every page load (add_init_script);
# also applied immediately to the current page. Locked/unlocked state is driven by the SAME
# 'cua_takeover' sessionStorage flag, so both stay in sync across navigations for free. ----
SYNC_UI_JS = """
(() => {
  const active = sessionStorage.getItem('cua_takeover') === '1';
  if (!active) {
    if (!document.getElementById('__cua_lock')) {
      const d = document.createElement('div');
      d.id = '__cua_lock';
      d.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:transparent;';
      document.documentElement.appendChild(d);
    }
    if (!window.__cuaBlockKeys) {
      window.__cuaBlockKeys = (e) => {
        if (e.target && e.target.classList && e.target.classList.contains('__cua_allowed')) return;
        e.preventDefault(); e.stopPropagation();
      };
      document.addEventListener('keydown', window.__cuaBlockKeys, true);
      document.addEventListener('keypress', window.__cuaBlockKeys, true);
    }
    document.getElementById('__cua_banner')?.remove();
    return;
  }
  document.getElementById('__cua_lock')?.remove();
  if (window.__cuaBlockKeys) {
    document.removeEventListener('keydown', window.__cuaBlockKeys, true);
    document.removeEventListener('keypress', window.__cuaBlockKeys, true);
    window.__cuaBlockKeys = null;
  }
  if (document.getElementById('__cua_banner')) return;
  const q = sessionStorage.getItem('cua_question') || '';
  const b = document.createElement('div');
  b.id = '__cua_banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#c00;color:#fff;font:14px sans-serif;padding:8px;display:flex;gap:12px;align-items:center;justify-content:center';
  const label = document.createElement('b');
  label.textContent = 'YOU are in control.';
  const msg = document.createElement('span');
  msg.textContent = q ? 'Agent asks: ' + q : 'Do the step in this page.';
  const btn = document.createElement('button');
  btn.textContent = 'Done, hand back to agent';
  btn.style.cssText = 'padding:6px 14px;font-size:14px;cursor:pointer';
  btn.onclick = () => window.__cua_handback();
  b.append(label, msg, btn);
  document.documentElement.appendChild(b);
})();
"""

if "_takeover_ready" not in globals():
    async def _handback():
        if HANDBACK["event"]:
            HANDBACK["event"].set()
    await page.expose_function("__cua_handback", _handback)   # page -> notebook signal
    await page.add_init_script(SYNC_UI_JS)                    # keeps lock/banner correct after every navigation
    # sessionStorage lives in the BROWSER TAB, not the Python kernel: restarting the kernel does
    # NOT clear it, since Playwright's browser process is separate and keeps running. Force-clear
    # any flag left over from an earlier, possibly-interrupted run, so a fresh kernel always starts
    # from a known "not in takeover" state regardless of the tab's history.
    await page.evaluate("() => { sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question'); }")
    await page.evaluate(SYNC_UI_JS)                            # apply to the current page right now (locked by default)
    _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
    print(f"[lock] initial setup done | __cua_lock present on page: {_lock_present} | url={page.url}")
    _takeover_ready = True


async def human_takeover(question: str = "", auto_on_navigate: bool = False, block_risky: bool = True, allow_refs: list[int] | None = None) -> str:
    """Give the live browser to a human. Returns when they click 'Done', OR, if auto_on_navigate
    is set, as soon as the page reloads at all (same url or not -- a form POST-back that
    re-renders the same url still counts).

    allow_refs, when given, is the STRICTEST mode: the general lock stays fully ACTIVE, and only
    these specific elements are poked open (a visible green outline marks them). Everything else
    on the page, including navigation links, stays locked. Used by request_value and
    request_missing_values, which know exactly which field(s) are needed.

    Without allow_refs, the whole page unlocks instead. block_risky=True (the default) then
    ADDITIONALLY blurs and disables every button needs_human (STEP 3) would flag, so a general
    takeover (ask_human) can still not be used to bypass the approval step. The one call site
    that should pass block_risky=False is the take-over-to-submit case in click(), since acting
    on that specific button is the entire point of that one takeover.

    auto_on_navigate=True is for that same approval-step takeover: the human took over
    specifically to click a submit button, so ANY resulting page reload IS the "done" signal.
    """
    HANDBACK["event"] = asyncio.Event()
    visited = []
    print(f"[takeover] started | auto_on_navigate={auto_on_navigate} | block_risky={block_risky} | allow_refs={allow_refs} | url={page.url}")

    def on_nav(frame):
        if frame != page.main_frame:
            return
        visited.append(frame.url)
        print(f"[takeover] framenavigated fired -> {frame.url}")
        if auto_on_navigate and not HANDBACK["event"].is_set():
            HANDBACK["event"].set()
            print("[takeover] auto hand-back triggered")

    page.on("framenavigated", on_nav)
    await page.evaluate("([q]) => { sessionStorage.setItem('cua_takeover', '1'); sessionStorage.setItem('cua_question', q); }", [question])
    if allow_refs is not None:
        await page.evaluate(BANNER_ONLY_JS)     # lock stays active; only these refs are poked open
        await page.evaluate(RESTRICT_JS, allow_refs)
        risky = []
    else:
        await page.evaluate(SYNC_UI_JS)
        risky = [e["ref"] for e in surface.last_elements if e["inViewport"] and needs_human(e["ref"])] if block_risky else []
        if block_risky:
            await page.evaluate(BLOCK_JS, risky)
    _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
    print(f"[lock] takeover open | __cua_lock present={_lock_present} (True only expected in allow_refs mode) | risky refs blocked: {risky}")
    await HANDBACK["event"].wait()
    print(f"[takeover] hand-back received | visited={visited} | url now={page.url}")
    page.remove_listener("framenavigated", on_nav)
    if allow_refs is not None:
        await page.evaluate(UNRESTRICT_JS)
    elif block_risky:
        await page.evaluate(UNBLOCK_JS)
    try:
        await page.evaluate("sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question');")
        await page.evaluate(SYNC_UI_JS)   # re-lock and remove the banner right away (safe in both modes)
        _lock_present = await page.evaluate("() => !!document.getElementById('__cua_lock')")
        print(f"[lock] takeover ended, re-locked | __cua_lock present (should be True): {_lock_present}")
    except Exception as exc:
        print(f"[lock] could not confirm re-lock after hand-back (page likely moved on): {type(exc).__name__}")
    text = (await page.inner_text("body"))[:300].replace("\n", " ")
    return f"Pages the human visited: {visited or 'none'}. Page now: {page.url}. Page text: {text}"


def approval_info(args: dict) -> dict:
    name = surface.name_of(args["ref"])
    fields = "; ".join(f"{k}: {v}" for k, v in TYPED.items()) or "(nothing typed)"
    return {"title": f"Agent wants to click '{name}' on {page.url.split('/')[-1]}", "details": f"Values it entered: {fields}"}

# %% BROWSER 7: STEP 3 (copied verbatim from agent.ipynb)
import asyncio, base64, functools
from langchain.tools import tool
from langchain.agents.middleware import AgentMiddleware, AgentState, Runtime

ACT_LOCK = asyncio.Lock()


def one_at_a_time(fn):
    @functools.wraps(fn)
    async def wrapper(*a, **k):
        async with ACT_LOCK:
            return await fn(*a, **k)
    return wrapper


TYPED: dict[str, str] = {}      # what the agent entered, by field name (shown in the approval bar)
GIVEN = {"text": ""}            # what the user actually gave us; set before each run
RESULT: dict = {}
DENY_LINKS = ("register", "lookup", "admin")
SENSITIVE_WORDS = ("ssn", "password", "social")


async def _unlocked(coro):
    """Run one Playwright action with the general lock (STEP 2) removed for just that instant.
    force=True alone does NOT bypass the lock: Playwright still dispatches the click/fill by
    coordinate ('use page.mouse over the center of the element', per its own docs), so the real
    browser hit-tests normally and the lock overlay -- being on top -- would receive it instead
    of our intended target. Genuinely removing the lock, only for this one action, is what
    actually works."""
    await page.evaluate(UNLOCK_JS)
    try:
        return await coro
    finally:
        await page.evaluate(LOCK_JS)


async def _click(self, ref: int):
    await _unlocked(self.page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000, force=True))
    await self.page.wait_for_timeout(600)
    try:
        await self.page.wait_for_load_state("load", timeout=5000)
    except Exception:
        pass

async def _type_text(self, ref: int, text: str):
    await _unlocked(self.page.locator(f'[data-cua-ref="{ref}"]').fill(text, timeout=5000, force=True))

async def _page_text(self) -> str:
    return (await self.page.inner_text("body"))[:4000]

PlaywrightSurface.click = _click
PlaywrightSurface.type_text = _type_text
PlaywrightSurface.page_text = _page_text
surface = PlaywrightSurface(page)


def _blocks(prefix: str, obs) -> list[dict]:
    """Package text and a screenshot as one tool result the model can read."""
    return [
        {"type": "text", "text": f"{prefix}\n{obs.as_text()}"},
        {"type": "image", "base64": base64.b64encode(obs.png).decode(), "mime_type": "image/png"},
    ]


def _describe(ref: int, hint: str = "") -> str:
    """Best available description of an element: the code's own name, the model's visual
    hint, both together, or a last-resort 'field N' only if neither is available. This is
    what closes the gap between D2 (the model can read a label visually, from the screenshot)
    and a human-facing message (which used to ask only the code, never the model)."""
    name = (surface.name_of(ref) or "").strip()
    hint = (hint or "").strip()
    if name and hint:
        return f"{name} ({hint})"
    return name or hint or f"field {ref}"


START_PAGES = {"overview.htm", "index.htm"}   # start pages: asking a human here is too early. Open the task page first.


def current_page() -> str:
    """Page name from the URL: no query, no ;jsessionid=, no trailing slash, lower case."""
    return page.url.split("?")[0].split(";")[0].rstrip("/").rsplit("/", 1)[-1].lower()


async def current_value(ref: int) -> str:
    """Read whatever is currently in this field, live from the page. Empty string if none or unreadable."""
    try:
        loc = page.locator(f'[data-cua-ref="{ref}"]')
        tag = await loc.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            return (await loc.evaluate("el => el.selectedOptions[0] ? el.selectedOptions[0].text : ''")).strip()
        return (await loc.input_value(timeout=1000)).strip()
    except Exception:
        return ""


async def _ask_for_value(ref: int, field: str, kind: str) -> list:
    """The agent tried to enter a value the user never gave. Hand the browser to a human --
    unless the field already has a value, in which case refuse and say so. This is a code
    guarantee, not something left to the model's memory of what it already asked about."""
    val = await current_value(ref)
    if val:
        return _blocks(
            f"SKIP: '{field}' already has a value ({val!r}). Do not ask about it again; move to a different field.",
            await surface.observe(),
        )
    report = await human_takeover(
        f"I need a value for '{field}' and you did not give me one. Please {kind} it yourself in the page, then click Done.",
        allow_refs=[ref],
    )
    return _blocks(
        f"A human entered the value for '{field}' themselves. Do NOT type it again. {report}",
        await surface.observe(),
    )


@tool(parse_docstring=True)
@one_at_a_time
async def observe() -> list:
    """Look at the current page.

    Returns:
        A screenshot with red numbered boxes, plus a text list of the numbered elements.
    """
    return _blocks("Current page.", await surface.observe())


SAFE_SUBMITS = {"log in", "find transactions"}   # buttons that do not change data
AUTO_LIMIT = None                                # None = always ask a human. Later: 500.0 for small transfers
DECLINED: set[str] = set()                       # buttons a human refused; never clicked again this run


def _amount() -> float:
    raw = TYPED.get("amount", "").replace("$", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return float("inf")                      # unknown amount counts as risky


def needs_human(ref: int) -> bool:
    """Every button except a short safe list needs a human. Links (navigation) run freely."""
    el = next((e for e in surface.last_elements if e["ref"] == ref), None)
    role = (el or {}).get("role")
    name = ((el or {}).get("name") or "").strip().lower()
    risky = bool(el) and (bool(el.get("submit")) or role == "button") and name not in SAFE_SUBMITS
    if risky and "transfer" in name and AUTO_LIMIT is not None and _amount() <= AUTO_LIMIT:
        risky = False
    print(f"approval check -> role={role!r} name={name!r} risky={risky}")
    return risky


LOGIN_ATTEMPTS = {"count": 0}
LOGIN_BLOCKED = {"blocked": False}
# Best-guess wording for ParaBank's own login failure message; not verified against the live
# site in this session. The 3-attempt hard cap below is the guaranteed backstop regardless of
# whether this text matches -- it does not depend on guessing the wording right.
LOGIN_FAILURE_TEXTS = ("could not be verified", "user does not exist", "invalid username or password")
LOGIN_ATTEMPT_LIMIT = 3


def login_check(attempts_so_far: int, page_text_after: str, limit: int = LOGIN_ATTEMPT_LIMIT):
    """Pure decision: after a login click, should further attempts be blocked, and why."""
    attempts = attempts_so_far + 1
    failed_text = next((t for t in LOGIN_FAILURE_TEXTS if t in page_text_after.lower()), None)
    if failed_text:
        return attempts, True, f"the login page reported: '{failed_text}'"
    if attempts >= limit:
        return attempts, True, f"login was attempted {attempts} times with no success"
    return attempts, False, None


@tool(parse_docstring=True)
@one_at_a_time
async def click(ref: int) -> list:
    """Click an element on the page.

    Buttons that change data ask a human for approval first. You do not need to do anything for that.

    Args:
        ref: Number of the element in the latest screenshot and list.

    Returns:
        The new page state. If a human declined, the result says DECLINED and you must stop.
    """
    name = (surface.name_of(ref) or "").strip().lower()
    if any(w in name for w in DENY_LINKS):
        return _blocks(f"DENIED: '{name}' is not allowed.", await surface.observe())
    if name in DECLINED:
        return _blocks("DECLINED earlier by a human. Do not retry. Call finish with 'DECLINED:' and stop.", await surface.observe())
    if name == "log in" and LOGIN_BLOCKED["blocked"]:
        return _blocks("BLOCKED: login already failed or hit its attempt limit. Do not try again. Call finish with a summary starting 'STUCK:' and stop.", await surface.observe())
    if needs_human(ref):
        # The page is already locked (STEP 2) whenever it is not an active takeover, so a
        # human cannot click the real button while this decision is pending -- only our own
        # decision bar (its own higher z-index) is interactive right now.
        choice = await page.evaluate(DECISION_JS, approval_info({"ref": ref}))
        if choice == "r":
            DECLINED.add(name)
            return _blocks("DECLINED by a human. Do not retry or work around it. Call finish with 'DECLINED:' and stop.", await surface.observe())
        if choice == "t":
            report = await human_takeover(question="", auto_on_navigate=True, block_risky=False)   # this IS the approval step; the human may act on the button itself
            return _blocks(f"A human completed this step manually in the browser. {report} Do NOT click again. Check the result from the page text, then call finish.", await surface.observe())
        # choice == "a": approved, fall through. Our own click below uses force=True (STEP 3),
        # so the still-locked page does not stop it.
    try:
        await surface.click(ref)
    except Exception as exc:
        return _blocks(f"CLICK FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    if not host_allowed(page.url):
        await page.go_back()
        return _blocks("BLOCKED: left the allowed site. Went back.", await surface.observe())
    if name == "log in":
        page_text_after = await surface.page_text()
        LOGIN_ATTEMPTS["count"], blocked, reason = login_check(LOGIN_ATTEMPTS["count"], page_text_after)
        if blocked:
            LOGIN_BLOCKED["blocked"] = True
            return _blocks(
                f"STOP: login failed ({reason}). Do not try again. Call finish with a summary starting 'STUCK:' explaining this.",
                await surface.observe(),
            )
    return _blocks(f"Clicked [{ref}].", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def type_text(ref: int, text: str) -> list:
    """Type normal text into an input box.

    Only type values the user gave you in the goal. Never invent a value.

    Args:
        ref: Number of the input box in the latest screenshot and list.
        text: The text to type. It must come from the user's goal.

    Returns:
        The new page state.
    """
    field = _describe(ref)
    if any(w in field.lower() for w in SENSITIVE_WORDS) or text.strip().lower() not in GIVEN["text"].lower():
        return await _ask_for_value(ref, field, "type")
    try:
        await surface.type_text(ref, text)
    except Exception as exc:
        return _blocks(f"TYPE FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    TYPED[field.lower()] = text
    return _blocks(f"Typed into [{ref}].", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def type_secret(ref: int, name: str) -> list:
    """Type a stored secret into an input box, without ever seeing its value.

    Use this to log in. You give only the secret's name.

    Args:
        ref: Number of the input box in the latest screenshot and list.
        name: Secret name. Either 'username' or 'password'.

    Returns:
        The new page state. The value is never included.
    """
    if name not in SECRETS:
        return _blocks(f"UNKNOWN SECRET '{name}'. Use one of: {list(SECRETS)}", await surface.observe())
    if not host_allowed(page.url):
        return _blocks("REFUSED: this site is not on the allowlist.", await surface.observe())
    try:
        await _unlocked(page.locator(f'[data-cua-ref="{ref}"]').fill(resolve_secret(name), timeout=5000, force=True))
    except Exception as exc:
        return _blocks(f"FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    return _blocks(f"Typed secret '{name}' into [{ref}].", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def select_option(ref: int, option: str) -> list:
    """Choose an option in a dropdown.

    Only choose options the user named in the goal. Never guess.

    Args:
        ref: Number of the dropdown in the latest screenshot and list.
        option: Visible text of the option, exactly as shown in its options list.

    Returns:
        The new page state.
    """
    field = _describe(ref)
    if option.strip().lower() not in GIVEN["text"].lower():
        return await _ask_for_value(ref, field, "choose")
    try:
        await _unlocked(page.locator(f'[data-cua-ref="{ref}"]').select_option(label=option, timeout=5000, force=True))
    except Exception as exc:
        return _blocks(f"SELECT FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    TYPED[field.lower()] = option
    return _blocks(f"Selected '{option}' in [{ref}].", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def page_text() -> str:
    """Read the visible text of the whole page (balances, tables, messages).

    Returns:
        The page text, up to 4000 characters.
    """
    return await surface.page_text()


@tool(parse_docstring=True)
@one_at_a_time
async def ask_human(question: str) -> list:
    """Ask a human for help by handing over the browser.

    Use this when you are unsure which element to pick, the page looks unexpected,
    a step failed twice, or you would have to guess. Never guess account choices or amounts.

    Args:
        question: What you are unsure about and what you need the human to do.

    Returns:
        What the human did, and the new page state.
    """
    print(f"guard (ask_human) -> page={current_page()!r} start_page={current_page() in START_PAGES}")
    if current_page() in START_PAGES:
        return _blocks(
            "NOT YET: you are still on the start page. Open the page where this task is done first "
            "(use the menu). Then, with the form on screen, use request_value on each field you cannot fill.",
            await surface.observe(),
        )
    report = await human_takeover(question)
    return _blocks(f"A human took over and handed back. {report}", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def request_value(ref: int, hint: str) -> list:
    """Ask the human to fill one field that you cannot fill, because the user did not give the value.

    Open the page that has the field first. Then point at the field, and say what you see: read
    the label from the screenshot even if the element has no name in the code. This happens on
    older pages where a label sits in a nearby table cell or heading, not attached to the input.
    Your visual reading is what the human sees in the request, so give your best reading even if
    you are not fully sure. The page scrolls to the field, the human types the value there and
    hands control back. Do not type into that field yourself afterwards.

    Args:
        ref: Number of the field (input box or dropdown) in the latest screenshot and list.
        hint: What you see as this field's label or purpose, read from the screenshot.

    Returns:
        The new page state, after the human is done.
    """
    print(f"guard (request_value) -> page={current_page()!r} start_page={current_page() in START_PAGES}")
    if current_page() in START_PAGES:
        return _blocks(
            "NOT YET: you are still on the start page. Open the page that has this form first.",
            await surface.observe(),
        )
    field = _describe(ref, hint)
    try:
        loc = page.locator(f'[data-cua-ref="{ref}"]')
        await loc.scroll_into_view_if_needed(timeout=3000)
        await loc.focus(timeout=3000)
    except Exception:
        pass                                     # the human can still find it; do not fail the request
    return await _ask_for_value(ref, field, "enter")


def missing_field_labels(elements: list[dict], hints: dict[str, str] | None = None) -> list[tuple[int, str]]:
    """Empty, visible, fillable fields, in page order. Pure: no browser, no network call."""
    hints = hints or {}
    out = []
    for e in elements:
        if not e["inViewport"] or e["role"] not in ("textbox", "combobox") or e.get("value"):
            continue
        ref = e["ref"]
        name = (e.get("name") or "").strip()
        hint = hints.get(str(ref), "").strip()
        label = f"{name} ({hint})" if name and hint else (name or hint or f"field {ref}")
        out.append((ref, label))
    return out


@tool(parse_docstring=True)
@one_at_a_time
async def request_missing_values(hints: dict[str, str] = {}) -> list:
    """Ask a human to fill every empty field on the current page in one go.

    Use this once you have typed or chosen every value the user actually gave you, and the
    form still has empty fields left. Call this ONCE for all of them, rather than calling
    request_value field by field. If some fields are still empty after the human clicks Done,
    call this again: only the fields still empty will be shown, not the ones already filled.

    Args:
        hints: Optional. Maps a field's ref number (as text, e.g. "17") to your own reading of
            its label, for fields with no clear name in the code.

    Returns:
        The new page state, after the human is done.
    """
    if current_page() in START_PAGES:
        return _blocks("NOT YET: open the page that has this form first.", await surface.observe())
    missing = missing_field_labels(surface.last_elements, hints)
    if not missing:
        return _blocks("Nothing is missing right now.", await surface.observe())
    labels = [label for _, label in missing]
    question = "Please fill in these fields, then click Done: " + "; ".join(labels)
    report = await human_takeover(question, allow_refs=[ref for ref, _ in missing])
    return _blocks(f"A human filled in what they chose to. {report}", await surface.observe())


@tool(parse_docstring=True)
async def finish(summary: str, values: dict[str, str]) -> str:
    """Report the final result and stop.

    If you cannot make progress, start the summary with 'STUCK:'. If a human declined, start it with 'DECLINED:'.

    Args:
        summary: One-line summary of what you did or why you stopped.
        values: The requested facts, for example {"account_id": "13344", "balance": "$100.00"}.

    Returns:
        A confirmation. Stop after this.
    """
    RESULT.clear()
    RESULT.update({"summary": summary, "values": values})
    return "Recorded. Stop now."


BROWSER_TOOLS = [observe, click, type_text, type_secret, select_option, page_text, request_value, request_missing_values, ask_human, finish]
print("tools ready:", [t.name for t in BROWSER_TOOLS])

# %% [markdown]
# ### Additive cells below (new, capture-only, never touching a tool's body copied above)
# `DESCRIBE_JS`/`HEADING_JS`/`READ_LABELED_JS` give the recorder richer facts than the model ever
# sees (label, container, nth, name/label duplicate counts, a page heading) -- computed only when
# logging an event, from the same `data-cua-ref` attributes `OBSERVE_JS` already sets. `nameOf`/
# `roleOf`/`labelOf` inside `DESCRIBE_JS` intentionally mirror agent.ipynb's own `OBSERVE_JS`
# logic (small, documented duplication) so "name" means the same thing to the recorder as it does
# to the model.

# %% BROWSER 8: descriptor, heading, and labeled-value JS (new, additive)
HEADING_JS = """
() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const pick = (q) => Array.from(document.querySelectorAll(q)).find(vis);
  const el = pick('h1') || pick('.title') || pick('h2');
  return ((el && el.innerText) || document.title || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
}
"""

# The value shown next to a label: the cell after it, the input a <label> points at, or the next
# sibling. `matches` (how many elements on the page carry this exact label text) is D68's
# duplicate-label signal for extract steps.
READ_LABELED_JS = """
(label) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const bare = (s) => norm(s).replace(/:$/, '').toLowerCase();
  const want = bare(label);
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const all = Array.from(document.body.querySelectorAll('td, th, dt, label, b, strong, span, div, p, li')).filter(vis);
  const hits = all.filter(e => bare(e.innerText || e.textContent) === want &&
                               !Array.from(e.children).some(c => bare(c.innerText || c.textContent) === want));
  const valueOf = (el) => {
    const cell = el.closest('td, th, dt');
    if (cell && cell.nextElementSibling) return norm(cell.nextElementSibling.innerText);
    if (el.tagName === 'LABEL' && el.htmlFor) { const t = document.getElementById(el.htmlFor); if (t) return norm(t.value || t.innerText); }
    if (el.nextElementSibling) return norm(el.nextElementSibling.innerText);
    let n = el.nextSibling;
    while (n) { const t = norm(n.textContent); if (t) return t; n = n.nextSibling; }
    return '';
  };
  for (const h of hits) { const v = valueOf(h); if (v) return { value: v, matches: hits.length }; }
  return { value: '', matches: hits.length };
}
"""

# One element's RICH descriptor (role, name, name_source, label, container, nth, and duplicate
# counts). Never shown to the model -- only used to build a capture event. Deliberately mirrors
# agent.ipynb's OWN roleOf/nameOf (Setup 4/4) so 'name' means the same thing here as it does to
# the model; labelOf/containerOf are new (the model never sees them; they exist only so the
# recorder can produce a `label` or `structure` locator, D42).
DESCRIBE_JS = """
(ref) => {
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const roleOf = (el) => {
    const r = el.getAttribute('role'); if (r) return r;
    const t = el.tagName.toLowerCase();
    if (t === 'a') return 'link';
    if (t === 'button') return 'button';
    if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') {
      const ty = (el.getAttribute('type') || 'text').toLowerCase();
      if (['submit', 'button', 'reset', 'image'].includes(ty)) return 'button';
      if (ty === 'checkbox') return 'checkbox';
      if (ty === 'radio') return 'radio';
      return 'textbox';
    }
    return 'generic';
  };
  const nameInfo = (el) => {
    const aria = norm(el.getAttribute('aria-label')); if (aria) return [aria, 'aria'];
    if (el.labels && el.labels.length) { const t = norm(el.labels[0].innerText); if (t) return [t, 'label']; }
    const t = el.tagName.toLowerCase(), ty = (el.getAttribute('type') || '').toLowerCase();
    if (t === 'input' && ['submit', 'button', 'reset'].includes(ty)) { const v = norm(el.value); if (v) return [v, 'value']; }
    const txt = norm(el.innerText).slice(0, 80); if (txt) return [txt, 'text'];
    for (const a of ['placeholder', 'title', 'alt']) { const v = norm(el.getAttribute(a)); if (v) return [v, 'attr_acc']; }
    const nm = el.getAttribute('name') || el.id; if (nm) return [nm, 'attr'];
    return ['', 'none'];
  };
  const formCtl = (el) => ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
  const labelOf = (el, role) => {
    if (!formCtl(el) || role === 'button') return '';
    if (el.labels && el.labels.length) return norm(el.labels[0].innerText).slice(0, 60);
    const cell = el.closest('td, th, dd');
    const prev = cell && cell.previousElementSibling;
    return prev ? norm(prev.innerText).slice(0, 60) : '';
  };
  const containerOf = (el) => {
    const form = el.closest('form, [role=form]');
    const tbl = el.closest('table, [role=table], [role=grid]');
    const c = formCtl(el) || el.tagName === 'BUTTON' ? (form || tbl) : (tbl || form);
    if (!c) return [null, null];
    const isForm = c === form;
    let name = norm(c.getAttribute('aria-label'));
    if (!name && !isForm) { const cap = c.querySelector('caption'); if (cap) name = norm(cap.innerText); }
    if (!name && isForm) { const lg = c.querySelector('legend'); if (lg) name = norm(lg.innerText); }
    const tag = el.tagName.toLowerCase();
    const nth = Array.from(c.querySelectorAll(tag)).indexOf(el) + 1;
    return [{ role: isForm ? 'form' : 'table', name: name || null }, nth || null];
  };
  const all = Array.from(document.querySelectorAll('[data-cua-ref]'));
  const target = all.find(el => el.getAttribute('data-cua-ref') === String(ref));
  if (!target) return null;
  const role = roleOf(target), ni = nameInfo(target), label = labelOf(target, role);
  const name = ni[0], name_source = ni[1];
  const nameCount = name ? all.filter(el => roleOf(el) === role && nameInfo(el)[0] === name).length : 1;
  const labelCount = label ? all.filter(el => labelOf(el, roleOf(el)) === label).length : 1;
  const cn = containerOf(target);
  return {
    role, name, name_source, label: label || null,
    text: (!formCtl(target) ? (norm(target.innerText).slice(0, 80) || null) : null),
    tag: target.tagName.toLowerCase(), type: (target.getAttribute('type') || '').toLowerCase() || null,
    submit: (target.tagName === 'BUTTON' && target.type !== 'button') ||
            (target.tagName === 'INPUT' && ['submit', 'image'].includes((target.getAttribute('type') || '').toLowerCase())),
    options: target.tagName === 'SELECT' ? Array.from(target.options).map(o => o.text.trim()).slice(0, 15) : null,
    container: cn[0], nth: cn[1], name_count: nameCount || 1, label_count: labelCount || 1,
  };
}
"""


async def current_heading() -> str:
    try:
        return await page.evaluate(HEADING_JS)
    except Exception:
        return ""


async def describe_ref(ref: int) -> dict | None:
    try:
        return await page.evaluate(DESCRIBE_JS, ref)
    except Exception:
        return None


async def read_labeled_value(page, label: str) -> str:
    """The value shown next to `label` on the current page. Raises LookupError if there is none.
    Written to be reused by Phase 4 replay, so record and replay read values the same way (D46)."""
    res = await page.evaluate(READ_LABELED_JS, label)
    if not res["value"]:
        raise LookupError(f"no value found next to the label {label!r}")
    return res["value"]


print("descriptor/heading/labeled-value helpers ready")

# %% BROWSER 9: three new tools the compiler needs (extract_value, open_path, finish_business_outcome)
from urllib.parse import parse_qsl


@tool(parse_docstring=True)
@one_at_a_time
async def extract_value(label: str, save_as: str, value_type: str, description: str) -> list:
    """Read a value shown next to a label on the page (e.g. 'Balance:') and record it as an output.

    Use this instead of page_text when the task needs to save one specific value by name.

    Args:
        label: The exact label text as shown on the page, e.g. 'Balance:'.
        save_as: A short lower_snake_case name for this value, e.g. 'balance'.
        value_type: One of string, integer, number, currency, boolean.
        description: One sentence describing what this value is.

    Returns:
        The new page state.
    """
    res = await page.evaluate(READ_LABELED_JS, label)
    if not res["value"]:
        return _blocks(f"FAILED to read '{label}': no value found next to that label.", await surface.observe())
    if not value_matches_type(res["value"], value_type):
        return _blocks(f"FAILED to read '{label}': the value does not look like a {value_type}.", await surface.observe())
    return _blocks(f"Read '{label}'.", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def open_path(path: str) -> list:
    """Navigate directly to a page on this site by its path, when no link on the page goes there.

    Only use this for a path whose query values come from the user's goal. Never invent a value.

    Args:
        path: A path starting with '/', e.g. '/activity.htm?id=13344'. Every value in it must
            come from the goal.

    Returns:
        The new page state.
    """
    if any(w in path.lower() for w in DENY_LINKS):
        return _blocks(f"DENIED: '{path}' is not allowed.", await surface.observe())
    values = [v for _, v in parse_qsl(urlparse(path).query)]
    if any(v.strip().lower() not in GIVEN["text"].lower() for v in values):
        return _blocks(
            f"REFUSED: '{path}' has a value not given in the goal. Only open a path whose values you were given.",
            await surface.observe(),
        )
    url = f"{BASE}{path}"
    if not host_allowed(url):
        return _blocks("REFUSED: this path is not on the allowed site.", await surface.observe())
    try:
        await page.goto(url)
    except Exception as exc:
        return _blocks(f"FAILED to open '{path}': {type(exc).__name__}", await surface.observe())
    return _blocks(f"Opened {path}.", await surface.observe())


@tool(parse_docstring=True)
async def finish_business_outcome(outcome: str, proof_text: str) -> str:
    """Report that this run hit a known business outcome (e.g. a bad account id), not a normal
    task result. Only call this INSTEAD of finish() when the page shows a message that proves a
    declared bad-input scenario, such as 'could not find account'.

    Args:
        outcome: Short UPPER_SNAKE name for what happened, e.g. ACCOUNT_NOT_FOUND.
        proof_text: The exact sentence from the page that proves this outcome. Copy it exactly
            from the page text.

    Returns:
        A confirmation, or a refusal if proof_text is not really on the page. Stop after this.
    """
    text = await surface.page_text()
    if proof_text not in text:
        return "REFUSED: that exact text was not found on the current page. Re-read the page and copy it exactly."
    RESULT.clear()
    RESULT.update({"summary": f"PROBE: {outcome}", "values": {}, "outcome": outcome, "proof_text": proof_text})
    return "Recorded as a business-outcome probe. Stop now."


print("new tools ready:", [t.name for t in (extract_value, open_path, finish_business_outcome)])

# %% BROWSER 10: event capture wrapper (new, additive -- wraps .coroutine, never a tool's own body)
EVENTS: list[dict] = []   # the recording. One dict per REAL tool call. No secret VALUES, no extracted values.


def _first_line(result) -> str:
    """The tool's own status text: the first text block of a list result, or the plain string a
    str-returning tool (page_text, finish, finish_business_outcome) gives back directly."""
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"].split("\n", 1)[0]
        return ""
    return str(result).split("\n", 1)[0]


def _capture(tool_obj, *, value_of=lambda kwargs: None) -> None:
    """Replace tool_obj.coroutine with a wrapper that logs an event AROUND the ORIGINAL call --
    calls it unchanged, returns its result unchanged. This is the whole mechanism: nothing about
    click()'s approval gate, the lock, or the login guard (all copied verbatim above) is touched."""
    original = tool_obj.coroutine

    async def wrapped(**kwargs):
        before_url, before_heading = page.url, await current_heading()
        ref = kwargs.get("ref")
        el = await describe_ref(ref) if ref is not None else None
        was_risky = needs_human(ref) if (ref is not None and tool_obj.name == "click") else False
        result = await original(**kwargs)
        message = _first_line(result)
        status = classify_status(message)
        EVENTS.append({
            "i": len(EVENTS), "tool": tool_obj.name, "args": dict(kwargs),
            "message": message, "status": status,
            "before": {"url": norm_url(before_url), "heading": before_heading},
            "after": {"url": norm_url(page.url), "heading": await current_heading()},
            "approved": bool(was_risky and status == "ok"),
            "el": el, "value": value_of(kwargs),
        })
        return result

    tool_obj.coroutine = wrapped


_VALUE_OF = {
    "type_text": lambda kw: kw.get("text"),
    "type_secret": lambda kw: kw.get("name"),       # the secret NAME, never its value
    "select_option": lambda kw: kw.get("option"),
}
for _t in (*BROWSER_TOOLS, open_path):
    if _t.name == "finish":
        continue   # finish gets its own wrapper below (captures summary/values, not a page action)
    _capture(_t, value_of=_VALUE_OF.get(_t.name, lambda kw: None))


_extract_value_original = extract_value.coroutine


async def _extract_value_wrapped(label: str, save_as: str, value_type: str, description: str):
    before_url, before_heading = page.url, await current_heading()
    res = await page.evaluate(READ_LABELED_JS, label)   # only for label_count -- the VALUE itself is never logged (D46/D16)
    result = await _extract_value_original(label=label, save_as=save_as, value_type=value_type, description=description)
    message = _first_line(result)
    EVENTS.append({
        "i": len(EVENTS), "tool": "extract_value", "args": {"label": label, "save_as": save_as, "value_type": value_type},
        "message": message, "status": classify_status(message),
        "before": {"url": norm_url(before_url), "heading": before_heading},
        "after": {"url": norm_url(page.url), "heading": await current_heading()},
        "approved": False, "el": None,
        "label": label, "save_as": save_as, "value_type": value_type, "description": description,
        "label_count": res.get("matches", 1),
    })
    return result


extract_value.coroutine = _extract_value_wrapped

_finish_original = finish.coroutine


async def _finish_wrapped(summary: str, values: dict[str, str]):
    result = await _finish_original(summary=summary, values=values)
    EVENTS.append({
        "i": len(EVENTS), "tool": "finish", "args": {}, "message": result, "status": classify_status(result),
        "before": {"url": norm_url(page.url), "heading": ""}, "after": {"url": norm_url(page.url), "heading": ""},
        "approved": False, "el": None, "summary": summary, "values": values,
    })
    return result


finish.coroutine = _finish_wrapped

_probe_original = finish_business_outcome.coroutine


async def _probe_wrapped(outcome: str, proof_text: str):
    before_url, before_heading = page.url, await current_heading()
    result = await _probe_original(outcome=outcome, proof_text=proof_text)
    status = "ok" if result.startswith("Recorded") else "failed"
    EVENTS.append({
        "i": len(EVENTS), "tool": "finish_business_outcome", "args": {},
        "message": result, "status": status,
        "before": {"url": norm_url(before_url), "heading": before_heading},
        "after": {"url": norm_url(page.url), "heading": await current_heading()},
        "approved": False, "el": None,
        "outcome": outcome if status == "ok" else None,
        "proof": proof_text if status == "ok" else None,
    })
    return result


finish_business_outcome.coroutine = _probe_wrapped

ALL_TOOLS = [*BROWSER_TOOLS, extract_value, open_path, finish_business_outcome]
print("capture ready:", [t.name for t in ALL_TOOLS])

# %% BROWSER 11: STEP 3d equivalent (TypeSafe tool-selection middleware, copied verbatim from
# agent.ipynb; uses the job mapping from OFFLINE 13b above, D76-extended). Off by default.
class TypeSafeToolRouterMiddleware(AgentMiddleware):
    """Classifies the step's job with TypeSafe's Choice primitive and narrows the tool
    list to it. Sends the current page path and the last tool result's text to
    api.typesafe.ai (D50/D52 caveat: never enable on a run that may show real account
    data). Any error here (network, auth, timeout) fails OPEN: the request goes through
    unmodified."""

    def __init__(self, classifier):
        self.classifier = classifier

    async def awrap_model_call(self, request, handler):
        try:
            state = f"page={current_page()!r}. last result: {str(request.messages[-1].content)[:400]!r}"
            response = await self.classifier.ainvoke(
                {"state": state, "questions": {"job": Choice(instructions="What kind of step is this?", criteria=JOB_CRITERIA)}}
            )
            answer = response.choices["job"]
            named = {t.name for t in request.tools if hasattr(t, "name")}
            keep = confidence_gate(named, answer.choice, answer.confidence)
            request = request.override(tools=[t for t in request.tools if not hasattr(t, "name") or t.name in keep])
            print(f"typesafe job -> {answer.choice!r} confidence={answer.confidence:.2f} kept={sorted(keep)}")
        except Exception as exc:
            print(f"typesafe job router FAILED, continuing with no change: {type(exc).__name__}: {exc}")
        return await handler(request)


print("TypeSafe tool router middleware ready (activates only if TYPESAFE_API_KEY is set below)")

# %% BROWSER 12: system prompt and agent, with TypeSafe wired in exactly as agent.ipynb's STEP 4
# does (model router + tool router, both gated by TYPESAFE_API_KEY; off by default)
from langgraph.checkpoint.memory import MemorySaver

# Same numbered rules as agent.ipynb's SYSTEM_PROMPT (STEP 4), items 1-9 unchanged verbatim,
# minus the web_search sentence (D48: not included in this notebook's tool list) and with three
# new tool lines documented (extract_value, open_path, finish_business_outcome).
RECORDER_SYSTEM_PROMPT = """You are an expert browser operator. You drive a real browser on a banking demo site.

## Browser tools
Every tool result shows a screenshot with red numbered boxes plus a list of numbered elements. A field already filled shows its current value, e.g. [7] textbox "City" = '2'. Never ask about a field that already shows a value; move to one that does not. Dropdowns list their options. Refer to elements only by number. Numbers change after every action, so use the latest list.
- observe: look at the page.
- click(ref), type_text(ref, text), select_option(ref, option): act on elements.
- type_secret(ref, name): type a stored secret ('username' or 'password'). You never see the value.
- page_text: read the visible page text (balances, messages).
- extract_value(label, save_as, value_type, description): read one specific value shown next to a label (e.g. 'Balance:') and record it as an output. Use this, not page_text, when the task asks you to report a specific value by name.
- open_path(path): go directly to a page on this site by its path, when no link on the page goes there. Every value in the path must come from the goal.
- finish_business_outcome(outcome, proof_text): call this INSTEAD of finish when the page shows a message proving a bad-input outcome the goal asked you to find (e.g. an account that does not exist). proof_text must be copied exactly from the page.
- request_value(ref, hint): ONE field you cannot fill. Prefer request_missing_values instead when several fields are empty.
- request_missing_values(hints): every empty field on the current page, asked in ONE go, not one at a time. hints maps a ref number to your own label reading, for fields with no name in the code.
- ask_human(question): only when you are unsure what to click. Not for missing values.
- finish(summary, values): report the result, logout and then stop.

## How to work
1. Call observe first. If you see a login form, log in with type_secret, then confirm the account overview appears.
2. Do the task by the shortest path. Read values with page_text and copy them exactly. Never invent a value.
3. Use ONLY values the user gave you in the goal. Never make one up. If values you need (payee, amount, account, address) are missing: FIRST open the page where the task is done (use the menu links), THEN call request_missing_values ONCE to ask for everything still empty at the same time. Never ask a human while you are still on the start page.
4. If a tool says a human entered a value, do not type it again. Continue with the next step.
5. Buttons that change data (Send Payment, Transfer, Open New Account, and so on) need a human. Click the button when the form is ready; the system asks the human for approval by itself. If the result says DECLINED, never retry or work around it: call finish with 'DECLINED:'.
6. Make ONE tool call at a time. Do not click into a field before typing.
7. Stay on the banking site. If you are lost or repeat the same action 3 times, call finish with 'STUCK:' and say why.
8. Attempt login at most 3 times. If the page says the login could not be verified, stop immediately -- do not retry. Call finish with a summary starting 'STUCK:' explaining what happened.
9. Do not use ls, read_file, write_file, edit_file, delete, glob, grep or task.
"""

# Optional: route each step to Haiku or Sonnet, and narrow tools by job, via TypeSafe (a
# third-party classifier service). Off by default. Turns on only if TYPESAFE_API_KEY is set in
# .env (get one at typesafe.ai). Copied verbatim from agent.ipynb's STEP 4 -- same trade-off,
# same decision (D50): step text and page state are sent to api.typesafe.ai on every step this is
# on. Never enable this for a run that may show real account data.
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
HAIKU_MODEL = "anthropic:claude-haiku-4-5-20251001"
SONNET_MODEL = "anthropic:claude-sonnet-5"

recorder_middleware = []   # no key: no TypeSafe layer at all, same as agent.ipynb with no key set
if TYPESAFE_API_KEY:
    from langchain_typesafe import Choice, TypeSafeClassifier
    from langchain_typesafe.experimental.middleware import ModelChoice, ModelRouterMiddleware

    recorder_router = ModelRouterMiddleware(
        choices={
            "fast": ModelChoice(
                model=HAIKU_MODEL,
                criteria="A single simple step: reading the page, or one obvious click, type, or select with no ambiguity.",
            ),
            "powerful": ModelChoice(
                model=SONNET_MODEL,
                criteria="Anything else: planning, choosing between several similar elements, forms, or any step before a risky click.",
            ),
        },
        instructions="Pick the cheapest model that can do the step correctly. If unsure, pick 'powerful'.",
    )
    recorder_middleware = [TypeSafeToolRouterMiddleware(TypeSafeClassifier()), recorder_router]
    print(f"model router ON (TypeSafe): fast={HAIKU_MODEL} | powerful={SONNET_MODEL}")
else:
    print("model router OFF: no TYPESAFE_API_KEY in .env. Using MODEL only:", MODEL)

recorder_agent = create_deep_agent(
    model=MODEL,
    tools=ALL_TOOLS,
    system_prompt=RECORDER_SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
    middleware=recorder_middleware,
)
print("agent ready (capture) | tools:", [t.name for t in ALL_TOOLS])

# %% BROWSER 13: your test values and the run helper
import uuid


async def run_capture(goal: str) -> None:
    """Clear the event log and TYPED state, run the agent on one goal, print the result and the
    captured events. Does not compile or save anything -- that is BROWSER 14."""
    EVENTS.clear()
    TYPED.clear()
    GIVEN["text"] = goal
    cfg = {"configurable": {"thread_id": f"rec-{uuid.uuid4().hex[:6]}"}, "recursion_limit": 100}
    out = await recorder_agent.ainvoke({"messages": [{"role": "user", "content": goal}]}, config=cfg)
    print("AGENT SAID:", out["messages"][-1].content)
    print(f"captured {len(EVENTS)} events")
    for e in EVENTS:
        print(f"  [{e['i']}] {e['tool']:22s} status={e['status']:8s} {e['before']['url']} -> {e['after']['url']}")


ACCOUNT_ID = "CHANGE_ME"       # <-- an account you own
BAD_ACCOUNT_ID = "CHANGE_ME"   # <-- an account id that does NOT exist
print("ready. account:", ACCOUNT_ID, "| bad account:", BAD_ACCOUNT_ID)

# %% BROWSER 14: RUN 1, good balance flow (starting logged out -- this records the login too)
GOAL_BALANCE = f"Log in and read the balance of account {ACCOUNT_ID}. Use extract_value to save it as 'balance'."
await run_capture(GOAL_BALANCE)
BALANCE_EVENTS = list(EVENTS)

# %% BROWSER 15: RUN 2, bad-input probe (needs run 1's login still active)
GOAL_PROBE = (
    f"Open account {BAD_ACCOUNT_ID}. If the page says the account could not be found, call "
    "finish_business_outcome with outcome='ACCOUNT_NOT_FOUND' and proof_text copied exactly from the page."
)
await run_capture(GOAL_PROBE)
PROBE_EVENTS = list(EVENTS)

# %% BROWSER 16: compile RUN 1 (+ the outcome rule from RUN 2), show it, then save
probe_rule = rule_from_probe(PROBE_EVENTS, {"account_id": BAD_ACCOUNT_ID})
print("RULE the recorder made:", probe_rule.outcome, "| when the page shows:", repr(probe_rule.when.text_present))

balance_spec = {
    "name": "get_account_balance",
    "description": "Read the current balance of one account, given its account id.",
    "inputs": {"account_id": {"value": ACCOUNT_ID, "type": "string", "description": "The account number.", "pattern": r"^[0-9]{4,10}$"}},
}
result = compile_run(BALANCE_EVENTS, balance_spec, extra_rules=[probe_rule])
show(result)
if result["login"]:
    print("saved:", save_capability(result["login"]))
print("saved:", save_capability(result["task"]))

# %% BROWSER 17: RUN 3 (optional). Transfer. A human must click Approve in the browser
FROM_ACCOUNT = "CHANGE_ME"
TO_ACCOUNT = "CHANGE_ME"
AMOUNT = "20.00"
GOAL_TRANSFER = f"Transfer {AMOUNT} from account {FROM_ACCOUNT} to account {TO_ACCOUNT}."
await run_capture(GOAL_TRANSFER)
TRANSFER_EVENTS = list(EVENTS)

transfer_spec = {
    "name": "transfer_funds",
    "description": "Move a stated amount from one account to another.",
    "inputs": {
        "from_account": {"value": FROM_ACCOUNT, "type": "string", "description": "Account to take the money from.", "pattern": r"^[0-9]{4,10}$"},
        "to_account": {"value": TO_ACCOUNT, "type": "string", "description": "Account to put the money in.", "pattern": r"^[0-9]{4,10}$"},
        "amount": {"value": AMOUNT, "type": "currency", "description": "Amount to move.", "pattern": r"^\$?[0-9]+(\.[0-9]{2})?$"},
    },
}
transfer_result = compile_run(TRANSFER_EVENTS, transfer_spec)
show(transfer_result)
print("saved:", save_capability(transfer_result["task"]))
