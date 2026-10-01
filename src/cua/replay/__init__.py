"""Replay: runs a capability saved by discovery with plain code, no LLM (step 4: loading the
artifact and locating a target only; later steps add the step actions, the walk, and recovery)."""

from cua.replay.loader import (
    PLACEHOLDER,
    fill,
    given_inputs,
    load_capability,
    load_outcomes,
    secret_name,
    seen_outcome,
    step_inputs,
)
from cua.replay.locate import (
    anchor_point,
    find_template,
    find_text,
    locate,
    read_cell,
    same_label,
    same_text,
    text_hit,
    typed_ok,
)

__all__ = [
    "PLACEHOLDER",
    "anchor_point",
    "fill",
    "find_template",
    "find_text",
    "given_inputs",
    "load_capability",
    "load_outcomes",
    "locate",
    "read_cell",
    "same_label",
    "same_text",
    "secret_name",
    "seen_outcome",
    "step_inputs",
    "text_hit",
    "typed_ok",
]
