"""Write a capability to disk (YAML + crops) and ask the model for its metadata (R11).

Moved from notebooks/discovery/discovery.py (``crops_for``, ``save_artifact``, ``describe``).
Two changes the migration asked for, no logic change: ``describe`` takes the model as a parameter
(it used the notebook's global ``MODEL``), and ``save_artifact`` defaults to the top-level
``artifacts/`` folder (``artifacts/<name>.yaml`` + ``artifacts/crops/<name>/``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml
from langchain_core.language_models import BaseChatModel

from cua.discovery.recorder.build import used_inputs
from cua.discovery.recorder.events import NotSaved, step_events
from cua.safety.redact import IdMask, OcrFn, mask_png
from cua.schema import Capability, CapabilityMeta, Event

TEXT_KEYS = {
    "name",
    "description",
    "label",
    "text",
    "option",
    "value",
    "checkpoint",
    "row_key",
    "column",
    "save_as",
    "columns",
}  # where a typed value could hide
NAME_KEYS = {"name", "save_as", "template"}  # names and paths: an id keeps its digits, no stars


@dataclass(frozen=True)
class ArtifactMask:
    """How a capability is cleaned before it is written: account ids down to their last digits
    (text, names, crops), then a refusal if any run value is still in a text field. ``redact``
    masks the run's values; ``ocr_fn`` reads the crops (None: crops are written as they are)."""

    ids: IdMask
    redact: Callable[[str], str]
    ocr_fn: OcrFn | None = None


def artifact_texts(yml: str) -> list[str]:
    """The artifact's free-text fields only. Structural numbers (``version: 1``, a viewport, an
    offset, ``s1.png``) are not values a person typed, and a one-character form value such as
    '1' matches them, so the whole-file check refused clean artifacts."""
    out: list[str] = []

    def walk(node: object, key: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, str(k))
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
        elif key in TEXT_KEYS and isinstance(node, str):
            out.append(node)

    walk(yaml.safe_load(yml) if yml.strip() else {})
    return out


def _mask_ids(node: object, ids: IdMask, key: str = "") -> object:
    if isinstance(node, dict):
        return {k: _mask_ids(v, ids, str(k)) for k, v in node.items()}
    if isinstance(node, list):
        return [_mask_ids(v, ids, key) for v in node]
    if isinstance(node, str) and key in TEXT_KEYS | NAME_KEYS:
        return ids.name(node) if key in NAME_KEYS else ids(node)
    return node


def masked(cap: Capability, mask: ArtifactMask) -> Capability:
    """The capability with every account id cut to its last digits; NotSaved if a run value is
    still in one of its text fields (checked before anything is written)."""
    data = _mask_ids(cap.model_dump(mode="json", exclude_none=True), mask.ids)
    out = Capability.model_validate(data)
    yml = yaml.safe_dump(data, sort_keys=False)
    if leaked := [t for t in artifact_texts(yml) if mask.redact(t) != t]:
        raise NotSaved(f"a run value is in the artifact ({len(leaked)} text field(s)).")
    return out


def crops_for(log: list[Event], cap: Capability) -> dict[str, bytes]:
    pairs = zip(step_events(log), cap.steps, strict=False)
    return {
        s.target.template: ev["crop"]  # type: ignore[misc,union-attr]
        for ev, s in pairs
        if getattr(s, "target", None) and s.target.template  # type: ignore[union-attr]
    }


def save_artifact(
    cap: Capability,
    crops: dict[str, bytes],
    out_dir: Path = Path("artifacts"),
    mask: ArtifactMask | None = None,
) -> Path:
    """``<out_dir>/<name>.yaml`` + its crops. With ``mask``: ids cut to their last digits and a
    run value refused (NotSaved) BEFORE any file is written."""
    if mask is not None:
        cap = masked(cap, mask)
        crops = {mask.ids.name(rel): _crop(png, mask) for rel, png in crops.items()}
    path = Path(out_dir) / f"{cap.name}.yaml"
    for rel, png in crops.items():
        (Path(out_dir) / rel).parent.mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / rel).write_bytes(png)
    path.write_text(yaml.safe_dump(cap.model_dump(mode="json", exclude_none=True), sort_keys=False))
    Capability.model_validate(yaml.safe_load(path.read_text()))  # what replay will load
    return path


def _crop(png: bytes, mask: ArtifactMask) -> bytes:
    return mask_png(png, mask.redact, mask.ocr_fn, mask.ids) if mask.ocr_fn else png


async def describe(
    goal: str, log: list[Event], model: BaseChatModel, ids: IdMask | None = None
) -> CapabilityMeta:
    """R11: name, description, input descriptions, success text. Labels only, no values. With
    ``ids``, the goal and the step lines reach the model with every account id cut."""
    cut = ids or (lambda text: text)
    goal = cut(goal)
    lines = [
        cut(f"{ev['tool']} {ev.get('label') or ev.get('text') or ''}") for ev in step_events(log)
    ]
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
