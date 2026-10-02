"""TypeSafe tool selection + model routing, restored (user, 2026-10-01; notebooks/discovery/PLAN.md
D50/D52/D76). Ported from the old DOM agent (``git show 4f692a8^:src/cua/agent.py``, the
``NEVER_HIDE``..``build_typesafe_middleware`` block) and re-mapped to the visual tools.

Off unless ``TYPESAFE_API_KEY`` is set: ``build_routing_middleware`` then returns ``[]`` and the
agent is the notebook's (one model, every tool). When on, each model call first sends the page
path and the last result's text (first 400 chars) to typesafe.ai: never turn it on with real data.
The tool router fails OPEN: below ``JOB_CONFIDENCE_THRESHOLD``, or on any classifier error, every
tool stays. ``langchain_typesafe`` (the ``typesafe`` extra) is imported only when the key is set.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from types import ModuleType
from typing import Protocol

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.language_models import BaseChatModel

from cua.llm import make_chat_model, model_name_for

NEVER_HIDE = frozenset({"observe", "click", "type_secret", "ask_human"})  # whatever the job

JOB_EXTRA_TOOLS: dict[str, frozenset[str]] = {
    "login": frozenset({"type_secret"}),
    "fill_form": frozenset({"type_text", "select_option", "scroll"}),
    "read_value": frozenset({"extract_value", "extract_table", "extract_options", "scroll"}),
    "navigate": frozenset({"open_path", "scroll"}),
    "need_human": frozenset({"request_missing_values", "ask_human"}),
    "finish": frozenset({"finish_business_outcome"}),
}
JOB_CRITERIA = {
    "login": "The page shows a username or password field, or we have not logged in yet.",
    "fill_form": "A form is on screen and a field still needs a value typed or a dropdown chosen.",
    "read_value": "We need to read a value or a table already on the page, such as a balance, a "
    "list of transactions, a dropdown's options or a confirmation message.",
    "navigate": "We need to reach another page of this site, or scroll to find something.",
    "need_human": "We are unsure which element to use, or a value we need was not given by the "
    "user.",
    "finish": "The goal's business result is on screen and only needs to be reported.",
}
JOB_CONFIDENCE_THRESHOLD = 0.8
MODEL_CRITERIA = {
    "fast": "A single simple step: reading the page, or one obvious click, type, or select with "
    "no ambiguity.",
    "powerful": "Anything else: planning, choosing between several similar elements, forms, or "
    "any step before a risky click.",
}
MODEL_INSTRUCTIONS = "Pick the cheapest model that can do this step correctly. If unsure, pick "
"'powerful'."

AsyncHandler = Callable[[ModelRequest], Awaitable[ModelResponse]]


class Classifier(Protocol):
    async def ainvoke(self, payload: dict[str, object]) -> object: ...


def job_tool_names(job: str, never_hide: frozenset[str] = NEVER_HIDE) -> set[str]:
    """Tools this job needs, plus the always-allowed set. Pure: no network, no LLM."""
    return set(never_hide) | JOB_EXTRA_TOOLS.get(job, frozenset())


def confidence_gate(
    base_tools: set[str],
    job: str,
    confidence: float,
    never_hide: frozenset[str] = NEVER_HIDE,
    threshold: float = JOB_CONFIDENCE_THRESHOLD,
) -> set[str]:
    """Narrow base_tools to this job's tools, but only if the classifier is confident.
    Below the threshold, fail OPEN: return base_tools unchanged rather than guess wrong."""
    if confidence < threshold:
        return base_tools
    return base_tools & job_tool_names(job, never_hide)


def page_name(url: str) -> str:
    """The URL's last path segment: no query, no ``;jsessionid=``, no trailing slash, lower case."""
    return url.split("?")[0].split(";")[0].rstrip("/").rsplit("/", 1)[-1].lower()


def step_state(request: ModelRequest, page_path: Callable[[], str]) -> str:
    """What the classifier sees for a step: the page path + the last result's first 400 chars."""
    last = str(request.messages[-1].content)[:400]
    return f"page={page_name(page_path())!r}. last result: {last!r}"


