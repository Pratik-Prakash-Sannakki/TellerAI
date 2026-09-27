# %% [markdown]
# # Phase 8: evidence capture helpers
# Pure Python. No browser, no network, no API key, no `import playwright` anywhere in this file.
# Two small, additive helpers that turn an already-completed run (discovery OR replay) into a
# self-contained folder under `evidence/`. Neither one runs a discovery agent or a replay itself --
# both take already-produced data (events/`Capability`/`compile_run`'s report, or a `Capability`/
# inputs/`ReplayResult`) and only ever write files. See `DECISIONS.md` D92 for the design writeup.
#
# `Capability`, `to_yaml`, `ReplayResult`, `Failure` are NOT copied here -- this file runs the
# model cells of `02_artifact_schema.py` in its own namespace, the same exec-cells-into-namespace
# technique `03_recorder.py` and `04_replay_engine.py` already use (D70). When this file is loaded
# a second way -- exec'd, definitions-only, into `05_replay_live.py`'s own namespace, which has
# already loaded the schema itself -- loading is skipped rather than redone (Section 1).
#
# ## How this file is tested (this agent runs this; no browser, ever)
# `uv run python notebooks/evidence_capture.py` runs every cell top to bottom, including the
# OFFLINE fixtures/tests in Sections 5-6. Last line: `ALL EVIDENCE CAPTURE CHECKS PASSED`. All
# fixture output goes to a throwaway temp directory (`tempfile.mkdtemp()`), never into the real
# `evidence/` folder -- so running this file never plants fake data next to real evidence.
#
# ## How the two helpers get used for real
# - **Discovery side**: after a real `notebooks/agent.ipynb`/`03_recorder.py` CAPTURE run produces
#   `events` and `compile_run(events, spec)` produces `{"login", "task", "report"}`, the project
#   owner calls `save_discovery_evidence(...)` once, by hand, in a new cell -- this file is never
#   exec'd into `03_recorder.py`'s own namespace (that notebook is owned, unmodified).
# - **Replay side**: `05_replay_live.py` loads this file's Sections 1-4 (definitions only) and
#   gains one new, opt-in `evidence_dir` parameter on its own `replay_live()` -- see the new cell
#   and the one-line diff to `replay_live` there. Default `evidence_dir=None` is byte-for-byte
#   today's behavior; nothing changes unless the project owner passes a path.

# %% Section 1: repo path, evidence root, and the Phase 2 schema (Capability/to_yaml/ReplayResult/Failure)
import json
import pathlib
import re
import tempfile


def _find_repo() -> pathlib.Path:
    here = pathlib.Path(globals().get("__file__", ".")).resolve()
    for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents, here.parent, *here.parents]:
        if (p / "notebooks" / "02_artifact_schema.py").exists():
            return p
    raise FileNotFoundError("cannot find notebooks/02_artifact_schema.py. Start the kernel in the repo.")


def _load_schema_once(wanted=("Section 1:", "Section 2:", "Section 2a:", "Section 3:", "Section 4:")) -> None:
    """Run the non-check model cells of the CURRENT Phase 2 notebook in this namespace -- the same
    technique 03_recorder.py's load_schema() and 04_replay_engine.py's load_schema() already use.
    A no-op when Capability/to_yaml/ReplayResult/Failure are already here (e.g. this file was
    loaded, definitions-only, from inside 05_replay_live.py, which loaded the schema itself first)
    -- avoids defining a second, redundant copy of the same Pydantic models in that namespace."""
    if all(name in globals() for name in ("Capability", "to_yaml", "ReplayResult", "Failure")):
        return
    text = (REPO / "notebooks" / "02_artifact_schema.py").read_text()
    for cell in re.split(r"(?m)^# %%", text)[1:]:
        header, _, body = cell.partition("\n")
        if header.strip().startswith(wanted):
            exec(compile(body, f"02_artifact_schema.py [{header.strip()}]", "exec"), globals())


REPO = globals().get("REPO") or _find_repo()
EX = REPO / "artifacts" / "examples"
EVIDENCE_ROOT = REPO / "evidence"
EVIDENCE_DISCOVERY_DIR = EVIDENCE_ROOT / "discovery"
EVIDENCE_REPLAY_DIR = EVIDENCE_ROOT / "replay"
_load_schema_once()
print("evidence_capture: schema ready:", Capability.__name__, ReplayResult.__name__, "| repo:", REPO.name)


# %% Section 2: the secret-value guard, shared by both helpers
class EvidenceWriteError(Exception):
    """Raised instead of writing anything, the same 'refuse, never partially write' shape
    save_capability (03_recorder.py) already uses for its own forbidden-value guard."""


