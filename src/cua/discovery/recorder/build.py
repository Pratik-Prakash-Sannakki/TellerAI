"""Event log -> ``Capability``: steps, inputs, outputs and secrets come from the log only (R12).

Moved unchanged from notebooks/discovery/discovery.py (``target`` .. ``output``).
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlparse

from cua.discovery.recorder.checkpoint import checkpoint
from cua.discovery.recorder.events import (
    READ_TOOLS,
    NotSaved,
    input_name,
    is_select,
    step_events,
    succeeded,
)
from cua.discovery.recorder.types import input_types
from cua.schema import (
    Anchor,
    Capability,
    CapabilityMeta,
    Click,
    Event,
    Extract,
    ExtractOptions,
    ExtractTable,
    Header,
    Input,
    Navigate,
    OcrText,
    Output,
    Scroll,
    Select,
    Step,
    TableCell,
    Target,
    Type,
)


def target(ev: Event, template: str) -> Target:
    a, own = ev.get("anchor"), ev.get("own")
    return Target(
        ocr_text=OcrText(text=own["text"], ordinal=own["ordinal"]) if own else None,  # type: ignore[arg-type]
        anchor=Anchor(label=a["text"], ordinal=a["ordinal"], offset=ev["offset"]) if a else None,  # type: ignore[arg-type]
        template=template if ev.get("crop") else None,
    )


def to_step(ev: Event, template: str) -> Step:  # noqa: PLR0911
    tool, args, name = (
        ev["tool"],
        ev["args"],
        input_name(ev.get("label") or ev["args"].get("hint", "")),  # type: ignore[arg-type]
    )
    if tool == "open_path":  # query values come from the goal, so each becomes an input
        return _navigate(ev)
    if tool == "scroll":
        return Scroll(direction=args["direction"])  # type: ignore[arg-type]
    if tool == "extract_value":
        cell = ev.get("table")
        return Extract(
            save_as=args["save_as"],  # type: ignore[arg-type]
            pattern=ev.get("pattern"),
            target=(
                Target(table_cell=TableCell(**cell))  # type: ignore[arg-type]
                if cell
                else target({**ev, "crop": None}, template)
            ),  # its crop shows the value
        )
    if tool == "extract_table":
        return ExtractTable(
            header=Header(
                label=args["columns"][0], ordinal=(ev.get("header") or {}).get("ordinal", 1)  # type: ignore[arg-type,index,union-attr]
            ),
            columns=args["columns"],  # type: ignore[arg-type]
            save_as=args["save_as"],  # type: ignore[arg-type]
            row_limit=args["row_limit"],  # type: ignore[arg-type]
        )
    if tool == "extract_options":  # found like a select: its label, never an option
        return ExtractOptions(
            target=target(ev, template), save_as=args["save_as"], index=ev.get("index")  # type: ignore[arg-type]
        )
    if tool == "click":
        return Click(target=target(ev, template), cleanup=bool(ev.get("cleanup")))
    if tool == "select_option" or (tool == "request_value" and ev.get("dropdown")):
        return Select(target=target(ev, template), option=f"{{{{{name}}}}}", index=ev.get("index"))
    value = f"{{{{secret:{args['secret_name']}}}}}" if tool == "type_secret" else f"{{{{{name}}}}}"
    return Type(target=target(ev, template), value=value)


def _navigate(ev: Event) -> Navigate:
    """``to_step``'s open_path branch, unchanged."""
    args = ev["args"]
    url = urlparse(
        ev.get("path", "/" + args["path"].lstrip("/"))  # type: ignore[union-attr]
        + ("?" + urlparse(args["path"]).query if urlparse(args["path"]).query else "")  # type: ignore[arg-type,operator]
    )
    query = "&".join(f"{k}={{{{{input_name(k)}}}}}" for k, _ in parse_qsl(url.query))
    return Navigate(path=url.path + (f"?{query}" if query else ""))


