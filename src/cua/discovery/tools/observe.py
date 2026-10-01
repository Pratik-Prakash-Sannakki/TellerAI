"""What the model sees: a look as content blocks (text listing + the numbered screenshot), and the
``observe`` tool.

Moved from discovery.py 289-295 (blocks), 1134-1135 (reply) and 1138-1142 (observe). ``blocks``
hides each secret value by name (``ctx.secrets``), as the notebook's ``hide_secrets`` did.
"""

from __future__ import annotations

import base64

from langchain_core.tools import BaseTool, tool

from cua.discovery.context import Ctx, look
from cua.discovery.tools import guard  # module import: guard -> human -> this module
from cua.safety import hide_secrets
from cua.vision.look import Look


def blocks(ctx: Ctx, prefix: str, lk: Look) -> list[dict[str, str]]:
    listing = "\n".join(
        f"[{e.ref}] {hide_secrets(e.text, ctx.secrets)!r} "
        f"box=({e.box.x1},{e.box.y1},{e.box.x2},{e.box.y2})"
        for e in lk.elements
    )
    return [
        {"type": "text", "text": f"{prefix}\nURL: {lk.url}\nText on screen:\n{listing}"},
        {
            "type": "image",
            "base64": base64.b64encode(lk.drawn).decode(),
            "mime_type": "image/png",
        },
    ]


async def reply(ctx: Ctx, msg: str) -> list[dict[str, str]]:
    return blocks(ctx, msg, ctx.run.look or await look(ctx))


def make_observe_tools(ctx: Ctx) -> list[BaseTool]:
    @tool(parse_docstring=True)
    @guard.one_at_a_time(ctx)
    async def observe() -> guard.Result:
        """Take a new screenshot and number every piece of text on it. Old numbers stop working."""
        return blocks(ctx, "Current page.", await look(ctx))

    return [observe]
