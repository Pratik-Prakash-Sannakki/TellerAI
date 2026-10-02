"""Discovery's agent tools. ``build_tools(ctx)`` returns the notebook's 12 @tool functions in its
TOOLS order (discovery.py 1706-1707), plus ``extract_options`` after extract_table, each a closure
over ``ctx`` (it reads ``ctx.run`` at call time, so one tool set serves every run of a session).

This package's ``__init__`` stays import-light: ``recorder.events`` imports ``tools.failed`` while
``cua.discovery.context`` is still loading, so the tool modules are imported inside
``build_tools``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

    from cua.discovery.context import Ctx


def build_tools(ctx: Ctx) -> list[BaseTool]:
    """observe, click, type_text, type_secret, select_option, scroll, open_path, extract_value,
    extract_table, extract_options, finish_business_outcome, request_missing_values, ask_human."""
    from cua.discovery.tools.act import make_act_tools  # noqa: PLC0415 (see the module docstring)
    from cua.discovery.tools.human import make_human_tools  # noqa: PLC0415
    from cua.discovery.tools.nav import make_nav_tools  # noqa: PLC0415
    from cua.discovery.tools.observe import make_observe_tools  # noqa: PLC0415
    from cua.discovery.tools.read import make_read_tools  # noqa: PLC0415

    return [
        *make_observe_tools(ctx),
        *make_act_tools(ctx),
        *make_nav_tools(ctx),
        *make_read_tools(ctx),
        *make_human_tools(ctx),
    ]
