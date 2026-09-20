# %% [markdown]
# # Phase 3: the recorder
# A real agent run becomes a **draft capability** (YAML). The model discovers. The recorder writes it down.
# - **Part A, CAPTURE** (browser): every tool call is logged with a description of the element it touched.
# - **Part B, COMPILE** (pure Python): events + declared inputs -> `login_parabank.yaml` and `get_account_balance.yaml`.
#
# ## How to test this (the exact cells, in order)
# Before you start: `.env` has the API key and the ParaBank test user. Kernel = this repo's `.venv`. ParaBank is up.
#
# | Step | Run cells | What you should see (exact lines) |
# |---|---|---|
# | 1. Offline tests | `OFFLINE 1` to `OFFLINE 15` | last line: `ALL OFFLINE CHECKS PASSED` |
# | 2. Browser setup | `BROWSER 1` to `BROWSER 8` | `model: anthropic:claude-sonnet-5 \| base: https://parabank.parasoft.com/parabank`, then `opened: https://parabank.parasoft.com/parabank/index.htm`, then `scanner ready`, `takeover ready`, `capture ready`, `tools ready: ['observe', 'click', 'type_text', 'type_secret', 'select_option', 'extract_value', 'open_path', 'page_text', 'request_value', 'ask_human', 'finish']`, then `agent ready \| approval is enforced inside the click tool` |
# | 3. Your values | `BROWSER 9`: first edit `ACCOUNT_ID` (an account you own) and `BAD_ACCOUNT` (one that does not exist) | `ready. accounts: <yours> \| bad: <yours>` |
# | 4. Run 1, good balance | `BROWSER 10` | agent logs in and reads the balance. Then `AGENT SAID: ...` and `RECORDED: N events -> .../notebooks/scratch/events_balance.json`, then a table of events. You should see `type_secret` twice, `click` (Log In, page goes to `/overview.htm`), `click` (the account link, page goes to `/activity.htm?id=...`), `extract_value`, `finish` |
# | 5. Run 2, bad input | `BROWSER 11` | `RULE the recorder made: ACCOUNT_NOT_FOUND \| when the page shows: '<some sentence>'`. **Read that sentence.** If it is a generic "internal error" text, tell me: it is too vague for a business rule |
# | 6. Compile and save | `BROWSER 12` | two YAML blocks (`----- login: login_parabank -----`, `----- task: get_account_balance -----`), then `----- report -----` with `dropped:` lines, `constants ...: none`, `warnings: none`, then `saved: artifacts/login_parabank.yaml` and `saved: artifacts/get_account_balance.yaml` |
# | 7. Optional, risky flow | `BROWSER 13` | the browser shows a dark bar "Agent wants to click 'Transfer'". Click **Approve**. Then a YAML with `risk: risky` and `amount_input: amount`, and `saved: artifacts/transfer_funds.yaml`. Moves a tiny fake amount |
#
# **Send me back:** (1) the output of step 1 last line, (2) the event tables from steps 4 and 5, (3) the RULE line, (4) the two saved YAML files (or paste them),
# (5) the `----- report -----` block, (6) any red error, exactly as shown. Do not paste `.env` or anything you typed as a secret.
#
# Notes: run 1 clears the browser cookies first, so the login is part of the recording. Run 2 needs run 1's login to still be active.
# Cell titles start with `OFFLINE` (no browser needed) or `BROWSER` (needs browser + API key).

# %% OFFLINE 1: config and Phase 2 models
# Pure Python. No browser, no network, no API key.
# The Phase 2 models are NOT copied. We run the model cells of 02_artifact_schema.py in this namespace.
import json
import pathlib
import re
import tempfile
from urllib.parse import parse_qsl, urlparse

# ParaBank values live in config only (CLAUDE.md). Nothing below this cell knows about ParaBank.
BASE = "https://parabank.parasoft.com/parabank"
ALLOWED_HOSTS = {"parabank.parasoft.com"}
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}   # name -> env var. Names only.
APP = {"id": "parabank", "base_url": BASE, "vendor": "Parasoft"}
SESSION_EXPIRED_TEXT = "Customer Login"       # text of the login page, used for the relogin rule
START_PAGES = {"overview.htm", "index.htm"}   # pages where asking a human is too early


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
    """Run the model cells of the Phase 2 notebook in this namespace. The check cells are skipped."""
    text = (REPO / "notebooks" / "02_artifact_schema.py").read_text()
    for cell in re.split(r"(?m)^# %%", text)[1:]:
        header, _, body = cell.partition("\n")
        if header.strip().startswith(wanted):
            exec(compile(body, f"02_artifact_schema.py [{header.strip()}]", "exec"), globals())


load_schema()
print("schema loaded:", Capability.__name__, "| repo:", REPO.name)

# %% [markdown]
# ## Part B. COMPILE (pure Python)
# Events in, capability out. An **event** is one tool call the agent made, with a description of the element it touched.
# ```
# {i, tool, status, before:{url, heading}, after:{url, heading}, el, value, approved, label, save_as,
#  value_type, description, path, outcome, proof}
# ```

# %% OFFLINE 2: small helpers (urls, literals)
class CompileError(Exception):
    """The recording cannot become a valid capability. `.problems` lists every reason."""

    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("; ".join(self.problems))


def norm_url(url: str, base: str = BASE) -> str:
    """Relative path + query. Drops the host, the base path, ;jsessionid=... and the fragment.
    Session ids never reach an event."""
    if not url or url == "about:blank":
        return url or ""
    u, b = urlparse(url), urlparse(base)
    path = re.sub(r";[^?#/]*", "", u.path)
    if u.hostname == b.hostname and path.startswith(b.path):
        path = path[len(b.path):] or "/"
    elif u.hostname != b.hostname:
        return f"{u.scheme}://{u.hostname}{path}"          # off-site: keep the host so the compile refuses it
    return path + (f"?{u.query}" if u.query else "")


def path_only(url: str) -> str:
    return url.split("?")[0]


def _literal_re(lit: str):
    """The literal, but not inside a longer word or number: '5' is not found in '$50' or '1.5', 'id' not in 'account_id'."""
    return re.compile(r"(?<![A-Za-z0-9_])(?<!\d[.,])" + re.escape(lit) + r"(?![A-Za-z0-9_])(?![.,]\d)")


def contains_literal(text: str, lit: str) -> bool:
    return bool(lit) and bool(_literal_re(lit).search(text or ""))


def substitute(text: str, inputs: dict[str, str]) -> str:
    """Replace declared literals with {{name}}. Longest literal first."""
    for name, lit in sorted(inputs.items(), key=lambda kv: -len(kv[1])):
        text = _literal_re(lit).sub(lambda _m, n=name: "{{" + n + "}}", text)
    return text


def _canon(s: str) -> str:
    s = s.strip().lower().replace("$", "").replace(",", "")
    if re.fullmatch(r"-?[1-9]\d*(\.\d+)?|-?0(\.\d+)?", s):
        return f"{float(s):.2f}"                # $20.00 == 20 == 20.0. Ids with a leading zero stay text.
    return s


def same_value(a: str, b: str) -> bool:
    return _canon(a) == _canon(b)


# %% OFFLINE 3: locator derivation (D8)
ACCESSIBLE = {"aria", "label", "value", "text", "attr_acc"}   # name sources a role locator can really match


def derive_target(desc: dict, inputs: dict[str, str]) -> "Target":
    """Descriptor -> ranked Target. role+name (high) > label, text (medium) > structure inside a container (low).
    data-cua-ref is never used. A page-wide index is never produced."""
    t = lambda s: substitute(s, inputs) if s else s
    name, label, text = t(desc.get("name")), t(desc.get("label")), t(desc.get("text"))
    locs: list = []
    if name and desc.get("name_source") in ACCESSIBLE and desc.get("role") not in (None, "generic"):
        locs.append(RoleLocator(role=desc["role"], name=name))
    if label:
        locs.append(LabelLocator(label=label))
    if text and text != label:
        locs.append(TextLocator(text=text))
    c = desc.get("container")
    # A position inside a table means "the first account", not "account 14232". If the identity of the element
    # comes from an input, a positional fallback would silently hit the WRONG record. So: no structure locator.
    data_dependent = any("{{" in (s or "") for s in (name, label, text))
    if c and desc.get("nth") and desc.get("tag") and not data_dependent:
        within = Within(role=c["role"], name=t(c.get("name")))
        locs.append(StructureLocator(tag=desc["tag"], within=within, nth=desc["nth"],
                                     note=f"nth <{desc['tag']}> in the container, counting all of that tag"))
    if not locs:
        raise CompileError(f"cannot identify element {desc.get('role')!r} {desc.get('name')!r}: no role name, label, text or container")
    return Target(locators=locs)


