"""The notebook's two agent middlewares, moved unchanged from discovery.py 1767-1797, plus
``RecordWhy``: the model's short reason for each tool call, masked, for the event log (3.5),
and ``OnlyOurTools``: deepagents' built-in tools are never offered to the model, and refused if
called."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Iterable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from cua.discovery.context import Ctx
from cua.discovery.run import run_values, saved_texts
from cua.safety.redact import hide_secrets, redactor
from cua.schema.value_types import SHAPES

Handler = Callable[[ModelRequest], ModelResponse]
AsyncHandler = Callable[[ModelRequest], Awaitable[ModelResponse]]
ToolResult = ToolMessage | Command  # type: ignore[type-arg]
ToolHandler = Callable[[ToolCallRequest], ToolResult]
AsyncToolHandler = Callable[[ToolCallRequest], Awaitable[ToolResult]]
WHY_CHARS = 200  # an event's ``why`` is at most this long
# A ``why`` is never a value: anything value-shaped left after masking is blanked as well (an
# email, phone, amount or date, or 4+ digits in a row, spaces/dashes allowed: account-like).
VALUE_SHAPED = re.compile(
    "|".join(f"(?:{SHAPES[k]})" for k in ("email", "phone", "currency", "date"))
    + r"|\d(?:[ -]?\d){3,}"
)


class NoopAnthropicPromptCachingMiddleware(AgentMiddleware):
    """Disable prompt caching: some Anthropic-compatible gateways reject cache markers."""

    name = "AnthropicPromptCachingMiddleware"

    def wrap_model_call(self, request: ModelRequest, handler: Handler) -> ModelResponse:
        return handler(request)

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        return await handler(request)


def _has_image(content: object) -> bool:
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "image" for b in content
    )


class LatestScreenshotOnly(AgentMiddleware):
    """Old screenshots are stale (their numbers no longer work); send the model only the newest."""

    def _trim(self, request: ModelRequest) -> ModelRequest:
        seen, msgs = False, []
        for msg in reversed(request.messages):
            m = msg
            if _has_image(m.content):
                if seen:
                    m = m.model_copy(
                        update={
                            "content": [
                                b
                                for b in m.content
                                if not (isinstance(b, dict) and b.get("type") == "image")
                            ]
                        }
                    )
                seen = True
            msgs.append(m)
        return request.override(messages=msgs[::-1])

    def wrap_model_call(self, request: ModelRequest, handler: Handler) -> ModelResponse:
        return handler(self._trim(request))

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        return await handler(self._trim(request))


def _arg_values(msg: AIMessage) -> set[str]:
    """Every text the model is about to pass a tool (refs and x/y are ints, not values): masked
    even before it is typed."""
    return {v for call in msg.tool_calls for v in call["args"].values() if isinstance(v, str)}


class RecordWhy(AgentMiddleware):
    """3.5: keep the text the model wrote before its tool calls as ``ctx.run.why`` (masked with
    every run value, secret and the calls' own args, then every value shape, then cut to
    ``WHY_CHARS``); ``guard.log``
    puts it on each event those calls write. Never a value."""

    def __init__(self, ctx: Ctx) -> None:
        super().__init__()
        self.ctx = ctx

    def _record(self, response: ModelResponse) -> ModelResponse:
        msg = next((m for m in response.result if isinstance(m, AIMessage)), None)
        if msg is None or not msg.tool_calls:
            return response
        run, secrets = self.ctx.run, self.ctx.secrets
        values = run_values(run, secrets) | saved_texts(run.saved) | _arg_values(msg)
        text = " ".join(hide_secrets(msg.text, secrets).split())
        run.why = VALUE_SHAPED.sub("[value]", redactor(values)(text))[:WHY_CHARS]
        return response

    def wrap_model_call(self, request: ModelRequest, handler: Handler) -> ModelResponse:
        return self._record(handler(request))

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        return self._record(await handler(request))


class OnlyOurTools(AgentMiddleware):
    """``create_deep_agent`` always adds deepagents' file tools (``ls``, ``read_file``, ...) and its
    ``task`` sub-agent tool. The model is offered only ``allowed`` (our tools); a call to any other
    name is answered "REFUSED" and never run. Place it before the tool router, which then only
    narrows within ours."""

    def __init__(self, allowed: Iterable[str]) -> None:
        super().__init__()
        self.allowed = frozenset(allowed)

    def _offer(self, request: ModelRequest) -> ModelRequest:
        return request.override(
            tools=[t for t in request.tools if getattr(t, "name", None) in self.allowed]
        )

    def _refusal(self, request: ToolCallRequest) -> ToolMessage | None:
        name = request.tool_call["name"]
        if name in self.allowed:
            return None
        return ToolMessage(
            content=f"REFUSED: {name!r} is not an allowed tool",
            name=name,
            tool_call_id=request.tool_call["id"],
            status="error",
        )

    def wrap_model_call(self, request: ModelRequest, handler: Handler) -> ModelResponse:
        return handler(self._offer(request))

    async def awrap_model_call(self, request: ModelRequest, handler: AsyncHandler) -> ModelResponse:
        return await handler(self._offer(request))

    def wrap_tool_call(self, request: ToolCallRequest, handler: ToolHandler) -> ToolResult:
        return self._refusal(request) or handler(request)

    async def awrap_tool_call(
        self, request: ToolCallRequest, handler: AsyncToolHandler
    ) -> ToolResult:
        return self._refusal(request) or await handler(request)
