"""build_agent: the notebook's agent over a ctx's tools, with the TypeSafe routing middleware
appended only when it is on.

Built with ``langchain.agents.create_agent``, not ``deepagents.create_deep_agent``: the latter
always injects a virtual filesystem (``ls``, ``read_file``, ``write_file``, ``edit_file``,
``glob``, ``grep``, ``delete``, ``execute``) and a sub-agent ``task`` tool, and its
``FilesystemMiddleware``/``SubAgentMiddleware`` cannot be excluded. A banking agent needs neither,
so the model sees only our 13 tools. From deepagents we keep ``PatchToolCallsMiddleware``, which
answers a dangling tool call left by an interrupted run before it resumes.
"""

from __future__ import annotations

from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from langchain.agents import create_agent
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
    """The discovery agent, with a checkpointer so a run can be resumed (``run_goal``)."""
    tools = build_tools(ctx)
    print(f"agent ready | {len(tools)} tools")
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=VISUAL_SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
        middleware=[
            RecordWhy(ctx),  # outermost: sees the model's final answer
            NoopAnthropicPromptCachingMiddleware(),
            LatestScreenshotOnly(),
            *build_routing_middleware(lambda: ctx.page.url),
            PatchToolCallsMiddleware(),  # before_agent only: its place in the list is moot
        ],
    )
