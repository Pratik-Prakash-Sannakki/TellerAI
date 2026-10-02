"""The prompts are the first filter (user, 2026-09-30); the models and code checks are the second.
These rules must never be dropped by a later edit. Ported from tests/discovery/test_prompt_rules.py
(now against cua.discovery.agent.prompt and cua.discovery.recorder.save.describe)."""

from __future__ import annotations

import ast
import hashlib
import inspect

from cua.discovery.agent.prompt import PROMPT_VERSION, VISUAL_SYSTEM_PROMPT
from cua.discovery.recorder import save
from cua.discovery.tools import build_tools
from tests.fakes import make_ctx
from tests.unit._snapshots import DISCOVERY as SNAP_DISCOVERY

SRC = SNAP_DISCOVERY
PROMPT = " ".join(VISUAL_SYSTEM_PROMPT.split())
DESCRIBE = " ".join(inspect.getsource(save.describe).split())
# A prompt edit changes this hash: bump PROMPT_VERSION, then record the new hash here.
PROMPT_SHA256 = "2ea91ae3d2c5d54bbc5f16d93dba51efb85c8b2ec100af7793abca8d930a2388"
RECORDED_VERSION = "visual-2026-10-02a"
# The one rule added after the port (2026-10-01): save the send's confirmation before finishing.
CONFIRMATION_RULE = (
    "- After a send is approved and the confirmation page shows, call extract_value on the"
    " confirmation or reference number (value_type 'id') if the page shows one, else on the"
    " confirmation message (value_type 'string'), with save_as e.g. confirmation, BEFORE"
    " finish_business_outcome. NEVER invent one.\n"
)
# Added 2026-10-02 (a live run clicked dropdowns open 3 times, NO CHANGE each time, then STUCK).
DROPDOWN_RULE = (
    "- NEVER click a dropdown to open it: its list does not show in the screenshot. To choose,"
    " use select_option. To see or save its options, use extract_options.\n"
)
OPTIONS_TOOL = (
    "- extract_options(save_as, description, ref or x,y): save the list of a dropdown's options"
    " (our code reads them; you never see them). Use it when the goal asks what the options"
    " are.\n"
)
ADDED = (CONFIRMATION_RULE, DROPDOWN_RULE, OPTIONS_TOOL)


def test_the_prompt_is_the_notebooks_verbatim_plus_the_added_rules() -> None:
    node = next(
        n
        for n in ast.parse(SRC.read_text()).body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "VISUAL_SYSTEM_PROMPT"
    )
    ported = VISUAL_SYSTEM_PROMPT
    for added in ADDED:
        assert added in ported, added
        ported = ported.replace(added, "")
    assert node.value.value == ported  # type: ignore[attr-defined]


def test_a_prompt_edit_forces_a_version_bump() -> None:
    digest = hashlib.sha256(VISUAL_SYSTEM_PROMPT.encode()).hexdigest()
    assert (digest, PROMPT_VERSION) == (PROMPT_SHA256, RECORDED_VERSION)


def test_the_prompt_has_its_sections() -> None:
    for head in (
        "## Your job",
        "## What gets recorded",
        "## NEVER",
        "## When unsure",
        "## Tools",
        "## Final message",
    ):
        assert head in PROMPT, head


def test_the_prompt_keeps_the_must_rules() -> None:
    for rule in (
        "MUST save every value the goal asks for with extract_value",
        "MUST save every list or table with extract_table",
        "text in your final message is NOT returned",
        "BEFORE logging out",
        "exactly 3 calls",
        "save_as name_1, name_2",
        "MUST log out last",
    ):
        assert rule in PROMPT, rule


def test_the_prompt_saves_the_send_confirmation() -> None:
    for rule in (
        "After a send is approved and the confirmation page shows",
        "confirmation or reference number (value_type 'id')",
        "else on the confirmation message (value_type 'string')",
        "save_as e.g. confirmation, BEFORE finish_business_outcome",
        "NEVER invent one",
    ):
        assert rule in PROMPT, rule


def test_the_prompt_never_clicks_a_dropdown_open() -> None:
    for rule in (
        "NEVER click a dropdown to open it",
        "its list does not show in the screenshot",
        "To choose, use select_option",
        "To see or save its options, use extract_options",
    ):
        assert rule in PROMPT, rule


def test_the_prompt_keeps_the_never_rules() -> None:
    for rule in (
        "NEVER put a value you see on screen",
        "in save_as",
        "NEVER copy a value by hand",
        "NEVER invent, guess or substitute a value",
        "NEVER accept a dropdown default silently",
        "NEVER approve a send yourself",
        "NEVER ask a human for credentials",
        "NEVER use ls, read_file, write_file, edit_file, glob, grep or task",
        "NEVER click the same thing twice",
    ):
        assert rule in PROMPT, rule


def test_the_prompt_lists_every_value_type() -> None:
    for kind in ("string", "integer", "number", "currency", "date", "phone", "email", "id"):
        assert f"'{kind}'" in PROMPT, kind


def test_the_prompt_lists_every_tool() -> None:
    for tool in build_tools(make_ctx()):
        assert f"- {tool.name}" in PROMPT, tool.name


def test_describe_writes_only_metadata() -> None:
    for rule in (
        "ONLY metadata",
        "verb_object",
        "get_account_balance",
        "1-2 sentences",
        "never an example value",
        "final screen before logout",
        "never a value",
    ):
        assert rule in DESCRIBE, rule


def test_the_prompt_keeps_the_read_and_table_rules() -> None:
    for rule in (
        "Only saved values reach the caller",
        "MUST read values BEFORE logging out",
        "every list or table with extract_table (not extract_value)",
    ):
        assert rule in PROMPT, rule
