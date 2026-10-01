"""The prompts are the first filter (user, 2026-09-30); the models and code checks are the second.
These rules must never be dropped by a later edit."""
from pathlib import Path

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"
TEXT = SRC.read_text()


def _flat(start: str, end: str) -> str:
    body = TEXT[TEXT.index(start):]
    return " ".join(body[:body.index(end)].split())


PROMPT = _flat("VISUAL_SYSTEM_PROMPT = ", '"""\n\n')
DESCRIBE = _flat("async def describe(", "# %% [markdown]\n# ## Evidence")


def test_the_prompt_has_its_sections() -> None:
    for head in ("## Your job", "## What gets recorded", "## NEVER", "## When unsure", "## Tools",
                 "## Final message"):
        assert head in PROMPT, head


def test_the_prompt_keeps_the_must_rules() -> None:
    for rule in ("MUST save every value the goal asks for with extract_value",
                 "MUST save every list or table with extract_table",
                 "text in your final message is NOT returned",
                 "BEFORE logging out", "exactly 3 calls", "save_as name_1, name_2",
                 "MUST log out last"):
        assert rule in PROMPT, rule


def test_the_prompt_keeps_the_never_rules() -> None:
    for rule in ("NEVER put a value you see on screen", "in save_as", "NEVER copy a value by hand",
                 "NEVER invent, guess or substitute a value", "NEVER accept a dropdown default silently",
                 "NEVER approve a send yourself", "NEVER ask a human for credentials",
                 "NEVER use ls, read_file, write_file, edit_file, glob, grep or task",
                 "NEVER click the same thing twice"):
        assert rule in PROMPT, rule


def test_the_prompt_lists_every_value_type() -> None:
    for kind in ("string", "integer", "number", "currency", "date", "phone", "email", "id"):
        assert f"'{kind}'" in PROMPT, kind


def test_the_prompt_lists_every_tool() -> None:
    names = TEXT[TEXT.index("TOOLS = ["):].split("]", 1)[0]
    for name in names.removeprefix("TOOLS = [").replace("\n", " ").split(","):
        assert f"- {name.strip()}" in PROMPT, name


def test_describe_writes_only_metadata() -> None:
    for rule in ("ONLY metadata", "verb_object", "get_account_balance", "1-2 sentences",
                 "never an example value", "final screen before logout", "never a value"):
        assert rule in DESCRIBE, rule


def test_the_prompt_keeps_the_read_and_table_rules() -> None:
    """Moved from test_read_runs.py / test_extract_table.py (their tool code is now in cua)."""
    for rule in ("Only saved values reach the caller", "MUST read values BEFORE logging out",
                 "every list or table with extract_table (not extract_value)"):
        assert rule in PROMPT, rule