# %% OFFLINE 4: clean-up (D23)
ACTION_TOOLS = {"click", "type_text", "type_secret", "select_option", "extract_value", "open_path"}
NAV_TOOLS = {"click", "open_path"}
STATE_TOOLS = {"type_text", "type_secret", "select_option", "extract_value"}


def _key(e: dict):
    el = e.get("el") or {}
    c = el.get("container") or {}
    return (e["tool"], el.get("role"), el.get("name"), el.get("tag"), c.get("role"), el.get("nth"),
            e.get("value"), e.get("label"), e.get("path"))


def clean_events(events: list[dict]):
    """Keep only actions that worked and mattered. Returns (kept, dropped). dropped = [(i, tool, reason)]."""
    dropped, kept = [], []
    for e in events:
        if e.get("status") == "handoff":
            raise CompileError(f"event {e['i']} ({e['tool']}): a human entered something by hand. That step cannot be recorded. "
                               "Put every value in the goal as a declared input and run again.")
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
    """A click that changed the page, then a later click that returned to the page it left, with nothing typed,
    chosen or read in between: both are a dead end. Remove them."""
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
    # A submit button (Find Transactions) is the point of the run even when a human did not have to approve it.
    return e["tool"] in STATE_TOOLS or bool(e.get("approved")) or bool((e.get("el") or {}).get("submit"))


def trim_tail(task: list[dict], dropped: list):
    """Link clicks after the last meaningful action changed nothing that the capability needs."""
    last = max((n for n, e in enumerate(task) if _meaningful(e)), default=None)
    if last is None:
        return task
    for e in task[last + 1:]:
        dropped.append((e["i"], e["tool"], "after the last meaningful step"))
    return task[:last + 1]


def split_login(kept: list[dict]):
    """D32: everything up to and including the first click after the last type_secret is login."""
    secret_idx = [n for n, e in enumerate(kept) if e["tool"] == "type_secret"]
    if not secret_idx:
        return [], kept
    for n in range(secret_idx[-1] + 1, len(kept)):
        if kept[n]["tool"] == "click":
            return kept[:n + 1], kept[n + 1:]
    raise CompileError("secrets were typed but no click followed. The login click is missing.")


# %% OFFLINE 5: steps, capability, outcome rule (D8, D9, D10, D29, D33)
SENSITIVE_WORDS = ("ssn", "password", "social")


def _params(text: str, inputs: dict, constants: list, where: str) -> str:
    """A typed or chosen value. Whole-value match -> {{name}}. Otherwise substitute inside. No match at all -> constant."""
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


def build_steps(events: list[dict], specs: dict, constants: list):
    """Events -> (steps, outputs, secrets, paths). Adds a navigate for the start page, and where the URL changed with no click."""
    inputs = {n: s["value"] for n, s in specs.items()}
    steps, outputs, secrets, paths = [], [], [], []
    prev = None
    for n, e in enumerate(events):
        t, where = e["tool"], f"event {e['i']} ({e['tool']})"
        b, a = e["before"]["url"], e["after"]["url"]
        paths += [b, a]
        if t == "open_path":
            steps.append(Navigate(path=substitute(norm_url(e["path"]), inputs), why="Opened directly by the agent."))
            paths.append(norm_url(e["path"]))
        elif prev is None or b != prev:
            steps.append(Navigate(path=substitute(b, inputs),
                                  why="Start page of this capability." if prev is None else "The page changed without a click."))
        prev = a
        el = e.get("el") or {}
        if t == "click":
            risky = bool(e.get("approved"))
            steps.append(Click(target=derive_target(el, inputs), risk="risky" if risky else "safe",
                               amount_input=_amount_input(specs) if risky else None,
                               why="Point of no return. A human approved it in discovery. Replay decides by policy." if risky else None))
        elif t in ("type_text", "type_secret"):
            field = f"{el.get('name') or ''} {el.get('label') or ''}".lower()
            if t == "type_text" and any(w in field for w in SENSITIVE_WORDS):
                raise CompileError(f"{where}: typed into a sensitive field ({el.get('label') or el.get('name')}). Refusing to record it.")
            if t == "type_secret":
                if e["value"] not in secrets:
                    secrets.append(e["value"])
                value = "{{secret:" + e["value"] + "}}"
            else:
                value = _params(e["value"], inputs, constants, f"{where} into {el.get('label') or el.get('name')!r}")
            steps.append(TypeText(target=derive_target(el, inputs), value=value))
        elif t == "select_option":
            if el.get("options") and e["value"] not in el["options"]:
                raise CompileError(f"{where}: option {e['value']!r} is not in the dropdown's options")
            steps.append(Select(target=derive_target(el, inputs),
                                option=_params(e["value"], inputs, constants, f"{where} in {el.get('label') or el.get('name')!r}")))
        elif t == "extract_value":
            steps.append(Extract(target=Target(locators=[LabeledValueLocator(label=substitute(e["label"], inputs))]), save_as=e["save_as"]))
            outputs.append(OutputParam(name=e["save_as"], type=e.get("value_type", "string"),
                                       description=e.get("description") or f"The value shown next to '{e['label']}'."))
    return steps, outputs, secrets, paths


def find_leftovers(cap: "Capability", inputs: dict) -> list[str]:
    """D29: no declared literal may survive anywhere in the capability, except in the `inputs` docs.
    The message names the input and the place, never the value."""
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


