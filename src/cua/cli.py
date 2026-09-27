"""The `cua` command: `cua discover "<goal>"` and `cua replay <capability.yaml>`.

`cua discover` needs a real browser and a real `ANTHROPIC_API_KEY` -- it runs the actual
discovery agent (`cua.agent`) against ParaBank, wraps every tool call into an **event** (the same
shape `notebooks/03_recorder.py`'s CAPTURE half produces), and compiles the recording into a
`Capability` via `cua.recorder.compile_run`. The event-capture wrapping and the three
recorder-only tools (`extract_value`, `open_path`, `finish_business_outcome`) live in THIS module,
not in `cua.recorder` -- `cua.recorder` stays pure Python with no Playwright import (a hard
requirement of this port), and the CAPTURE half stays exactly what CLAUDE.md's own Phase 3 notes
call it: agent-side code, orchestrated by the caller, not an independent importable API.

`cua replay` needs a real browser but NO API key -- replay has no LLM, only Playwright and `.env`
for secrets (D6, D32).
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from cua import agent as agent_mod
from cua import recorder
from cua.config import BASE, host_allowed


# ---------------------------------------------------------------------------
# `cua discover`: the CAPTURE-half glue (agent-side, per CLAUDE.md's own Phase 3 scoping note).
# ---------------------------------------------------------------------------
def _first_line(result) -> str:
    """The tool's own status text: the first text block of a list result, or the plain string a
    str-returning tool (page_text, finish, finish_business_outcome) gives back directly."""
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"].split("\n", 1)[0]
        return ""
    return str(result).split("\n", 1)[0]


async def _current_heading(page) -> str:
    try:
        return await page.evaluate(agent_mod.HEADING_JS)
    except Exception:
        return ""


async def _describe_ref(page, ref) -> dict | None:
    try:
        return await page.evaluate(agent_mod.DESCRIBE_JS, ref)
    except Exception:
        return None


def _new_tools(agent: agent_mod.DiscoveryAgent):
    """The three additive tools the recorder's compiler needs (D73), ported from
    `03_recorder.py` BROWSER 9, operating on `agent` instead of module globals."""
    from langchain.tools import tool

    @tool(parse_docstring=True)
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
        res = await agent.page.evaluate(agent_mod.READ_LABELED_JS, label)
        if not res["value"]:
            return agent._blocks(f"FAILED to read '{label}': no value found next to that label.", await agent.surface.observe())
        if not recorder.value_matches_type(res["value"], value_type):
            return agent._blocks(f"FAILED to read '{label}': the value does not look like a {value_type}.", await agent.surface.observe())
        return agent._blocks(f"Read '{label}'.", await agent.surface.observe())

    @tool(parse_docstring=True)
    async def open_path(path: str) -> list:
        """Navigate directly to a page on this site by its path, when no link on the page goes there.

        Only use this for a path whose query values come from the user's goal. Never invent a value.

        Args:
            path: A path starting with '/', e.g. '/activity.htm?id=13344'. Every value in it must
                come from the goal.

        Returns:
            The new page state.
        """
        if any(w in path.lower() for w in agent_mod.DENY_LINKS):
            return agent._blocks(f"DENIED: '{path}' is not allowed.", await agent.surface.observe())
        values = [v for _, v in parse_qsl(urlparse(path).query)]
        if any(v.strip().lower() not in agent.given_text.lower() for v in values):
            return agent._blocks(
                f"REFUSED: '{path}' has a value not given in the goal. Only open a path whose values you were given.",
                await agent.surface.observe(),
            )
        url = f"{BASE}{path}"
        if not host_allowed(url):
            return agent._blocks("REFUSED: this path is not on the allowed site.", await agent.surface.observe())
        try:
            await agent.page.goto(url)
        except Exception as exc:
            return agent._blocks(f"FAILED to open '{path}': {type(exc).__name__}", await agent.surface.observe())
        return agent._blocks(f"Opened {path}.", await agent.surface.observe())

    @tool(parse_docstring=True)
    async def finish_business_outcome(outcome: str, proof_text: str) -> str:
        """Report that this run hit a known business outcome (e.g. a bad account id), not a normal
        task result. Only call this INSTEAD of finish() when the page shows a message that proves a
        declared bad-input scenario, such as 'could not find account'.

        Args:
            outcome: Short UPPER_SNAKE name for what happened, e.g. ACCOUNT_NOT_FOUND.
            proof_text: The exact sentence from the page that proves this outcome. Copy it exactly
                from the page.

        Returns:
            A confirmation, or a refusal if proof_text is not really on the page. Stop after this.
        """
        text = await agent.surface.page_text()
        if proof_text not in text:
            return "REFUSED: that exact text was not found on the current page. Re-read the page and copy it exactly."
        agent.result.clear()
        agent.result.update({"summary": f"PROBE: {outcome}", "values": {}, "outcome": outcome, "proof_text": proof_text})
        return "Recorded as a business-outcome probe. Stop now."

    return extract_value, open_path, finish_business_outcome


def _capture(tool_obj, agent, events, *, value_of=lambda kwargs: None) -> None:
    """Replace tool_obj.coroutine with a wrapper that logs an event AROUND the ORIGINAL call.
    Ported from `03_recorder.py` BROWSER 10's `_capture`."""
    original = tool_obj.coroutine

    async def wrapped(**kwargs):
        before_url, before_heading = agent.page.url, await _current_heading(agent.page)
        ref = kwargs.get("ref")
        el = await _describe_ref(agent.page, ref) if ref is not None else None
        was_risky = agent.needs_human(ref) if (ref is not None and tool_obj.name == "click") else False
        result = await original(**kwargs)
        message = _first_line(result)
        status = recorder.classify_status(message)
        events.append({
            "i": len(events), "tool": tool_obj.name, "args": dict(kwargs),
            "message": message, "status": status,
            "before": {"url": recorder.norm_url(before_url), "heading": before_heading},
            "after": {"url": recorder.norm_url(agent.page.url), "heading": await _current_heading(agent.page)},
            "approved": bool(was_risky and status == "ok"),
            "el": el, "value": value_of(kwargs),
        })
        return result

    tool_obj.coroutine = wrapped


