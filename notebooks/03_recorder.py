# %% [markdown]
# # Phase 3: the recorder
# (HOW-TO BLOCK IS ADDED AT THE TOP IN THE LAST TASK)

# %% OFFLINE 1: config and Phase 2 models
# Pure Python. No browser, no network, no API key.
# The Phase 2 models are NOT copied. We run the model cells of 02_artifact_schema.py in this namespace.
import json
import pathlib
import re
import tempfile
from urllib.parse import urlparse

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
