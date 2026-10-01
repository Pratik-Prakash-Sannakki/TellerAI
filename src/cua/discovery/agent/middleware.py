"""The notebook's two agent middlewares, moved unchanged from discovery.py 1767-1797."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

Handler = Callable[[ModelRequest], ModelResponse]
AsyncHandler = Callable[[ModelRequest], Awaitable[ModelResponse]]


class NoopAnthropicPromptCachingMiddleware(AgentMiddleware):
    """Disable prompt caching on the Iliad gateway; it rejects Anthropic cache markers."""

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