def step_inputs(steps: list[Step]) -> list[str]:
    """The {{input}} names the steps use, in order. {{secret:x}} is not an input."""
    used = [
        getattr(s, "value", None) or getattr(s, "option", None) or getattr(s, "path", "")
        for s in steps
    ]
    return list(dict.fromkeys(m for u in used for m in re.findall(r"\{\{(\w+)\}\}", u)))  # type: ignore[arg-type]


def used_inputs(log: list[Event]) -> list[str]:
    return step_inputs([to_step(ev, "crop.png") for ev in step_events(log)])


def build_capability(log: list[Event], meta: CapabilityMeta) -> Capability:
    """Steps, inputs and secrets come from the log only. The model's text cannot fail the build."""
    start = next(ev["args"] for ev in log if ev["tool"] == "start")
    events, name = step_events(log), input_name(meta.name)
    _refuse(log, events)
    steps = [to_step(ev, f"crops/{name}/s{i}.png") for i, ev in enumerate(events)]
    _check_login_order(steps)
    names, types = step_inputs(steps), input_types(succeeded(log))  # every value, retries too
    return Capability(
        name=name,
        description=meta.description,
        base_url=start["base_url"],  # type: ignore[arg-type]
        viewport=start["viewport"],  # type: ignore[arg-type]
        device_scale_factor=start["device_scale_factor"],  # type: ignore[arg-type]
        inputs=[
            Input(
                name=n,
                type=types.get(n, "string"),
                description=meta.inputs.get(n) or n.replace("_", " "),
            )
            for n in names
        ],
        outputs=[output(ev) for ev in events if ev["tool"] in READ_TOOLS],
        secrets=list(
            dict.fromkeys(ev["args"]["secret_name"] for ev in events if ev["tool"] == "type_secret")  # type: ignore[misc]
        ),
        steps=steps,
        checkpoint=checkpoint(log, meta.success_text),
    )


def _check_login_order(steps: list[Step]) -> None:
    """Every secret is typed before the first click (the login). Replay clicking Log In on empty
    boxes fails on the site's error page, so a capability in that order is never saved."""
    clicks = [i for i, s in enumerate(steps) if s.action == "click"]
    secrets = [i for i, s in enumerate(steps) if "{{secret:" in (getattr(s, "value", "") or "")]
    if clicks and secrets and max(secrets) > clicks[0]:
        raise NotSaved(
            "the login steps are out of order (a secret is typed after the first click). "
            "Re-run discovery."
        )


def check_savable(log: list[Event]) -> None:
    """Raise NotSaved before any model call when this run cannot become a capability."""
    _refuse(log, step_events(log))


def _refuse(log: list[Event], events: list[Event]) -> None:
    """``build_capability``'s refusals, unchanged: a leaked value, a blind dropdown, no outcome."""
    if leaks := [i for i, ev in enumerate(events) if ev.get("leak")]:
        raise NotSaved(
            f"steps {leaks}: a label or target text is a value typed this run. "
            "Not saved (it would store the value). Re-run discovery."
        )
    if blind := [i for i, ev in enumerate(events) if is_select(ev) and not ev.get("anchor")]:
        raise NotSaved(
            f"steps {blind}: a dropdown with no label to find it by (only its crop). "
            "Not saved (replay would guess between dropdowns). Re-run discovery."
        )
    if not any(ev["tool"] == "send" for ev in log) and not any(
        ev["tool"] in READ_TOOLS for ev in events
    ):
        raise NotSaved(
            "nothing was read or sent: re-run and save the values with extract_value "
            "(a table: extract_table; a dropdown's options: extract_options). "
            "Not saved (a caller would get SUCCESS with no data)."
        )


def output(ev: Event) -> Output:
    a = ev["args"]
    if ev["tool"] == "extract_table":
        return Output(
            name=a["save_as"], type="table", description=a["description"], columns=a["columns"]  # type: ignore[arg-type]
        )
    if ev["tool"] == "extract_options":  # a list of the dropdown's option texts
        return Output(name=a["save_as"], type="options", description=a["description"])  # type: ignore[arg-type]
    return Output(name=a["save_as"], type=a["value_type"], description=a["description"])  # type: ignore[arg-type]
