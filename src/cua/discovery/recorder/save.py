"""Write a capability to disk (YAML + crops) and ask the model for its metadata (R11).

Moved from notebooks/discovery/discovery.py (``crops_for``, ``save_artifact``, ``describe``).
Two changes the migration asked for, no logic change: ``describe`` takes the model as a parameter
(it used the notebook's global ``MODEL``), and ``save_artifact`` defaults to the top-level
``artifacts/`` folder (``artifacts/<name>.yaml`` + ``artifacts/crops/<name>/``).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from langchain_core.language_models import BaseChatModel

from cua.discovery.recorder.build import used_inputs
from cua.discovery.recorder.events import step_events
from cua.schema import Capability, CapabilityMeta, Event


def crops_for(log: list[Event], cap: Capability) -> dict[str, bytes]:
    pairs = zip(step_events(log), cap.steps, strict=False)
    return {
        s.target.template: ev["crop"]  # type: ignore[misc,union-attr]
        for ev, s in pairs
        if getattr(s, "target", None) and s.target.template  # type: ignore[union-attr]
    }


def save_artifact(
    cap: Capability, crops: dict[str, bytes], out_dir: Path = Path("artifacts")
) -> Path:
    path = Path(out_dir) / f"{cap.name}.yaml"
    for rel, png in crops.items():
        (Path(out_dir) / rel).parent.mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / rel).write_bytes(png)
    path.write_text(yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False))
    Capability.model_validate(yaml.safe_load(path.read_text()))  # what replay will load
    return path


async def describe(goal: str, log: list[Event], model: BaseChatModel) -> CapabilityMeta:
    """R11: name, description, input descriptions, success text. Labels only, no values."""
    lines = [f"{ev['tool']} {ev.get('label') or ev.get('text') or ''}" for ev in step_events(log)]
    names = used_inputs(log)
    tables, options = (
        list(dict.fromkeys(ev["args"]["save_as"] for ev in step_events(log) if ev["tool"] == t))
        for t in ("extract_table", "extract_options")
    )
    prompt = (
        f"Goal: {goal}\nSteps (tool, field label):\n"
        + "\n".join(lines)
        + f"\nInputs a caller fills in: {', '.join(names) or 'none'}.\n"
        f"Tables it returns (rows): {', '.join(tables) or 'none'}.\n"  # type: ignore[arg-type]
        f"Option lists it returns: {', '.join(options) or 'none'}.\n"  # type: ignore[arg-type]
        "You write ONLY metadata for this recorded capability; the steps are already fixed.\n"
        "- name: snake_case verb_object named after the GOAL, what the caller gets done (e.g. "
        "get_account_balance), not the pages it passes through.\n"
        "- description: 1-2 sentences on what the capability does and what it returns.\n"
        "- inputs: a map from EXACTLY those input names to one line on what the caller must "
        "supply, never an example value (no other keys; secrets such as the login are not "
        "inputs).\n"
        "- success_text: text shown on the final screen before logout that proves success, "
        "never a value.\n"
        "NEVER include a value from the goal or the screen (an account number, amount, name) "
        "anywhere."
    )
    return await model.with_structured_output(CapabilityMeta).ainvoke(prompt)  # type: ignore[return-value]
