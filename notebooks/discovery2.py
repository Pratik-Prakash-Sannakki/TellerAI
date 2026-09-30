# %%
"""Discovery v2: a small, practical browser agent pattern.

This notebook is intentionally compact. It follows the same ideas used in
`agent.ipynb`:
- build a browser agent with `create_deep_agent(...)`
- expose a limited set of tools for the browser
- add a human handoff when the agent needs a value or is unsure
- require human approval before an action that changes data
- stop cleanly with a final summary

This is meant to be a small template you can adapt for a real task.
"""

# %%
import os
import uuid

from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from playwright.async_api import async_playwright

load_dotenv(override=True)

MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-5")
BASE = "https://parabank.parasoft.com/parabank"
ALLOWED_HOSTS = {"parabank.parasoft.com"}
SECRETS = {"username": "PARABANK_USERNAME", "password": "PARABANK_PASSWORD"}

# %%
# Browser setup: one visible page, one login flow, one agent.

def resolve_secret(name: str) -> str:
    """Read a secret from the environment without exposing it to the model."""
    key = SECRETS.get(name)
    if not key:
        raise KeyError(f"Unknown secret: {name!r}")
    value = os.getenv(key, "")
    if not value:
        raise RuntimeError(f"Environment variable {key!r} is empty")
    return value


async def open_browser():
    """Open a browser and go to the target page."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
    await page.goto(f"{BASE}/index.htm")
    return pw, browser, context, page


# %%
# A tiny helper surface for the agent. It keeps Playwright calls in one place and
# exposes only the actions the model should use.


class BrowserSurface:
    def __init__(self, page):
        self.page = page

    async def observe(self) -> str:
        return await self.page.inner_text("body")

    async def click(self, selector: str) -> None:
        await self.page.locator(selector).click(timeout=5000, force=True)

    async def fill(self, selector: str, value: str) -> None:
        await self.page.locator(selector).fill(value, timeout=5000, force=True)

    async def select(self, selector: str, label: str) -> None:
        await self.page.locator(selector).select_option(label=label, timeout=5000, force=True)

    async def page_text(self) -> str:
        return (await self.page.inner_text("body"))[:4000]


# %%
# These are the core ideas from `agent.ipynb`:
# - the agent can ask a human for a missing value
# - the agent can ask a human when it is unsure
# - risky actions need approval before they actually happen

RESULT = {}


def human_handoff(message: str) -> str:
    """Simple stand-in for the browser handoff pattern used in the real agent."""
    # In the real notebook, this is where the agent pauses and hands the browser to a human.
    return f"HUMAN HANDOFF: {message}"


async def require_approval(action_name: str, description: str) -> bool:
    """Return True if the action is allowed to continue.

    This mimics the approval check in the larger notebook: a risky action is not
    executed until a human approves it.
    """
    print(f"Approval needed for: {action_name} -> {description}")
    answer = input("Approve this action? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


# %%
# Browser tools. This is intentionally tiny and readable.


@tool(parse_docstring=True)
async def observe() -> str:
    """Look at the current page and return the visible text."""
    return await surface.observe()


@tool(parse_docstring=True)
async def type_secret(ref: str, name: str) -> str:
    """Type a stored secret into a field. Never reveal the value."""
    value = resolve_secret(name)
    await surface.fill(ref, value)
    return f"Typed secret '{name}' into {ref}."


@tool(parse_docstring=True)
async def type_text(ref: str, text: str) -> str:
    """Type text the user explicitly gave us."""
    await surface.fill(ref, text)
    return f"Typed '{text}' into {ref}."


@tool(parse_docstring=True)
async def click(ref: str) -> str:
    """Click an element on the page.

    If this action changes data, approval must be granted first.
    """
    if "submit" in ref.lower() or "transfer" in ref.lower() or "payment" in ref.lower():
        allowed = await require_approval("click", f"Click on {ref}")
        if not allowed:
            return f"DECLINED: {ref} was not approved."
    await surface.click(ref)
    return f"Clicked {ref}."


@tool(parse_docstring=True)
async def request_value(ref: str, hint: str) -> str:
    """Ask the human to provide a missing value for one field."""
    return human_handoff(f"Please fill {ref} ({hint}) and then hand control back to the agent.")


@tool(parse_docstring=True)
async def ask_human(question: str) -> str:
    """Use this when the agent is unsure which element or next step to take."""
    return human_handoff(question)


@tool(parse_docstring=True)
async def finish(summary: str, values: dict) -> str:
    """End the run and report the final result."""
    RESULT.clear()
    RESULT.update({"summary": summary, "values": values})
    return "Recorded. Stop now."


BROWSER_TOOLS = [observe, type_secret, type_text, click, request_value, ask_human, finish]

# %%
# This is the 1-2-3 pattern used in the bigger agent notebook.
SYSTEM_PROMPT = """
You are a browser agent for a banking demo site.

Rules:
1. Observe the page before acting.
2. Use only values the user gave you. Never invent one.
3. If a value is missing, ask the human for it and continue.
4. If you are unsure which element to choose, ask the human.
5. If an action changes data, stop for approval.
6. Finish by reporting summary and values.
"""


def build_agent():
    """Factory for the deep agent. This mirrors the pattern used in `agent.ipynb`."""
    return create_deep_agent(
        model=MODEL,
        tools=BROWSER_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )


# %%
# The demo run.
# This is intentionally simple: it shows the agent can log in, fill a form, ask a human
# for a missing value, and stop before a risky action without a human approval.

# For a real run, uncomment and run this in a notebook cell after starting the browser.
# _pw, _browser, _context, _page = await open_browser()
# surface = BrowserSurface(_page)
# agent = build_agent()
# GOAL = "Log in, then transfer $25 from my account to 999999."
# result = await agent.ainvoke({
#     "messages": [{"role": "user", "content": GOAL}],
# }, config={"configurable": {"thread_id": f"discovery2-{uuid.uuid4().hex[:6]}"}})
# print(result["messages"][-1].content)

# %%
# Practical notes from the reference agent notebook:
# - ask_human() is for uncertainty or a decision the model cannot make itself
# - request_value() is for a single missing field that the user did not provide
# - request_missing_values() is the batch version when multiple fields are empty
# - a risky action such as payment, transfer, or submit should not proceed without human approval
# - if the human rejects the action, stop and do not retry
# - finish() is the formal end state for both success and blocked cases

print("discovery2 notebook ready")