def _routes(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        p = path_only(p)
        if p and p not in out:
            out.append(p)
    return out


def _checkpoint(last: dict) -> "Checkpoint":
    url, heading = last["after"]["url"], (last["after"].get("heading") or "").strip()
    if not heading:
        raise CompileError("the final page has no heading or title, so the checkpoint has no text signal (D9 needs both)")
    return Checkpoint(url_contains=path_only(url).rsplit("/", 1)[-1] or "/", text_present=heading)


def _cap(name, description, when_to_use, events, specs, rules, constants) -> "Capability":
    steps, outputs, secrets, paths = build_steps(events, specs, constants)
    inputs = {n: s["value"] for n, s in specs.items()}
    text = json.dumps([x.model_dump(mode="json") for x in steps])
    used = [n for n in specs if "{{" + n + "}}" in text]
    cap = Capability(
        name=name, version=1, status="draft", description=description, when_to_use=when_to_use,
        app=App(**APP),
        risk_level="risky" if any(s.action == "click" and s.risk == "risky" for s in steps) else "safe",
        inputs=[InputParam(name=n, type=s.get("type", "string"), description=s.get("description", n),
                           pattern=s.get("pattern")) for n, s in specs.items() if n in used],
        outputs=outputs, secrets=secrets, routes=_routes(paths), steps=steps,
        checkpoint=_checkpoint(events[-1]), outcome_rules=list(rules),
    )
    bad = find_leftovers(cap, inputs)
    if bad:
        raise CompileError(bad)
    return cap


def relogin_rule() -> "OutcomeRule":
    return OutcomeRule(when=Condition(text_present=SESSION_EXPIRED_TEXT), kind="recoverable", action="relogin",
                       message="The session expired. Run the login capability again and continue.")


def _check_specs(specs: dict):
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


def compile_run(events: list[dict], spec: dict, *, extra_rules=()) -> dict:
    """The whole pipeline. Returns {"login": Capability|None, "task": Capability, "report": {...}}.
    spec = {name, description, when_to_use, inputs: {name: {value, type, description, pattern?}}}"""
    specs = spec["inputs"]
    _check_specs(specs)
    if any(e["tool"] == "finish" and e.get("outcome") for e in events):
        raise CompileError("this run ended with a business outcome. It is a probe: use rule_from_probe(), not compile_run().")
    kept, dropped = clean_events(events)
    kept = drop_detours(kept, dropped)
    login_ev, task_ev = split_login(kept)
    task_ev = trim_tail(task_ev, dropped)
    if not task_ev:
        raise CompileError("nothing left to record after the login. The run did nothing that matters.")
    constants: list = []
    try:
        login = None
        if login_ev:
            login = _cap(f"login_{APP['id']}", f"Log in to {APP['id']} with the stored credentials.",
                         "The session is logged out or has expired. Run before any capability that needs a logged-in session.",
                         login_ev, {}, [], constants)
            leak = find_leftovers(login, {n: s["value"] for n, s in specs.items()})
            if leak:
                raise CompileError(leak)
        rules = [*extra_rules] + ([relogin_rule()] if login else [])
        task = _cap(spec["name"], spec["description"], spec["when_to_use"], task_ev, specs, rules, constants)
    except ValidationError as err:                      # the Phase 2 schema said no
        raise CompileError([f"schema: {'; '.join(x['msg'] for x in err.errors())}"]) from err
    except ValueError as err:
        raise CompileError(f"schema: {err}") from err
    warnings = [f"declared input {n!r} is never used in the steps" for n in specs if n not in {i.name for i in task.inputs}]
    report = {"dropped": dropped, "constants": constants, "warnings": warnings}
    return {"login": login, "task": task, "report": report}


def rule_from_probe(events: list[dict], probe_inputs: dict[str, str]) -> "OutcomeRule":
    """D10: a bad-input run ended with finish(outcome, proof_text). Turn it into a business rule.
    The bad value is cut out of the proof text, so the rule matches for any input."""
    fin = next((e for e in reversed(events) if e["tool"] == "finish" and e.get("outcome")), None)
    if not fin:
        raise CompileError("this run has no finish(outcome=..., proof_text=...). It is not a probe.")
    pieces = [fin["proof"]]
    for lit in probe_inputs.values():
        pieces = [x for p in pieces for x in _literal_re(lit).split(p)]
    text = max((p.strip(" :#.-,") for p in pieces), key=len, default="")
    if len(text) < 6:
        raise CompileError("the proof text is too short once the input value is removed. Ask for a longer message from the page.")
    try:
        return OutcomeRule(when=Condition(text_present=text), kind="business", outcome=fin["outcome"],
                           message=f"Seen in a bad-input probe. The application answered: {text}")
    except ValidationError as err:
        raise CompileError(f"outcome rule: {'; '.join(x['msg'] for x in err.errors())}") from err


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
    path.write_text("# DRAFT written by the recorder (Phase 3). A reviewer must read it before it is verified.\n" + text)
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


# %% OFFLINE 6b: declared output types (D12). The extract tool and, later, replay use the same check
VALUE_TYPES = {"string": r"\S.*", "integer": r"-?\d+", "number": r"-?[\d,]*\.?\d+",
               "currency": r"-?\$?-?[\d,]+(\.\d{2})?", "boolean": r"true|false|yes|no"}


def value_matches_type(value: str, value_type: str) -> bool:
    return value_type in VALUE_TYPES and bool(re.fullmatch(VALUE_TYPES[value_type], value.strip(), re.I))


# %% [markdown]
# ## Offline tests (hand-made events, no browser)
# Run these cells any time. They prove the risky logic without a browser.

# %% OFFLINE 7: fixtures (hand-made events that look like a real ParaBank run)
def D(role, name, src, tag, *, label=None, text=None, submit=False, options=None, container=None, nth=None, type=None):
    """A descriptor, as the browser scanner would produce it."""
    return dict(role=role, name=name, name_source=src, tag=tag, type=type, label=label, text=text,
                submit=submit, options=options, container=container, nth=nth)


FORM, TABLE = {"role": "form", "name": None}, {"role": "table", "name": None}
USER = D("textbox", "username", "attr", "input", label="Username:", container=FORM, nth=1, type="text")
PASS = D("textbox", "password", "attr", "input", label="Password:", container=FORM, nth=2, type="password")
LOGIN = D("button", "Log In", "value", "input", submit=True, container=FORM, nth=3, type="submit")
ACCT = D("link", "14232", "text", "a", text="14232", container=TABLE, nth=1)
NEWACCT = D("link", "Open New Account", "text", "a", text="Open New Account")
OVERVIEW = D("link", "Accounts Overview", "text", "a", text="Accounts Overview")
XFER_LINK = D("link", "Transfer Funds", "text", "a", text="Transfer Funds")
AMOUNT = D("textbox", "amount", "attr", "input", label="Amount:", container=FORM, nth=1, type="text")
FROM = D("combobox", "fromAccountId", "attr", "select", label="From account #:", container=FORM, nth=1, options=["14232", "14343"])
TO = D("combobox", "toAccountId", "attr", "select", label="To account #:", container=FORM, nth=2, options=["14232", "14343"])
NOTE = D("textbox", "note", "attr", "input", label="Note:", container=FORM, nth=3, type="text")
TRANSFER = D("button", "Transfer", "value", "input", submit=True, container=FORM, nth=4, type="submit")
SSN = D("textbox", "ssn", "attr", "input", label="Social Security Number:", container=FORM, nth=5, type="text")


class Run:
    """Builds an event list the way the tools would. `to=(url, heading)` moves the page."""

    def __init__(self, url, heading=""):
        self.ev, self.url, self.head = [], url, heading

    def act(self, tool, el=None, *, status="ok", to=None, **kw):
        before = {"url": self.url, "heading": self.head}
        if to:
            self.url, self.head = to
        self.ev.append({"i": len(self.ev), "tool": tool, "status": status, "before": before,
                        "after": {"url": self.url, "heading": self.head}, "el": el, **kw})
        return self


def login_events(r):
    r.act("observe")
    r.act("type_secret", USER, value="username")
    r.act("type_secret", PASS, value="password")
    return r.act("click", LOGIN, to=("/overview.htm", "Accounts Overview"))


BAL_SPEC = {
    "name": "get_account_balance",
    "description": "Read the current balance of one account.",
    "when_to_use": "A caller needs the balance of a specific account and can name it by account id.",
    "inputs": {"account_id": {"value": "14232", "type": "string", "description": "The account number.", "pattern": "^[0-9]{4,10}$"}},
}
XFER_SPEC = {
    "name": "transfer_funds",
    "description": "Move money between two accounts of the same customer.",
    "when_to_use": "A caller wants to transfer a stated amount from one account to another.",
    "inputs": {
        "from_account": {"value": "14232", "type": "string", "description": "Account to take the money from.", "pattern": "^[0-9]{4,10}$"},
        "to_account": {"value": "14343", "type": "string", "description": "Account to put the money in.", "pattern": "^[0-9]{4,10}$"},
        "amount": {"value": "20.00", "type": "currency", "description": "Amount to move."},
    },
}


def good_balance(final_heading="Account Details"):
    r = login_events(Run("/index.htm", "Customer Login"))
    r.act("page_text")
    r.act("click", ACCT, status="failed")                                   # first try failed
    r.act("click", ACCT, to=("/activity.htm?id=14232", final_heading))
    r.act("extract_value", label="Balance:", save_as="balance", value_type="currency")
    r.act("finish")
    return r.ev


def transfer_events(approved=True):
    r = Run("/overview.htm", "Accounts Overview")
    r.act("click", XFER_LINK, to=("/transfer.htm", "Transfer Funds"))
    r.act("type_text", AMOUNT, value="$20.00")
    r.act("type_text", AMOUNT, value="$20.00")                              # repeated identical action
    r.act("select_option", FROM, value="14232")
    r.act("select_option", TO, value="14343")
    r.act("type_text", NOTE, value="Ref-77")                                # a constant: matches no input
    r.act("click", TRANSFER, approved=approved, to=("/transfer.htm", "Transfer Complete!"))
    r.act("finish")
    return r.ev


def rejects(name, fn, expect, hide=()):
    """fn must raise CompileError whose message contains `expect` and none of `hide`."""
    try:
        fn()
    except CompileError as err:
        msg = str(err)
        assert expect in msg, f"{name}: expected {expect!r} in: {msg}"
        assert not any(h in msg for h in hide), f"{name}: message leaks a value: {msg}"
        print(f"refused ok: {name}")
        return
    raise AssertionError(f"{name}: was NOT refused")


print("fixtures ready")

# %% OFFLINE 8: test helpers
assert norm_url("https://parabank.parasoft.com/parabank/activity.htm;jsessionid=ABC123?id=14232") == "/activity.htm?id=14232"
assert norm_url("https://parabank.parasoft.com/parabank/index.htm;jsessionid=ZZ") == "/index.htm"
assert norm_url("https://evil.example.com/x") == "https://evil.example.com/x"
assert contains_literal("id=5&x", "5") and not contains_literal("$50", "5") and not contains_literal("1.5", "5")
assert not contains_literal("account_id", "id")
assert substitute("Account #14232 to 14343", {"a": "14232", "b": "14343"}) == "Account #{{a}} to {{b}}"
assert same_value("$20.00", "20") and same_value("14232", "14232") and not same_value("0123", "123")
assert value_matches_type("$1,200.00", "currency") and value_matches_type("-5", "integer")
assert not value_matches_type("abc", "currency") and not value_matches_type("", "string") and not value_matches_type("x", "nope")
print("helpers: ok")

# %% OFFLINE 9: TEST good balance flow, login split, cleanup
res = compile_run(good_balance(), BAL_SPEC)
login, task = res["login"], res["task"]
assert login.name == "login_parabank" and login.secrets == ["username", "password"]
assert [s.action for s in login.steps] == ["navigate", "type", "type", "click"]
assert login.steps[1].value == "{{secret:username}}" and login.steps[2].value == "{{secret:password}}"
assert login.checkpoint.url_contains == "overview.htm" and login.checkpoint.text_present == "Accounts Overview"
# the task starts logged in and has no secret steps (D32)
assert task.secrets == [] and "secret:" not in to_yaml(task)
assert [s.action for s in task.steps] == ["navigate", "click", "extract"]
assert task.steps[0].path == "/overview.htm"
loc = task.steps[1].target.locators
assert loc[0].strategy == "role" and loc[0].role == "link" and loc[0].name == "{{account_id}}"
assert all(l.strategy != "structure" for l in loc), "no positional fallback for a data-dependent element"
assert task.steps[2].target.locators[0].strategy == "labeled_value" and task.steps[2].save_as == "balance"
assert [(o.name, o.type) for o in task.outputs] == [("balance", "currency")] and [i.name for i in task.inputs] == ["account_id"]
assert task.checkpoint.url_contains == "activity.htm" and task.checkpoint.text_present == "Account Details"
assert task.routes == ["/overview.htm", "/activity.htm"] and task.risk_level == "safe" and task.status == "draft"
assert [r.kind for r in task.outcome_rules] == ["recoverable"] and task.outcome_rules[0].action == "relogin"
text = to_yaml(task) + to_yaml(login)
assert "14232" not in text and "data-cua" not in text and "jsessionid" not in text
assert from_yaml(to_yaml(task)) == task and from_yaml(to_yaml(login)) == login
reasons = {(i, why) for i, _, why in res["report"]["dropped"]}
assert (0, "not an action") in reasons and (4, "not an action") in reasons and (5, "did not work (failed)") in reasons
print("good balance flow: ok | login split: ok | cleanup: ok")

# a run with no secrets typed (already logged in) has no login capability
r = Run("/overview.htm", "Accounts Overview")
r.act("click", ACCT, to=("/activity.htm?id=14232", "Account Details"))
r.act("extract_value", label="Balance:", save_as="balance", value_type="currency")
res2 = compile_run(r.ev, BAL_SPEC)
assert res2["login"] is None and res2["task"].outcome_rules == []
print("no login in run -> no login capability: ok")

# %% OFFLINE 10: TEST dead-end click and trailing click
r = login_events(Run("/index.htm", "Customer Login"))
r.act("click", NEWACCT, to=("/openaccount.htm", "Open New Account"))        # wrong turn
r.act("click", OVERVIEW, to=("/overview.htm", "Accounts Overview"))         # and back
r.act("click", ACCT, to=("/activity.htm?id=14232", "Account Details"))
r.act("extract_value", label="Balance:", save_as="balance", value_type="currency")
r.act("click", OVERVIEW, to=("/overview.htm", "Accounts Overview"))         # wandered off afterwards
res = compile_run(r.ev, BAL_SPEC)
assert [s.action for s in res["task"].steps] == ["navigate", "click", "extract"]
assert "/openaccount.htm" not in res["task"].routes
assert res["task"].checkpoint.url_contains == "activity.htm"                # from the last KEPT step, not the wandering
why = {i: w for i, _, w in res["report"]["dropped"]}
assert why[4].startswith("dead end") and why[5].startswith("dead end") and why[8] == "after the last meaningful step"
print("dead-end click removed: ok | trailing click removed: ok")

# a page change with no click (e.g. the harness opened a page) becomes a navigate
r = Run("/overview.htm", "Accounts Overview")
r.act("click", ACCT, to=("/activity.htm?id=14232", "Account Details"))
r.url = "/transactions.htm"                                                  # the URL moved by itself
r.act("extract_value", label="Balance:", save_as="balance", value_type="currency")
steps = compile_run(r.ev, BAL_SPEC)["task"].steps
assert [s.action for s in steps] == ["navigate", "click", "navigate", "extract"] and steps[2].path == "/transactions.htm"
print("navigation without a click is kept: ok")

# %% OFFLINE 11: TEST leftover-literal refusal
rejects("literal left in the checkpoint", lambda: compile_run(good_balance("Details for account 14232"), BAL_SPEC),
        "input 'account_id' still appears as a literal in checkpoint.text_present", hide=("14232",))
rejects("declared value does not match its own pattern",
        lambda: compile_run(good_balance(), {**BAL_SPEC, "inputs": {"account_id": {**BAL_SPEC["inputs"]["account_id"], "value": "12"}}}),
        "does not match its own pattern")
rejects("empty declared value",
        lambda: compile_run(good_balance(), {**BAL_SPEC, "inputs": {"account_id": {"value": ""}}}), "no declared value")

# %% OFFLINE 12: TEST risky click, parameters, constants
res = compile_run(transfer_events(), XFER_SPEC)
t = res["task"]
click = t.steps[-1]
assert click.action == "click" and click.risk == "risky" and click.amount_input == "amount" and t.risk_level == "risky"
assert [s.action for s in t.steps] == ["navigate", "click", "type", "select", "select", "type", "click"]   # the repeat is gone
assert t.steps[2].value == "{{amount}}" and t.steps[3].option == "{{from_account}}" and t.steps[4].option == "{{to_account}}"
assert t.steps[3].target.locators[0].strategy == "label"                      # name came from an attribute, so no role locator
assert t.steps[3].target.locators[-1].strategy == "structure" and t.steps[3].target.locators[-1].within.role == "form"
assert click.target.locators[0].role == "button" and click.target.locators[0].name == "Transfer"
assert t.checkpoint.url_contains == "transfer.htm" and t.checkpoint.text_present == "Transfer Complete!"
assert res["report"]["constants"] == [{"where": "event 5 (type_text) into 'Note:'", "value": "Ref-77"}]
assert any(why == "repeat of the previous action" for _, _, why in res["report"]["dropped"])
assert not any(v in to_yaml(t) for v in ("14232", "14343", "20.00"))
assert [i.name for i in t.inputs] == ["from_account", "to_account", "amount"]
c = tool_contract(t)
assert c["returns"]["may_need_approval"] is True and c["input_schema"]["required"] == ["from_account", "to_account", "amount"]
print("risky click: ok | typed values -> inputs: ok | constants reported: ok")

# control: the same run with no human approval is a safe capability
t2 = compile_run(transfer_events(approved=False), XFER_SPEC)["task"]
assert t2.risk_level == "safe" and t2.steps[-1].risk == "safe" and t2.steps[-1].amount_input is None
print("no approval -> safe: ok")

# %% OFFLINE 13: TEST bad-input outcome
probe = Run("/overview.htm", "Accounts Overview")
probe.act("open_path", path="/activity.htm?id=99999999", to=("/activity.htm?id=99999999", "Error!"))
probe.act("finish", outcome="ACCOUNT_NOT_FOUND", proof="Could not find account number 99999999")
rule = rule_from_probe(probe.ev, {"account_id": "99999999"})
assert rule.kind == "business" and rule.outcome == "ACCOUNT_NOT_FOUND"
assert rule.when.text_present == "Could not find account number" and "99999999" not in rule.when.text_present
res = compile_run(good_balance(), BAL_SPEC, extra_rules=[rule])
task = res["task"]
assert [r.kind for r in task.outcome_rules] == ["business", "recoverable"]
assert tool_contract(task)["returns"]["business_outcomes"] == ["ACCOUNT_NOT_FOUND"]
assert from_yaml(to_yaml(task)) == task
rejects("a probe is not a capability", lambda: compile_run(probe.ev, BAL_SPEC), "It is a probe")
rejects("a normal run is not a probe", lambda: rule_from_probe(good_balance(), {}), "not a probe")
print("bad-input outcome rule: ok")

# %% OFFLINE 14: TEST refusals (handoff, sensitive field, secret value on save, save path)
r = Run("/transfer.htm", "Transfer Funds")
r.act("request_value", AMOUNT, status="handoff")
r.act("click", TRANSFER, approved=True, to=("/transfer.htm", "Transfer Complete!"))
rejects("a human typed a value by hand", lambda: compile_run(r.ev, XFER_SPEC), "entered something by hand")

r = Run("/register.htm", "Signing up")
r.act("type_text", SSN, value="123-45-6789")
rejects("typed into a sensitive field", lambda: compile_run(r.ev, XFER_SPEC), "sensitive field", hide=("123-45-6789",))

rejects("secrets typed but no login click", lambda: compile_run(Run("/index.htm").act("type_secret", USER, value="username").ev, BAL_SPEC),
        "login click is missing")
rejects("off-site start page is not a valid path",
        lambda: compile_run(Run("https://evil.example.com/x").act("click", ACCT, to=("/a.htm", "A")).ev, BAL_SPEC), "schema")

with tempfile.TemporaryDirectory() as tmp:
    good = compile_run(good_balance(), BAL_SPEC)["task"]
    rejects("secret value must never reach the file", lambda: save_capability(good, tmp, forbidden=["Account Details"]),
            "secret value would be written", hide=("Account Details",))
    assert not list(pathlib.Path(tmp).iterdir()), "nothing may be written when the guard trips"
    path = save_capability(good, tmp, forbidden=["hunter2-not-present"])
    assert from_yaml(path.read_text()) == good and path.read_text().startswith("# DRAFT")
    verified = good.model_copy(update={"status": "verified"})
    path.write_text(to_yaml(verified))
    rejects("never overwrite a verified capability", lambda: save_capability(good, tmp), "already verified")
print("refusals: ok | save: ok")

# %% OFFLINE 15: summary
print("\nALL OFFLINE CHECKS PASSED")


# %% [markdown]
# ## Part A. CAPTURE (needs the browser and an API key)
# **Temporary duplication:** the setup, scanner, takeover and tool cells below are copied from `agent.ipynb`
# (Phase 1) and changed only where the recorder needs it. `agent.ipynb` is untouched. Phase 9 merges them into `src/`.
# What changed vs Phase 1:
# - the scanner returns a full **descriptor** per element (role, name, where the name came from, label, text, container, nth);
# - every tool logs an **event** (before and after page, descriptor, did it work, was it approved);
# - new tools `extract_value` and `open_path`; `finish` can report a business **outcome** with proof;
# - value grounding uses the declared inputs first; `web_search` is removed (it sends text outside the allowlist).

# %% BROWSER 1: environment, secrets, model
import asyncio
import base64
import functools
import os

from dotenv import load_dotenv

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-5")


def resolve_secret(name: str) -> str:
    """Look up a secret by name. Raises on unknown name or empty value. The value is never printed."""
    if name not in SECRETS:
        raise KeyError(f"unknown secret name: {name!r}")
    value = os.environ.get(SECRETS[name], "")
    if not value:
        raise RuntimeError(f"env var {SECRETS[name]} is empty or not set")
    return value


print("model:", MODEL, "| base:", BASE)

# %% BROWSER 2: open the browser (skips if one is already open in this kernel)
from playwright.async_api import async_playwright

if "page" not in globals():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
await page.goto(f"{BASE}/index.htm")
print("opened:", page.url)

# %% BROWSER 3: domain guard
def host_allowed(url: str) -> bool:
    return url == "about:blank" or urlparse(url).hostname in ALLOWED_HOSTS

# %% BROWSER 4: scanner with element descriptors, and read_labeled_value
from dataclasses import dataclass

# The model still sees only "[ref] role "name"". The extra fields are for the recorder.
# data-cua-ref is a TEMPORARY handle so a tool can find the element the model pointed at. It is never saved.
OBSERVE_JS = """
() => {
  document.querySelectorAll('[data-cua-ref]').forEach(e => e.removeAttribute('data-cua-ref'));
  const sel = 'a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=link], [onclick]';
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
  const formCtl = (el) => ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
  // [name, where the name came from]. Only aria/label/value/text/attr_acc are real accessible names.
  // 'attr' (the name= or id= attribute) is NOT one, so the recorder will not build a role locator from it.
  const nameInfo = (el) => {
    const aria = norm(el.getAttribute('aria-label')); if (aria) return [aria, 'aria'];
    const lb = el.getAttribute('aria-labelledby');
    if (lb) { const t = norm(lb.split(/\\s+/).map(id => (document.getElementById(id) || {}).innerText || '').join(' ')); if (t) return [t, 'aria']; }
    if (el.labels && el.labels.length) { const t = norm(el.labels[0].innerText); if (t) return [t, 'label']; }
    const tag = el.tagName.toLowerCase(), ty = (el.getAttribute('type') || '').toLowerCase();
    if (tag === 'input' && ['submit', 'button', 'reset'].includes(ty)) { const v = norm(el.value); if (v) return [v, 'value']; }
    if (!['select', 'textarea', 'input'].includes(tag)) { const t = norm(el.innerText); if (t) return [t.slice(0, 80), 'text']; }
    for (const a of ['placeholder', 'title', 'alt']) { const v = norm(el.getAttribute(a)); if (v) return [v, 'attr_acc']; }
    const nm = el.getAttribute('name') || el.id; if (nm) return [nm, 'attr'];
    return ['', 'none'];
  };
  const labelOf = (el, role) => {
    if (!formCtl(el) || role === 'button') return '';
    if (el.labels && el.labels.length) return norm(el.labels[0].innerText).slice(0, 60);
    const cell = el.closest('td, th, dd');
    const prev = cell && cell.previousElementSibling;
    return prev ? norm(prev.innerText).slice(0, 60) : '';
  };
  // The container the control sits in. Controls prefer their form, other things prefer their table.
  const containerOf = (el) => {
    const form = el.closest('form, [role=form]');
    const tbl = el.closest('table, [role=table], [role=grid]');
    const c = formCtl(el) || el.tagName === 'BUTTON' ? (form || tbl) : (tbl || form);
    if (!c) return [null, null];
    const isForm = c === form;
    let name = norm(c.getAttribute('aria-label'));
    if (!name) { const lb = c.getAttribute('aria-labelledby'); if (lb) name = norm(lb.split(/\\s+/).map(id => (document.getElementById(id) || {}).innerText || '').join(' ')); }
    if (!name && !isForm) { const cap = c.querySelector('caption'); if (cap) name = norm(cap.innerText); }
    if (!name && isForm) { const lg = c.querySelector('legend'); if (lg) name = norm(lg.innerText); }
    const tag = el.tagName.toLowerCase();
    const nth = Array.from(c.querySelectorAll(tag)).indexOf(el) + 1;
    return [{ role: isForm ? 'form' : 'table', name: name || null }, nth || null];
  };
  const items = [];
  document.querySelectorAll(sel).forEach((el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width < 2 || r.height < 2 || st.visibility === 'hidden' || st.display === 'none') return;
    const ref = items.length + 1;
    el.setAttribute('data-cua-ref', String(ref));
    const role = roleOf(el), ni = nameInfo(el), cn = containerOf(el);
    items.push({
      ref, role, name: ni[0], name_source: ni[1],
      tag: el.tagName.toLowerCase(), type: (el.getAttribute('type') || '').toLowerCase() || null,
      label: labelOf(el, role) || null,
      text: formCtl(el) ? null : (norm(el.innerText).slice(0, 80) || null),
      container: cn[0], nth: cn[1],
      options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => o.text.trim()).slice(0, 15) : null,
      submit: (el.tagName === 'BUTTON' && el.type !== 'button') || (el.tagName === 'INPUT' && ['submit', 'image'].includes(el.type)),
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

HEADING_JS = """
() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const pick = (q) => Array.from(document.querySelectorAll(q)).find(vis);
  const el = pick('h1') || pick('.title') || pick('h2');
  return ((el && el.innerText) || document.title || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
}
"""

# The value shown next to a label: the cell after it, the input a <label> points at, or the next sibling.
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


async def read_labeled_value(page, label: str) -> str:
    """The value shown next to `label` on the current page. Raises LookupError if there is none.
    Written to be reused by Phase 4 replay, so record and replay read values the same way."""
    res = await page.evaluate(READ_LABELED_JS, label)
    if not res["value"]:
        raise LookupError(f"no value found next to the label {label!r}")
    return res["value"]


def shown_name(e: dict) -> str:
    """What the model sees. A name that is only an attribute (fromAccountId) reads better as its label."""
    return e["label"] if e.get("name_source") == "attr" and e.get("label") else e["name"]


def format_elements(elements: list[dict]) -> str:
    lines = []
    for e in elements:
        line = f'[{e["ref"]}] {e["role"]} "{shown_name(e)}"'
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

    def element(self, ref: int) -> dict | None:
        return next((e for e in self.last_elements if e["ref"] == ref), None)

    def name_of(self, ref: int) -> str | None:
        e = self.element(ref)
        return shown_name(e) if e else None

    async def click(self, ref: int):
        await self.page.locator(f'[data-cua-ref="{ref}"]').click(timeout=5000)
        await self.page.wait_for_timeout(600)
        try:
            await self.page.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass

    async def type_text(self, ref: int, text: str):
        await self.page.locator(f'[data-cua-ref="{ref}"]').fill(text, timeout=5000)

    async def page_text(self) -> str:
        return (await self.page.inner_text("body"))[:4000]


surface = PlaywrightSurface(page)
print("scanner ready")

# %% BROWSER 5: takeover (red bar with a Done button) and the approval bar
HANDBACK = {"event": None}

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

BANNER_JS = """
(() => {
  const render = () => {
    if (sessionStorage.getItem('cua_takeover') !== '1' || document.getElementById('__cua_banner')) return;
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
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render); else render();
})();
"""

if "_takeover_ready" not in globals():
    async def _handback():
        if HANDBACK["event"]:
            HANDBACK["event"].set()
    await page.expose_function("__cua_handback", _handback)
    await page.add_init_script(BANNER_JS)
    _takeover_ready = True


async def human_takeover(question: str = "") -> str:
    """Give the live browser to a human. Returns when they click 'Done' in the page."""
    HANDBACK["event"] = asyncio.Event()
    visited = []
    on_nav = lambda frame: visited.append(norm_url(frame.url)) if frame == page.main_frame else None
    page.on("framenavigated", on_nav)
    await page.evaluate("([q]) => { sessionStorage.setItem('cua_takeover', '1'); sessionStorage.setItem('cua_question', q); }", [question])
    await page.evaluate(BANNER_JS)
    await HANDBACK["event"].wait()
    page.remove_listener("framenavigated", on_nav)
    await page.evaluate("sessionStorage.removeItem('cua_takeover'); sessionStorage.removeItem('cua_question'); document.getElementById('__cua_banner')?.remove()")
    text = (await page.inner_text("body"))[:300].replace("\n", " ")
    return f"Pages the human visited: {visited or 'none'}. Page now: {norm_url(page.url)}. Page text: {text}"

print("takeover ready")

# %% BROWSER 6: capture (events)
from langchain.tools import tool

EVENTS: list[dict] = []          # the recording. One dict per tool call. No secret values, no extracted values.
DECLARED: dict[str, str] = {}    # input name -> the literal value the user declared for this run (D29)
GIVEN = {"text": ""}             # the goal text of this run
TYPED: dict[str, str] = {}       # what the agent entered, by field name (shown in the approval bar)
DECLINED: set[str] = set()       # buttons a human refused. Never clicked again this run.
RESULT: dict = {}

DESCRIPTOR_KEYS = ("role", "name", "name_source", "tag", "type", "label", "text", "submit", "options", "container", "nth")


async def page_state() -> dict:
    try:
        heading = await page.evaluate(HEADING_JS)
    except Exception:
        heading = ""
    return {"url": norm_url(page.url), "heading": heading}


def descriptor_of(ref: int) -> dict | None:
    """Describe the element the model pointed at. The temporary ref number is left out on purpose."""
    e = surface.element(ref)
    return {k: e.get(k) for k in DESCRIPTOR_KEYS} if e else None


async def record(tool_name: str, before: dict, status: str = "ok", el: dict | None = None, **extra):
    EVENTS.append({"i": len(EVENTS), "tool": tool_name, "status": status, "before": before,
                   "after": await page_state(), "el": el, **extra})


def is_given(text: str) -> bool:
    """D34 + D29: a typed or chosen value must be a declared input value, or a whole word/number in the goal."""
    t = text.strip()
    if not t:
        return False
    return any(same_value(t, v) for v in DECLARED.values()) or contains_literal(GIVEN["text"].lower(), t.lower())


print("capture ready")

# %% BROWSER 7: tools (Phase 1 safety kept; every tool logs an event)
ACT_LOCK = asyncio.Lock()


def one_at_a_time(fn):
    @functools.wraps(fn)
    async def wrapper(*a, **k):
        async with ACT_LOCK:
            return await fn(*a, **k)
    return wrapper


DENY_LINKS = ("register", "lookup", "admin")
SAFE_SUBMITS = {"log in", "find transactions"}   # buttons that do not change data
AUTO_LIMIT = None                                # None = always ask a human. Later: 500.0 for small transfers


def _blocks(prefix: str, obs) -> list[dict]:
    """Package text and a screenshot as one tool result the model can read."""
    return [
        {"type": "text", "text": f"{prefix}\n{obs.as_text()}"},
        {"type": "image", "base64": base64.b64encode(obs.png).decode(), "mime_type": "image/png"},
    ]


def current_page() -> str:
    """Page name from the URL: no query, no ;jsessionid=, no trailing slash, lower case."""
    return page.url.split("?")[0].split(";")[0].rstrip("/").rsplit("/", 1)[-1].lower()


def _amount() -> float:
    raw = next((v for k, v in TYPED.items() if k.startswith("amount")), "").replace("$", "").replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return float("inf")                      # unknown amount counts as risky


def needs_human(ref: int) -> bool:
    """Every button except a short safe list needs a human. Links (navigation) run freely."""
    el = surface.element(ref)
    role = (el or {}).get("role")
    name = (surface.name_of(ref) or "").strip().lower()
    risky = bool(el) and (bool(el.get("submit")) or role == "button") and name not in SAFE_SUBMITS
    if risky and "transfer" in name and AUTO_LIMIT is not None and _amount() <= AUTO_LIMIT:
        risky = False
    print(f"approval check -> role={role!r} name={name!r} risky={risky}")
    return risky


def approval_info(ref: int) -> dict:
    fields = "; ".join(f"{k}: {v}" for k, v in TYPED.items()) or "(nothing typed)"
    return {"title": f"Agent wants to click '{surface.name_of(ref)}' on {current_page()}", "details": f"Values it entered: {fields}"}


async def _ask_for_value(field: str, kind: str, tool_name: str, before: dict, el: dict | None) -> list:
    """The agent tried to enter a value the user never gave. Hand the browser to a human.
    The compile refuses runs with a handoff: a hand-typed step cannot be recorded."""
    report = await human_takeover(f"I need a value for '{field}' and you did not give me one. Please {kind} it yourself in the page, then click Done.")
    await record(tool_name, before, "handoff", el)
    return _blocks(f"A human entered the value for '{field}' themselves. Do NOT type it again. {report}", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def observe() -> list:
    """Look at the current page.

    Returns:
        A screenshot with red numbered boxes, plus a text list of the numbered elements.
    """
    before = await page_state()
    obs = await surface.observe()
    await record("observe", before)
    return _blocks("Current page.", obs)


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
    before, el = await page_state(), descriptor_of(ref)
    name = (surface.name_of(ref) or "").strip().lower()
    if any(w in name for w in DENY_LINKS):
        await record("click", before, "denied", el)
        return _blocks(f"DENIED: '{name}' is not allowed.", await surface.observe())
    if name in DECLINED:
        await record("click", before, "declined", el)
        return _blocks("DECLINED earlier by a human. Do not retry. Call finish with 'DECLINED:' and stop.", await surface.observe())
    approved = False
    if needs_human(ref):
        choice = await page.evaluate(DECISION_JS, approval_info(ref))   # Approve / Reject / Take over appear in the browser
        if choice == "r":
            DECLINED.add(name)
            await record("click", before, "declined", el)
            return _blocks("DECLINED by a human. Do not retry or work around it. Call finish with 'DECLINED:' and stop.", await surface.observe())
        if choice == "t":
            report = await human_takeover()
            await record("click", before, "handoff", el)
            return _blocks(f"A human completed this step manually in the browser. {report} Do NOT click again. Check the result from the page text, then call finish.", await surface.observe())
        approved = True                                                  # a human said yes: this click becomes risk: risky
    try:
        await surface.click(ref)
    except Exception as exc:
        await record("click", before, "failed", el)
        return _blocks(f"CLICK FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    if not host_allowed(page.url):
        await page.go_back()
        await record("click", before, "blocked", el)
        return _blocks("BLOCKED: left the allowed site. Went back.", await surface.observe())
    await record("click", before, "ok", el, approved=approved)
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
    before, el = await page_state(), descriptor_of(ref)
    field = (surface.name_of(ref) or f"field {ref}").strip()
    words = f"{field} {(el or {}).get('name') or ''}".lower()
    if any(w in words for w in SENSITIVE_WORDS) or not is_given(text):
        return await _ask_for_value(field, "type", "type_text", before, el)
    try:
        await surface.type_text(ref, text)
    except Exception as exc:
        await record("type_text", before, "failed", el, value=text)
        return _blocks(f"TYPE FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    TYPED[field.lower()] = text
    await record("type_text", before, "ok", el, value=text)
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
    before, el = await page_state(), descriptor_of(ref)
    if name not in SECRETS:
        await record("type_secret", before, "failed", el, value=name)
        return _blocks(f"UNKNOWN SECRET '{name}'. Use one of: {list(SECRETS)}", await surface.observe())
    if not host_allowed(page.url):
        await record("type_secret", before, "denied", el, value=name)
        return _blocks("REFUSED: this site is not on the allowlist.", await surface.observe())
    try:
        await page.locator(f'[data-cua-ref="{ref}"]').fill(resolve_secret(name), timeout=5000)
    except Exception as exc:
        await record("type_secret", before, "failed", el, value=name)
        return _blocks(f"FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    await record("type_secret", before, "ok", el, value=name)          # the NAME is recorded, never the value
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
    before, el = await page_state(), descriptor_of(ref)
    field = (surface.name_of(ref) or f"dropdown {ref}").strip()
    if not is_given(option):
        return await _ask_for_value(field, "choose", "select_option", before, el)
    try:
        await page.locator(f'[data-cua-ref="{ref}"]').select_option(label=option, timeout=5000)
    except Exception as exc:
        await record("select_option", before, "failed", el, value=option)
        return _blocks(f"SELECT FAILED for [{ref}]: {type(exc).__name__}", await surface.observe())
    TYPED[field.lower()] = option
    await record("select_option", before, "ok", el, value=option)
    return _blocks(f"Selected '{option}' in [{ref}].", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def page_text() -> str:
    """Read the visible text of the whole page (balances, tables, messages).

    Returns:
        The page text, up to 4000 characters.
    """
    before = await page_state()
    text = await surface.page_text()
    await record("page_text", before)
    return text


@tool(parse_docstring=True)
@one_at_a_time
async def extract_value(label: str, save_as: str, value_type: str = "string", description: str = "") -> str:
    """Read the value shown next to a label on the page, and record it as an output of the capability.

    Use this for anything the user wants to know, like a balance. Balances are not clickable, so
    you point at them by their label, for example 'Balance:'.

    Args:
        label: The label text as shown on the page, for example 'Balance:'.
        save_as: Output name in lower_snake_case, for example 'balance'.
        value_type: One of string, integer, number, currency, boolean.
        description: One short sentence saying what the value is. Do not put the value in it.

    Returns:
        The value that was read.
    """
    before = await page_state()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", save_as):
        return "save_as must be lower_snake_case, like 'balance'."
    if value_type not in VALUE_TYPES:
        return f"value_type must be one of {sorted(VALUE_TYPES)}."
    try:
        value = await read_labeled_value(page, label)
    except LookupError as exc:
        await record("extract_value", before, "failed", None, label=label, save_as=save_as)
        return f"FAILED: {exc}. Check the label on the page (use page_text) and try again."
    if not value_matches_type(value, value_type):
        await record("extract_value", before, "failed", None, label=label, save_as=save_as)
        return f"FAILED: the value next to {label!r} does not look like a {value_type}. Use another value_type or label."
    await record("extract_value", before, "ok", None, label=label, save_as=save_as, value_type=value_type, description=description)
    return f"{label} {value}"                                            # the value goes to the model, not into the event


@tool(parse_docstring=True)
@one_at_a_time
async def open_path(path: str) -> list:
    """Open a page of the banking site by its path, for example /overview.htm.

    Use it only when the goal names the page or the id to look at. Any value in the path must come from the goal.

    Args:
        path: Path on the site, starting with '/'. May have a query, for example /activity.htm?id=12345.

    Returns:
        The new page state.
    """
    before = await page_state()
    p = path.strip()
    values = [v for _, v in parse_qsl(urlparse(p).query)]
    if not p.startswith("/") or p.startswith("//") or any(w in p.lower() for w in DENY_LINKS):
        await record("open_path", before, "denied", None, path=p)
        return _blocks("DENIED: give a path on this site, starting with '/'.", await surface.observe())
    if not all(is_given(v) for v in values):
        await record("open_path", before, "denied", None, path=p)
        return _blocks("DENIED: every value in the path must come from the goal. Never invent one.", await surface.observe())
    try:
        await page.goto(BASE + p)
        await page.wait_for_load_state("load", timeout=5000)
    except Exception as exc:
        await record("open_path", before, "failed", None, path=p)
        return _blocks(f"OPEN FAILED: {type(exc).__name__}", await surface.observe())
    if not host_allowed(page.url):
        await page.go_back()
        await record("open_path", before, "blocked", None, path=p)
        return _blocks("BLOCKED: left the allowed site. Went back.", await surface.observe())
    await record("open_path", before, "ok", None, path=norm_url(BASE + p))
    return _blocks(f"Opened {p}.", await surface.observe())


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
    before = await page_state()
    print(f"guard (ask_human) -> page={current_page()!r} start_page={current_page() in START_PAGES}")
    if current_page() in START_PAGES:
        await record("ask_human", before, "blocked")
        return _blocks("NOT YET: you are still on the start page. Open the page where this task is done first "
                       "(use the menu). Then, with the form on screen, use request_value on each field you cannot fill.", await surface.observe())
    report = await human_takeover(question)
    await record("ask_human", before, "handoff")
    return _blocks(f"A human took over and handed back. {report}", await surface.observe())


@tool(parse_docstring=True)
@one_at_a_time
async def request_value(ref: int) -> list:
    """Ask the human to fill one field that you cannot fill, because the user did not give the value.

    Open the page that has the field first. Then point at the field. The page scrolls to it,
    the human types the value there and hands control back. Do not type into that field yourself afterwards.

    Args:
        ref: Number of the field (input box or dropdown) in the latest screenshot and list.

    Returns:
        The new page state, after the human is done.
    """
    before, el = await page_state(), descriptor_of(ref)
    print(f"guard (request_value) -> page={current_page()!r} start_page={current_page() in START_PAGES}")
    if current_page() in START_PAGES:
        await record("request_value", before, "blocked", el)
        return _blocks("NOT YET: you are still on the start page. Open the page that has this form first.", await surface.observe())
    field = (surface.name_of(ref) or f"field {ref}").strip()
    try:
        loc = page.locator(f'[data-cua-ref="{ref}"]')
        await loc.scroll_into_view_if_needed(timeout=3000)
        await loc.focus(timeout=3000)
    except Exception:
        pass                                     # the human can still find it; do not fail the request
    return await _ask_for_value(field, "enter", "request_value", before, el)


@tool(parse_docstring=True)
async def finish(summary: str, values: dict[str, str], outcome: str = "", proof_text: str = "") -> str:
    """Report the final result and stop.

    If you cannot make progress, start the summary with 'STUCK:'. If a human declined, start it with 'DECLINED:'.
    If the site answered with a business outcome the goal told you to look for (for example the account does
    not exist), give its name in outcome and copy the exact sentence from the page into proof_text.

    Args:
        summary: One-line summary of what you did or why you stopped.
        values: The requested facts, for example {"balance": "$100.00"}.
        outcome: Optional. UPPER_SNAKE name of the business outcome, for example ACCOUNT_NOT_FOUND. Leave empty otherwise.
        proof_text: Required with outcome. The exact text on the page that proves it, copied from the page.

    Returns:
        A confirmation. Stop after this.
    """
    before = await page_state()
    if outcome or proof_text:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", outcome or ""):
            return "outcome must be UPPER_SNAKE, like ACCOUNT_NOT_FOUND. Call finish again."
        norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
        if not proof_text.strip() or norm(proof_text) not in norm(await page.inner_text("body")):
            return "proof_text must be text that is really on the current page, copied exactly. Use page_text, then call finish again."
    RESULT.clear()
    RESULT.update({"summary": summary, "values": values, "outcome": outcome})
    await record("finish", before, "ok", None, outcome=outcome or None, proof=proof_text or None)
    return "Recorded. Stop now."


BROWSER_TOOLS = [observe, click, type_text, type_secret, select_option, extract_value, open_path, page_text, request_value, ask_human, finish]
print("tools ready:", [t.name for t in BROWSER_TOOLS])

# %% BROWSER 8: system prompt and agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

SYSTEM_PROMPT = """You are an expert browser operator. You drive a real browser on a banking demo site.

## Browser tools
Every tool result shows a screenshot with red numbered boxes plus a list of numbered elements (dropdowns list their options). Refer to elements only by number. Numbers change after every action, so use the latest list.
- observe: look at the page.
- click(ref), type_text(ref, text), select_option(ref, option): act on elements.
- type_secret(ref, name): type a stored secret ('username' or 'password'). You never see the value.
- extract_value(label, save_as, value_type): read a value that is shown next to a label (for example 'Balance:'). This is how you report facts.
- open_path(path): open a page by its path. Only when the goal names the page or the id to look at.
- page_text: read the visible page text (to find the exact label or message).
- request_value(ref): a field you cannot fill because the user did not give the value. The human fills it on the page.
- ask_human(question): only when you are unsure what to click. Not for missing values.
- finish(summary, values, outcome, proof_text): report the result, then stop.

## How to work
1. Call observe first. If you see a login form, log in with type_secret, then confirm the account overview appears.
2. Do the task by the shortest path. Read every requested fact with extract_value, using the label exactly as shown on the page. Never invent a value.
3. Use ONLY values the user gave you in the goal. If a value you need is missing: FIRST open the page where the task is done (use the menu links), THEN point at each missing field with request_value(ref). Never ask a human while you are still on the start page.
4. If a tool says a human entered a value, do not type it again. Continue with the next step.
5. Buttons that change data (Send Payment, Transfer, Open New Account, and so on) need a human. Click the button when the form is ready; the system asks the human for approval by itself. If the result says DECLINED, never retry or work around it: call finish with 'DECLINED:'.
6. Make ONE tool call at a time. Do not click into a field before typing.
7. Business outcome: if the goal names an outcome (for example ACCOUNT_NOT_FOUND) and the page shows the matching message, call finish with outcome set to that name and proof_text set to the message copied exactly from the page. Otherwise leave outcome empty.
8. Stay on the banking site. If you are lost or repeat the same action 3 times, call finish with 'STUCK:' and say why.
9. Do not use ls, read_file, write_file, edit_file, delete, glob, grep or task.
"""

agent = create_deep_agent(model=MODEL, tools=BROWSER_TOOLS, system_prompt=SYSTEM_PROMPT, checkpointer=MemorySaver())
print("agent ready | approval is enforced inside the click tool")

# %% BROWSER 9: your test values and the run helper
import uuid

# CHANGE THESE to accounts that exist in YOUR ParaBank test user. Fake data only.
ACCOUNT_ID = "14232"        # an account you own (for the balance run)
BAD_ACCOUNT = "99999999"    # an account that does not exist (for the bad-input run)
FROM_ACCOUNT = "14232"      # transfer: from
TO_ACCOUNT = "14343"        # transfer: to (another account you own)
AMOUNT = "1.00"             # transfer amount. Keep it tiny.

BAL_LIVE = {**BAL_SPEC, "inputs": {"account_id": {**BAL_SPEC["inputs"]["account_id"], "value": ACCOUNT_ID}}}
XFER_LIVE = {**XFER_SPEC, "inputs": {
    "from_account": {**XFER_SPEC["inputs"]["from_account"], "value": FROM_ACCOUNT},
    "to_account": {**XFER_SPEC["inputs"]["to_account"], "value": TO_ACCOUNT},
    "amount": {**XFER_SPEC["inputs"]["amount"], "value": AMOUNT},
}}
RUNS: dict[str, list] = {}


async def run_agent(name: str, goal: str, specs: dict, *, logged_out: bool = False, start: str = "/overview.htm"):
    """Declare inputs, reset capture, run the agent, keep the events. Events go to notebooks/scratch/ (git-ignored)."""
    DECLARED.clear()
    DECLARED.update({n: s["value"] for n, s in specs.items()})
    GIVEN["text"] = goal
    TYPED.clear(); DECLINED.clear(); EVENTS.clear()
    if logged_out:
        await page.context.clear_cookies()       # so the login is part of the recording
    await page.goto(f"{BASE}/index.htm" if logged_out else f"{BASE}{start}")
    cfg = {"configurable": {"thread_id": f"{name}-{uuid.uuid4().hex[:6]}"}, "recursion_limit": 100}
    out = await agent.ainvoke({"messages": [{"role": "user", "content": goal}]}, config=cfg)
    RUNS[name] = list(EVENTS)
    SCRATCH.mkdir(exist_ok=True)
    (SCRATCH / f"events_{name}.json").write_text(json.dumps(RUNS[name], indent=1))
    print("\nAGENT SAID:", out["messages"][-1].content)
    print(f"RECORDED: {len(EVENTS)} events -> {SCRATCH / f'events_{name}.json'}")


def print_events(name: str):
    for e in RUNS[name]:
        el = e.get("el") or {}
        what = f"{el.get('role')} {(el.get('name') or '')[:30]!r}" if el else (e.get("label") or e.get("path") or "")
        print(f"{e['i']:>2} {e['tool']:<14} {e['status']:<8} {e['before']['url'][:28]:<28} -> {e['after']['url'][:28]:<28} {what}"
              + ("  [APPROVED]" if e.get("approved") else ""))


print("ready. accounts:", ACCOUNT_ID, "| bad:", BAD_ACCOUNT)

# %% BROWSER 10: RUN 1. Balance, starting logged out (this records the login too)
GOAL_BAL = (f"Log in. Then open account {ACCOUNT_ID} from the accounts overview and read its balance with "
            f"extract_value (use the label shown on the page, value_type currency, save_as balance). Then finish.")
await run_agent("balance", GOAL_BAL, BAL_LIVE["inputs"], logged_out=True)
print_events("balance")

# %% BROWSER 11: RUN 2. Bad input probe (finds the business outcome text)
GOAL_BAD = (f"Open the account details page for account {BAD_ACCOUNT} with open_path, using the path /activity.htm?id={BAD_ACCOUNT}. "
            f"If the page says the account cannot be found or shows an error, call finish with outcome ACCOUNT_NOT_FOUND and "
            f"proof_text set to the exact error sentence from the page. Do nothing else.")
await run_agent("bad_account", GOAL_BAD, {"account_id": {"value": BAD_ACCOUNT}})
print_events("bad_account")
RULE = rule_from_probe(RUNS["bad_account"], {"account_id": BAD_ACCOUNT})
print("\nRULE the recorder made:", RULE.outcome, "| when the page shows:", repr(RULE.when.text_present))

# %% BROWSER 12: compile run 1 (+ the outcome rule), show it, then save
result = compile_run(RUNS["balance"], BAL_LIVE, extra_rules=[RULE] if "RULE" in globals() else [])
show(result)
SAVE = True    # set False to look without writing
if SAVE:
    forbidden = [resolve_secret(n) for n in SECRETS]      # refuse to write if a real secret value is in the file
    for cap in (result["login"], result["task"]):
        if cap:
            print("saved:", save_capability(cap, forbidden=forbidden).relative_to(REPO))

# %% BROWSER 13: RUN 3 (optional). Transfer. A human must click Approve in the browser
GOAL_XFER = (f"Open Transfer Funds. Transfer {AMOUNT} from account {FROM_ACCOUNT} to account {TO_ACCOUNT}. "
             f"Fill the amount and both dropdowns, then click the Transfer button when the form is ready. Then finish.")
await run_agent("transfer", GOAL_XFER, XFER_LIVE["inputs"])
print_events("transfer")
result_x = compile_run(RUNS["transfer"], XFER_LIVE)
show(result_x)
if SAVE:
    print("saved:", save_capability(result_x["task"], forbidden=[resolve_secret(n) for n in SECRETS]).relative_to(REPO))