def _wrap_extract_value(tool_obj, agent, events) -> None:
    original = tool_obj.coroutine

    async def wrapped(label: str, save_as: str, value_type: str, description: str):
        before_url, before_heading = agent.page.url, await _current_heading(agent.page)
        res = await agent.page.evaluate(agent_mod.READ_LABELED_JS, label)   # label_count only -- the VALUE is never logged
        result = await original(label=label, save_as=save_as, value_type=value_type, description=description)
        message = _first_line(result)
        events.append({
            "i": len(events), "tool": "extract_value", "args": {"label": label, "save_as": save_as, "value_type": value_type},
            "message": message, "status": recorder.classify_status(message),
            "before": {"url": recorder.norm_url(before_url), "heading": before_heading},
            "after": {"url": recorder.norm_url(agent.page.url), "heading": await _current_heading(agent.page)},
            "approved": False, "el": None,
            "label": label, "save_as": save_as, "value_type": value_type, "description": description,
            "label_count": res.get("matches", 1),
        })
        return result

    tool_obj.coroutine = wrapped


def _wrap_finish(tool_obj, agent, events) -> None:
    original = tool_obj.coroutine

    async def wrapped(summary: str, values: dict):
        result = await original(summary=summary, values=values)
        events.append({
            "i": len(events), "tool": "finish", "args": {}, "message": result, "status": recorder.classify_status(result),
            "before": {"url": recorder.norm_url(agent.page.url), "heading": ""},
            "after": {"url": recorder.norm_url(agent.page.url), "heading": ""},
            "approved": False, "el": None, "summary": summary, "values": values,
        })
        return result

    tool_obj.coroutine = wrapped


def _wrap_finish_business_outcome(tool_obj, agent, events) -> None:
    original = tool_obj.coroutine

    async def wrapped(outcome: str, proof_text: str):
        before_url, before_heading = agent.page.url, await _current_heading(agent.page)
        result = await original(outcome=outcome, proof_text=proof_text)
        status = "ok" if result.startswith("Recorded") else "failed"
        events.append({
            "i": len(events), "tool": "finish_business_outcome", "args": {},
            "message": result, "status": status,
            "before": {"url": recorder.norm_url(before_url), "heading": before_heading},
            "after": {"url": recorder.norm_url(agent.page.url), "heading": await _current_heading(agent.page)},
            "approved": False, "el": None,
            "outcome": outcome if status == "ok" else None,
            "proof": proof_text if status == "ok" else None,
        })
        return result

    tool_obj.coroutine = wrapped