def _assert_no_secret_values(text: str, secret_values: tuple[str, ...]) -> None:
    """D32: a secret VALUE must never be written anywhere; only its NAME may appear. In this
    codebase's actual data shapes that is already structural -- a captured `type_secret` event's
    own `value` field is the secret's NAME (see 03_recorder.py `_capture`'s
    `"type_secret": lambda kw: kw.get("name")`), and a replay `inputs` dict never contains a
    secret at all (secrets are resolved separately via `resolve_secret`, D32). `secret_values` is
    an explicit, optional defense-in-depth belt: real secret VALUES the caller knows about (e.g.
    read once from `.env` by a human, never by this file), checked against every blob about to be
    written, so a future bug that DID leak a raw value into an event or a result still cannot
    reach disk silently."""
    for v in secret_values:
        if v and v in text:
            raise EvidenceWriteError(
                "a secret VALUE would be written into evidence/. Nothing was saved. "
                "Only the secret's NAME belongs here (D32)."
            )


def _as_text(lines) -> str:
    text = lines if isinstance(lines, str) else "\n".join(str(x) for x in lines)
    return text if text.endswith("\n") or text == "" else text + "\n"


print("evidence_capture: secret-value guard ready")


# %% Section 3: discovery-side capture
def save_discovery_evidence(
    name: str,
    goal: str,
    events: list[dict],
    capability: "Capability",
    report: dict,
    transcript_lines,
    evidence_dir: pathlib.Path = EVIDENCE_DISCOVERY_DIR,
    *,
    login: "Capability | None" = None,
    secret_values: tuple[str, ...] = (),
) -> pathlib.Path:
    """Write one self-contained `evidence/discovery/<name>/` folder from an ALREADY-COMPLETED
    discovery run. Pure Python, no browser -- `events`, `capability` and `report` are exactly
    what a real discovery run already has in hand: `events` is 03_recorder.py CAPTURE's own
    in-memory list, `capability` is `compile_run(...)["task"]` (or `["login"]`, passed separately
    via `login=`), `report` is `compile_run(...)["report"]`. `transcript_lines` is the agent's own
    printed step-by-step output during discovery -- a list of lines, or one big string.

    Layout (one folder per run, `name` should be unique per run, e.g. include a date/time so a
    later run never silently overwrites an earlier one's evidence):
        <evidence_dir>/<name>/goal.txt
        <evidence_dir>/<name>/events.json
        <evidence_dir>/<name>/capability.yaml
        <evidence_dir>/<name>/login_capability.yaml   (only written when `login` is given)
        <evidence_dir>/<name>/compile_report.json
        <evidence_dir>/<name>/transcript.log

    Never overwrites `artifacts/*.yaml` -- `capability.yaml` here is always a fresh copy under
    `evidence/`, entirely separate from `save_capability`'s own output.

    Raises `EvidenceWriteError`, writing NOTHING, if any of `secret_values` (an explicit,
    optional defense-in-depth list -- see Section 2) appears anywhere in what would be written."""
    cap_yaml = to_yaml(capability)
    login_yaml = to_yaml(login) if login is not None else None
    events_json = json.dumps(events, indent=2, default=str)
    report_json = json.dumps(report, indent=2, default=str)
    transcript_text = _as_text(transcript_lines)
    goal_text = goal.rstrip("\n") + "\n"

    for blob in (goal_text, events_json, cap_yaml, login_yaml or "", report_json, transcript_text):
        _assert_no_secret_values(blob, secret_values)

    out = pathlib.Path(evidence_dir) / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "goal.txt").write_text(goal_text)
    (out / "events.json").write_text(events_json)
    (out / "capability.yaml").write_text(cap_yaml)
    if login_yaml is not None:
        (out / "login_capability.yaml").write_text(login_yaml)
    (out / "compile_report.json").write_text(report_json)
    (out / "transcript.log").write_text(transcript_text)
    return out


print("evidence_capture: save_discovery_evidence ready")


# %% Section 4: replay-side capture
def _default_label(result: "ReplayResult") -> str:
    """A readable folder-name suffix derived from the result's own status, when the caller
    doesn't give one explicitly (e.g. `error-slow-page`, to match a specific injected scenario)."""
    if result.status == "SUCCESS":
        return "success"
    if result.status == "BUSINESS_OUTCOME":
        return "business-" + (result.outcome or "outcome").lower().replace("_", "-")
    if result.status == "NEEDS_APPROVAL":
        return "needs-approval"
    return "failed"


