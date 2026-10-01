"""build_agent: the notebook's ``AGENT = create_deep_agent(...)`` (discovery.py 1799-1805) over a
ctx's tools, with the TypeSafe routing middleware appended only when it is on."""

from __future__ import annotations

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from cua.discovery.agent.middleware import (
    LatestScreenshotOnly,
    NoopAnthropicPromptCachingMiddleware,
    RecordWhy,
)
from cua.discovery.agent.prompt import VISUAL_SYSTEM_PROMPT
from cua.discovery.agent.routing import build_routing_middleware
from cua.discovery.context import Ctx
from cua.discovery.tools import build_tools


def build_agent(ctx: Ctx, model: BaseChatModel) -> CompiledStateGraph:  # type: ignore[type-arg]
    """The discovery deep agent, with a checkpointer so a run can be resumed (``run_goal``)."""
    tools = build_tools(ctx)
    print(f"agent ready | {len(tools)} tools")
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=VISUAL_SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
        middleware=[
            RecordWhy(ctx),  # outermost: sees the model's final answer
            NoopAnthropicPromptCachingMiddleware(),
            LatestScreenshotOnly(),
            *build_routing_middleware(lambda: ctx.page.url),
        ],
    )