def _wrap_request_value(tool_obj, agent, events) -> None:
    """D82: request_value gets its OWN wrapper -- a handoff through it opens a KNOWN, specific
    ref, so `synthesize_human_entries` can turn what ended up in that field into a proper step."""
    original = tool_obj.coroutine

    async def wrapped(ref: int, hint: str):
        before_url, before_heading = agent.page.url, await _current_heading(agent.page)
        el = await _describe_ref(agent.page, ref)
        result = await original(ref=ref, hint=hint)
        message = _first_line(result)
        status = recorder.classify_status(message)
        after_url, after_heading = agent.page.url, await _current_heading(agent.page)
        events.append({
            "i": len(events), "tool": "request_value", "args": {"ref": ref, "hint": hint},
            "message": message, "status": status,
            "before": {"url": recorder.norm_url(before_url), "heading": before_heading},
            "after": {"url": recorder.norm_url(after_url), "heading": after_heading},
            "approved": False, "el": el, "value": None,
        })
        if status == "handoff":
            entered = await agent.current_value(ref)
            events.extend(recorder.synthesize_human_entries(
                len(events), recorder.norm_url(before_url), before_heading,
                recorder.norm_url(after_url), after_heading,
                [{"ref": ref, "el": el, "value_after": entered}],
            ))
        return result

    tool_obj.coroutine = wrapped


def _wrap_request_missing_values(tool_obj, agent, events) -> None:
    original = tool_obj.coroutine

    async def wrapped(hints: dict | None = None):
        hints = hints or {}
        before_url, before_heading = agent.page.url, await _current_heading(agent.page)
        missing = agent_mod.missing_field_labels(agent.surface.last_elements, hints)
        els = {ref: await _describe_ref(agent.page, ref) for ref, _label in missing}
        result = await original(hints=hints)
        message = _first_line(result)
        status = recorder.classify_status(message)
        after_url, after_heading = agent.page.url, await _current_heading(agent.page)
        events.append({
            "i": len(events), "tool": "request_missing_values", "args": {"hints": dict(hints)},
            "message": message, "status": status,
            "before": {"url": recorder.norm_url(before_url), "heading": before_heading},
            "after": {"url": recorder.norm_url(after_url), "heading": after_heading},
            "approved": False, "el": None, "value": None,
        })
        if status == "handoff":
            entries = [{"ref": ref, "el": els[ref], "value_after": await agent.current_value(ref)} for ref, _label in missing]
            events.extend(recorder.synthesize_human_entries(
                len(events), recorder.norm_url(before_url), before_heading,
                recorder.norm_url(after_url), after_heading, entries,
            ))
        return result

    tool_obj.coroutine = wrapped


_VALUE_OF = {
    "type_text": lambda kw: kw.get("text"),
    "type_secret": lambda kw: kw.get("name"),       # the secret NAME, never its value
    "select_option": lambda kw: kw.get("option"),
}
_SPECIAL_WRAPPED = {"finish", "request_value", "request_missing_values", "extract_value", "finish_business_outcome"}

RECORDER_SYSTEM_PROMPT = agent_mod.SYSTEM_PROMPT.replace(
    "- finish(summary, values): report the result, logout and then stop.\n",
    "- extract_value(label, save_as, value_type, description): read one specific value shown next"
    " to a label (e.g. 'Balance:') and record it as an output. Use this, not page_text, when the"
    " task asks you to report a specific value by name.\n"
    "- open_path(path): go directly to a page on this site by its path, when no link on the page"
    " goes there. Every value in the path must come from the goal.\n"
    "- finish_business_outcome(outcome, proof_text): call this INSTEAD of finish when the page"
    " shows a message proving a bad-input outcome the goal asked you to find (e.g. an account"
    " that does not exist). proof_text must be copied exactly from the page.\n"
    "- finish(summary, values): report the result, logout and then stop.\n",
)


def _build_capture(agent: agent_mod.DiscoveryAgent) -> tuple[list, list[dict]]:
    """Build the full CAPTURE-mode tool list (the base discovery tools plus the recorder's own
    additive tools) and wire event logging onto every one of them. Returns (tools, events) --
    `events` is mutated in place as the agent runs; read it after the run finishes."""
    events: list[dict] = []
    base_tools = agent.build_tools()
    extract_value, open_path, finish_business_outcome = _new_tools(agent)
    all_tools = [*base_tools, extract_value, open_path, finish_business_outcome]

    for t in all_tools:
        if t.name in _SPECIAL_WRAPPED:
            continue
        _capture(t, agent, events, value_of=_VALUE_OF.get(t.name, lambda kw: None))

    by_name = {t.name: t for t in all_tools}
    _wrap_extract_value(by_name["extract_value"], agent, events)
    _wrap_finish(by_name["finish"], agent, events)
    _wrap_finish_business_outcome(by_name["finish_business_outcome"], agent, events)
    _wrap_request_value(by_name["request_value"], agent, events)
    _wrap_request_missing_values(by_name["request_missing_values"], agent, events)

    return all_tools, events