def save_replay_evidence(
    cap: "Capability",
    inputs: dict[str, str],
    result: "ReplayResult",
    transcript_lines,
    evidence_dir: pathlib.Path = EVIDENCE_REPLAY_DIR,
    *,
    label: str | None = None,
    secret_values: tuple[str, ...] = (),
) -> pathlib.Path:
    """Write one self-contained `evidence/replay/<cap.name>-<label>/` folder from an
    ALREADY-COMPLETED replay run. Pure Python -- `cap`, `inputs`, and `result` are exactly what a
    real replay call already has: the loaded `Capability`, the plain (never-secret, D32) inputs
    dict passed to `run_capability`/`run_capability_async`, and the `ReplayResult` it returned.
    `transcript_lines` is the full printed log from that run (e.g. every `logger(...)` line
    `run_capability_async` already produces, plus the final `REPLAY RESULT: ...` line).

    `label` names the specific case (e.g. `"error-account-not-found"`); when omitted, one is
    derived from `result.status` (Section 4 `_default_label`) -- good enough for a single success
    run, but an explicit label is recommended for each of the five error demos so their folder
    names read as a checklist rather than all colliding on the same default (`FAILED` ->
    `<name>-failed` for every hard-failure case, for instance).

    Layout:
        <evidence_dir>/<cap.name>-<label>/capability.yaml
        <evidence_dir>/<cap.name>-<label>/inputs.json
        <evidence_dir>/<cap.name>-<label>/result.json
        <evidence_dir>/<cap.name>-<label>/transcript.log

    Raises `EvidenceWriteError`, writing NOTHING, under the same secret-value guard as
    `save_discovery_evidence` (Section 2)."""
    slug = label or _default_label(result)
    cap_yaml = to_yaml(cap)
    inputs_json = json.dumps(inputs, indent=2, default=str)
    result_json = json.dumps(result.model_dump(mode="json", exclude_none=True), indent=2, default=str)
    transcript_text = _as_text(transcript_lines)

    for blob in (cap_yaml, inputs_json, result_json, transcript_text):
        _assert_no_secret_values(blob, secret_values)

    out = pathlib.Path(evidence_dir) / f"{cap.name}-{slug}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "capability.yaml").write_text(cap_yaml)
    (out / "inputs.json").write_text(inputs_json)
    (out / "result.json").write_text(result_json)
    (out / "transcript.log").write_text(transcript_text)
    return out


print("evidence_capture: save_replay_evidence ready")

# %% [markdown]
# ## Offline fixtures and checks below (Sections 5-6)
# Everything from here down is test-only: hand-built fixtures shaped exactly like
# `03_recorder.py`'s own OFFLINE fixtures (discovery side) and `04_replay_engine.py`'s own
# hand-built `ReplayResult`s (replay side), written into a throwaway temp directory, never into
# the real `evidence/` folder. `05_replay_live.py`'s loader only pulls in Sections 1-4.

# %% Section 5: fixtures + checks for save_discovery_evidence
TMP = pathlib.Path(tempfile.mkdtemp(prefix="evidence_capture_test_"))

# Shaped exactly like 03_recorder.py's own `_e`/`_balance_events` fixtures (D75): a login
# (two type_secret calls -- `value` is the secret's NAME, "username"/"password", never a real
# secret value, matching 03_recorder.py `_capture`'s own `type_secret` wrapper), then a balance
# read. This is real fixture shape, not reinvented.
FAKE_EVENTS = [
    {"i": 0, "tool": "observe", "args": {}, "before": {"url": "/index.htm", "heading": "Customer Login"},
     "after": {"url": "/index.htm", "heading": "Customer Login"}, "message": "", "status": "ok"},
    {"i": 1, "tool": "type_secret", "args": {}, "value": "username",
     "before": {"url": "/index.htm", "heading": ""}, "after": {"url": "/index.htm", "heading": ""},
     "message": "Typed secret 'username' into [1].", "status": "ok"},
    {"i": 2, "tool": "type_secret", "args": {}, "value": "password",
     "before": {"url": "/index.htm", "heading": ""}, "after": {"url": "/index.htm", "heading": ""},
     "message": "Typed secret 'password' into [2].", "status": "ok"},
    {"i": 3, "tool": "click", "args": {"ref": 3}, "before": {"url": "/index.htm", "heading": "Customer Login"},
     "after": {"url": "/overview.htm", "heading": "Accounts Overview"}, "message": "Clicked [3].", "status": "ok"},
    {"i": 4, "tool": "extract_value", "args": {"label": "Total"}, "save_as": "balance",
     "before": {"url": "/overview.htm", "heading": "Accounts Overview"},
     "after": {"url": "/overview.htm", "heading": "Accounts Overview"}, "message": "Read 'Total'.", "status": "ok"},
    {"i": 5, "tool": "finish", "args": {}, "values": {"balance": "$1,200.00"},
     "before": {"url": "/overview.htm", "heading": ""}, "after": {"url": "/overview.htm", "heading": ""},
     "message": "Recorded. Stop now.", "status": "finish"},
]
FAKE_REPORT = {"dropped": [[0, "observe", "not an action"]], "constants": [], "warnings": []}
FAKE_GOAL = "Log in and read the balance of account 13344."
FAKE_TRANSCRIPT = [
    "[1] observe -> Customer Login",
    "[2] type_secret('username') -> Typed secret 'username' into [1].",
    "[3] type_secret('password') -> Typed secret 'password' into [2].",
    "[4] click([3]) -> Accounts Overview",
    "[5] extract_value('Total') -> balance",
    "AGENT SAID: Recorded. Stop now.",
]

