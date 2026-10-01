"""The discovery agent: system prompt, middleware, optional TypeSafe routing, and build_agent.

``build`` is not imported here (it pulls in deepagents and the tools); import
``cua.discovery.agent.build`` for ``build_agent``.
"""

from cua.discovery.agent.prompt import PROMPT_VERSION, VISUAL_SYSTEM_PROMPT

__all__ = ["PROMPT_VERSION", "VISUAL_SYSTEM_PROMPT"]