def _infer_input_type(value: str) -> str:
    if re.fullmatch(r"\$?[0-9]+\.[0-9]{2}", value):
        return "currency"
    if re.fullmatch(r"-?[0-9]+", value):
        return "integer"
    return "string"


async def _run_discover(args: argparse.Namespace) -> int:
    agent_run = await agent_mod.build_agent(goal_text=args.goal, auto_limit=args.auto_approve_limit)
    tools, events = _build_capture(agent_run)
    lc_agent = agent_mod.build_langchain_agent(tools, system_prompt=RECORDER_SYSTEM_PROMPT)

    import uuid

    cfg = {"configurable": {"thread_id": f"discover-{uuid.uuid4().hex[:6]}"}, "recursion_limit": 100}
    out = await lc_agent.ainvoke({"messages": [{"role": "user", "content": args.goal}]}, config=cfg)
    print("AGENT SAID:", out["messages"][-1].content)
    print(f"captured {len(events)} events")

    spec_inputs = {}
    for pair in args.input or []:
        name, _, value = pair.partition("=")
        spec_inputs[name] = {
            "value": value, "type": _infer_input_type(value),
            "description": f"The value for {name}.",
            "pattern": r"^.{1,80}$",
        }
    spec = {"name": args.name, "description": args.description or args.goal, "inputs": spec_inputs}

    try:
        result = recorder.compile_run(events, spec)
    except recorder.CompileError as err:
        if "It is a probe" in str(err):
            print("This run ended with a business outcome, not a completed task -- it is a probe, not a capability.")
            print("Problems:", err.problems)
            return 1
        print("Could not compile a capability from this run:")
        for p in err.problems:
            print(" -", p)
        return 1

    recorder.show(result)
    out_dir = args.output.parent if args.output else recorder.ARTIFACTS
    name_override = args.output.stem if args.output else None
    if result["login"]:
        print("saved:", recorder.save_capability(result["login"], out_dir=out_dir))
    task_path = recorder.save_capability(result["task"], out_dir=out_dir)
    if name_override and name_override != result["task"].name:
        task_path = task_path.rename(task_path.with_name(f"{name_override}.yaml"))
    print("saved:", task_path)
    return 0


# ---------------------------------------------------------------------------
# `cua replay`: no LLM, no API key -- Playwright + `.env` for secrets only (D6, D32).
# ---------------------------------------------------------------------------
async def _run_replay(args: argparse.Namespace) -> int:
    from cua import live

    agent_run = await agent_mod.build_agent()
    inputs = {}
    for pair in args.input or []:
        name, _, value = pair.partition("=")
        inputs[name] = value

    result = await live.replay_live(args.capability, inputs, agent_run, auto_approve_limit=args.auto_approve_limit)
    print(result.model_dump_json(indent=2))
    return 0 if result.status in ("SUCCESS", "BUSINESS_OUTCOME") else 1


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cua", description="Computer-use automation: discover a capability, replay it deterministically.")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="Run the discovery agent against a goal and compile a capability YAML (needs a real browser + ANTHROPIC_API_KEY).")
    discover.add_argument("goal", help="The goal text, e.g. 'Log in and read the balance of account 14232.'")
    discover.add_argument("--name", required=True, help="Capability name (lower_snake_case), e.g. get_account_balance.")
    discover.add_argument("--description", default=None, help="Capability description. Defaults to the goal text.")
    discover.add_argument("--input", action="append", metavar="key=value",
                           help="Declare an input the goal references, e.g. --input account_id=14232. Repeatable.")
    discover.add_argument("--output", type=Path, default=None, help="Where to save the compiled YAML. Defaults to artifacts/<name>.yaml.")
    discover.add_argument("--auto-approve-limit", type=float, default=None,
                           help="Dollar amount at/under which a risky 'transfer' click needs no human during discovery. Default: always ask.")
    discover.set_defaults(func=_run_discover)

    replay = sub.add_parser("replay", help="Replay a saved capability YAML against the real browser (no LLM, no API key needed).")
    replay.add_argument("capability", type=Path, help="Path to a capability YAML, e.g. artifacts/get_account_balance.yaml.")
    replay.add_argument("--input", action="append", metavar="key=value",
                         help="A declared input's value, e.g. --input account_id=14232. Repeatable. Missing required inputs are prompted for interactively.")
    replay.add_argument("--auto-approve-limit", type=float, default=500.0,
                         help="Dollar amount at/under which a risky click proceeds without a human. Default: 500.0.")
    replay.set_defaults(func=_run_replay)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