# a real, unmodified example capability (read-only) stands in for compile_run(...)["task"]
FAKE_CAPABILITY = from_yaml((EX / "get_account_balance.yaml").read_text())

out1 = save_discovery_evidence(
    "20260926-fixture-balance", FAKE_GOAL, FAKE_EVENTS, FAKE_CAPABILITY, FAKE_REPORT, FAKE_TRANSCRIPT,
    evidence_dir=TMP / "discovery",
)
assert out1 == TMP / "discovery" / "20260926-fixture-balance"
for fname in ("goal.txt", "events.json", "capability.yaml", "compile_report.json", "transcript.log"):
    assert (out1 / fname).exists(), f"missing {fname}"
assert not (out1 / "login_capability.yaml").exists()   # no login= given
assert (out1 / "goal.txt").read_text() == FAKE_GOAL + "\n"
loaded_events = json.loads((out1 / "events.json").read_text())
assert loaded_events == FAKE_EVENTS
loaded_cap = from_yaml((out1 / "capability.yaml").read_text())
assert loaded_cap == FAKE_CAPABILITY
loaded_report = json.loads((out1 / "compile_report.json").read_text())
assert loaded_report == FAKE_REPORT
assert "AGENT SAID: Recorded. Stop now." in (out1 / "transcript.log").read_text()
print("save_discovery_evidence (happy path, no login): ok ->", out1)

# with a login capability too
out2 = save_discovery_evidence(
    "20260926-fixture-balance-with-login", FAKE_GOAL, FAKE_EVENTS, FAKE_CAPABILITY, FAKE_REPORT,
    FAKE_TRANSCRIPT, evidence_dir=TMP / "discovery",
    login=from_yaml((REPO / "artifacts" / "login_parabank.yaml").read_text()),
)
assert (out2 / "login_capability.yaml").exists()
assert from_yaml((out2 / "login_capability.yaml").read_text()).name == "login_parabank"
print("save_discovery_evidence (with login): ok ->", out2)

# secret-value NAME appears (as it must -- that's how a real event looks); never the VALUE
raw_text = (out1 / "events.json").read_text()
assert '"username"' in raw_text and '"password"' in raw_text            # names: fine, expected
assert "hunter2_the_real_password" not in raw_text                       # no such value was ever given

# defense-in-depth: simulate a hypothetical bug where a raw secret VALUE leaked into an event,
# and confirm the guard refuses the ENTIRE write -- no folder, no partial files -- rather than
# silently saving it. This is what "test this explicitly" means: prove the refusal fires and
# writes nothing, not just that the happy path never happens to contain a secret.
LEAKY_EVENTS = FAKE_EVENTS + [
    {"i": 6, "tool": "type_text", "args": {"ref": 9}, "value": "hunter2_the_real_password",
     "before": {"url": "/x", "heading": ""}, "after": {"url": "/x", "heading": ""}, "message": "", "status": "ok"},
]
leaky_target = TMP / "discovery" / "should-never-exist"
try:
    save_discovery_evidence(
        "should-never-exist", FAKE_GOAL, LEAKY_EVENTS, FAKE_CAPABILITY, FAKE_REPORT, FAKE_TRANSCRIPT,
        evidence_dir=TMP / "discovery", secret_values=("hunter2_the_real_password",),
    )
except EvidenceWriteError as err:
    assert "hunter2_the_real_password" not in str(err)     # even the error message never repeats the value
    print("save_discovery_evidence (secret-value guard): refused as expected:", err)
else:
    raise AssertionError("a leaked secret VALUE was NOT refused")