class ToolRouter(AgentMiddleware):
    """Classifies the step's job with TypeSafe's Choice primitive and narrows the tool list to it.
    Sends the current page path and the last tool result's text to typesafe.ai (never enable on a
    run that may show real account data). Any error here (network, auth, timeout) fails OPEN:
    the request goes through unmodified."""

    def __init__(
        self,
        classifier: Classifier,
        page_path: Callable[[], str],
        choice: Callable[..., object],
        never_hide: frozenset[str] = NEVER_HIDE,
    ) -> None:
        self.classifier, self.page_path, self.choice = classifier, page_path, choice
        self.never_hide = never_hide

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        try:
            state = step_state(request, self.page_path)
            job = self.choice(instructions="What kind of step is this?", criteria=JOB_CRITERIA)
            response = await self.classifier.ainvoke({"state": state, "questions": {"job": job}})
            answer = response.choices["job"]  # type: ignore[attr-defined]
            named = {t.name for t in request.tools if hasattr(t, "name")}
            keep = confidence_gate(named, answer.choice, answer.confidence, self.never_hide)
            request = request.override(
                tools=[t for t in request.tools if not hasattr(t, "name") or t.name in keep]
            )
            print(
                f"typesafe job -> {answer.choice!r} confidence={answer.confidence:.2f} "
                f"kept={sorted(keep)}"
            )
        except Exception as exc:
            why = f"{type(exc).__name__}: {exc}"
            print(f"typesafe job router FAILED, continuing with no change: {why}")
        return await handler(request)


def _typesafe() -> ModuleType:
    import langchain_typesafe  # noqa: PLC0415 (optional extra: imported only when switched on)

    return langchain_typesafe


class ModelRouter(AgentMiddleware):
    """Picks Haiku ("fast") or Sonnet ("powerful") for EACH model call, from the same step state
    the tool router sees. (TypeSafe's own ModelRouterMiddleware decides once per run from the
    goal, so a multi-step goal never reached Haiku.) Haiku only when the classifier is confident;
    below the threshold or on any error, the step uses Sonnet."""

    def __init__(
        self,
        classifier: Classifier,
        page_path: Callable[[], str],
        choice: Callable[..., object],
        models: dict[str, BaseChatModel],
        threshold: float = JOB_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.classifier, self.page_path, self.choice = classifier, page_path, choice
        self.models, self.threshold = models, threshold

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        route = "powerful"
        try:
            pick = self.choice(instructions=MODEL_INSTRUCTIONS, criteria=MODEL_CRITERIA)
            payload: dict[str, object] = {
                "state": step_state(request, self.page_path),
                "questions": {"model": pick},
            }
            response = await self.classifier.ainvoke(payload)
            answer = response.choices["model"]  # type: ignore[attr-defined]
            if answer.choice == "fast" and answer.confidence >= self.threshold:
                route = "fast"
            print(f"typesafe model -> {route!r} (asked {answer.choice!r} {answer.confidence:.2f})")
        except Exception as exc:
            print(f"typesafe model router FAILED, using 'powerful': {type(exc).__name__}: {exc}")
        return await handler(request.override(model=self.models[route]))


def _models() -> dict[str, BaseChatModel]:
    return {"fast": make_chat_model("haiku"), "powerful": make_chat_model("sonnet")}


def build_routing_middleware(page_path: Callable[[], str]) -> list[AgentMiddleware]:
    """[tool router, model router] when ``TYPESAFE_API_KEY`` is set, else ``[]`` (the notebook's
    agent, unchanged). ``page_path`` returns the site tab's current URL."""
    if not os.getenv("TYPESAFE_API_KEY", ""):
        print(
            "model router OFF: no TYPESAFE_API_KEY in .env. Using Sonnet only:",
            model_name_for("sonnet"),
        )
        return []
    ts = _typesafe()
    classifier = ts.TypeSafeClassifier()
    tools = ToolRouter(classifier, page_path, ts.Choice)
    models = ModelRouter(classifier, page_path, ts.Choice, _models())
    print(
        f"model router ON (TypeSafe, per step): fast={model_name_for('haiku')} | "
        f"powerful={model_name_for('sonnet')}"
    )
    return [tools, models]