assert not leaky_target.exists(), "the guard must write NOTHING, not a partial folder"
print("save_discovery_evidence (secret-value guard): confirmed nothing was written")


# %% Section 6: fixtures + checks for save_replay_evidence
FAKE_XFER = from_yaml((REPO / "artifacts" / "transfer_funds.yaml").read_text())
FAKE_BAL = from_yaml((EX / "get_account_balance.yaml").read_text())


def _result(**kw) -> "ReplayResult":
    base = dict(run_id="fixture-run", capability=kw.pop("capability"), capability_version=1)
    return ReplayResult(**base, **kw)


# SUCCESS
r_success = _result(capability=FAKE_BAL.name, status="SUCCESS", outputs={"balance": "$1,200.00"})
out_success = save_replay_evidence(
    FAKE_BAL, {"account_id": "13344"}, r_success, ["step 0 (navigate): ok", "REPLAY RESULT: SUCCESS {'balance': '$1,200.00'}"],
    evidence_dir=TMP / "replay",
)
assert out_success.name == "get_account_balance-success"
assert json.loads((out_success / "result.json").read_text())["status"] == "SUCCESS"
assert json.loads((out_success / "inputs.json").read_text()) == {"account_id": "13344"}
print("save_replay_evidence (SUCCESS): ok ->", out_success)

# BUSINESS_OUTCOME
r_business = _result(capability=FAKE_BAL.name, status="BUSINESS_OUTCOME", outcome="ACCOUNT_NOT_FOUND")
out_business = save_replay_evidence(
    FAKE_BAL, {"account_id": "00000"}, r_business, "REPLAY RESULT: BUSINESS_OUTCOME ACCOUNT_NOT_FOUND\n",
    evidence_dir=TMP / "replay",
)
assert out_business.name == "get_account_balance-business-account-not-found"
print("save_replay_evidence (BUSINESS_OUTCOME, default label): ok ->", out_business)

# NEEDS_APPROVAL
r_approval = _result(capability=FAKE_XFER.name, status="NEEDS_APPROVAL", pending_step=3,
                      reason="amount 750.0 is at or above the auto-approve limit 500.0")
out_approval = save_replay_evidence(
    FAKE_XFER, {"amount": "750.00"}, r_approval, ["[escalate] amount 750.0 ...", "REPLAY RESULT: NEEDS_APPROVAL ..."],
    evidence_dir=TMP / "replay", label="error-transfer-over-limit",
)
assert out_approval.name == "transfer_funds-error-transfer-over-limit"
print("save_replay_evidence (NEEDS_APPROVAL, explicit label): ok ->", out_approval)

# FAILED
fake_failure = Failure(step_index=3, step_action="click", expected="button 'Transfer'", observed="no match")
r_failed = _result(capability=FAKE_XFER.name, status="FAILED", failure=fake_failure)
out_failed = save_replay_evidence(
    FAKE_XFER, {"amount": "100.00"}, r_failed, "REPLAY RESULT: FAILED ...\n",
    evidence_dir=TMP / "replay", label="error-element-missing",
)
assert out_failed.name == "transfer_funds-error-element-missing"
assert json.loads((out_failed / "result.json").read_text())["failure"]["step_action"] == "click"
print("save_replay_evidence (FAILED, explicit label): ok ->", out_failed)

# secret-value guard, replay side: inputs/result should never legitimately contain a secret value
# (D32: secrets are resolved separately, never through `inputs`) -- prove the guard still refuses
# if one ever showed up anyway (e.g. a future bug that put a raw secret into `reason`/`failure`).
r_leaky = _result(capability=FAKE_XFER.name, status="FAILED",
                   failure=Failure(step_index=1, step_action="type", expected="ok",
                                    observed="typed 'hunter2_the_real_password' unexpectedly"))
leaky_replay_target = TMP / "replay" / "should-never-exist-failed"
try:
    save_replay_evidence(
        FAKE_XFER, {"amount": "10.00"}, r_leaky, "irrelevant",
        evidence_dir=TMP / "replay", label="should-never-exist",
        secret_values=("hunter2_the_real_password",),
    )
except EvidenceWriteError as err:
    assert "hunter2_the_real_password" not in str(err)
    print("save_replay_evidence (secret-value guard): refused as expected:", err)
else:
    raise AssertionError("a leaked secret VALUE was NOT refused")
assert not leaky_replay_target.exists(), "the guard must write NOTHING, not a partial folder"
print("save_replay_evidence (secret-value guard): confirmed nothing was written")

print("\nfixture output written under (throwaway, not evidence/):", TMP)
print("ALL EVIDENCE CAPTURE CHECKS PASSED")
