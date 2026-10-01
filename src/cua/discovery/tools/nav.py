"""The tools that move around the site: scroll and open_path.

Moved from discovery.py 1297-1343. ``BASE_URL`` is ``ctx.site.base_url``, deny words are
``ctx.site.deny_words``, the scroll step is ``ctx.session.cfg.scroll_px``. Tool names, signatures
and docstrings are the notebook's: the model reads them.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urljoin, urlparse

from langchain_core.tools import BaseTool, tool

from cua.discovery.context import Ctx, act, canvas, look, to_page
from cua.discovery.run import run_values
from cua.discovery.tools.guard import Result, log, one_at_a_time
from cua.discovery.tools.observe import blocks, reply
from cua.discovery.tools.read_helpers import page_texts
from cua.safety import host_allowed, norm
from cua.vision.crops import screens_same


def _make_scroll(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def scroll(direction: str, x: int | None = None, y: int | None = None) -> Result:
        """Scroll up or down, then take a new look. Old numbers stop working.

        Args:
            direction: 'up' or 'down'.
            x: Optional pixel x inside a small scrolling panel.
            y: Optional pixel y inside a small scrolling panel.
        """
        page, cfg = ctx.page, ctx.session.cfg
        before = ctx.run.look or await look(ctx)
        w, h = canvas(ctx)
        at = (x, y) if x is not None and y is not None else (w // 2, h // 2)
        dy = cfg.scroll_px if direction == "down" else -cfg.scroll_px
        after = await act(
            ctx, lambda: page.mouse.move(*to_page(ctx, at)), lambda: page.mouse.wheel(0, dy)
        )
        msg = f"Scrolled {direction}."
        if screens_same(before.png, after.png, cfg):
            msg = "BOTTOM OF PAGE reached." if dy > 0 else "TOP OF PAGE reached."
        log(ctx, "scroll", {"direction": direction, "x": x, "y": y}, msg)
        return blocks(ctx, msg, after)

    return scroll


def path_refusal(ctx: Ctx, path: str, url: str) -> str | None:
    """Why open_path may not open this path, or None."""
    if not host_allowed(url, ctx.site):
        return "REFUSED: that host is not allowed."
    if any(w in norm(path) for w in ctx.site.deny_words):
        return f"REFUSED: '{path}' is not allowed."
    if any(norm(v) not in norm(ctx.run.goal) for _, v in parse_qsl(urlparse(url).query)):
        return "REFUSED: query values must come from the goal."
    return None


def _make_open_path(ctx: Ctx) -> BaseTool:
    @tool(parse_docstring=True)
    @one_at_a_time(ctx)
    async def open_path(path: str) -> Result:
        """Open a page on the allowed site by its path (a menu link or a sitemap path).

        Args:
            path: A path you SAW on this site (a link's target or the current URL). Never guess one.
        """
        url = urljoin(ctx.site.base_url + "/", path.lstrip("/"))
        if refusal := path_refusal(ctx, path, url):
            log(ctx, "open_path", {"path": path}, refusal)
            return await reply(ctx, refusal)
        lk = ctx.run.look
        left = page_texts(lk, run_values(ctx.run, ctx.secrets)) if lk else []
        response = await ctx.page.goto(url)  # network metadata only, never the DOM
        status = response.status if response else 0
        bad = status >= 400  # noqa: PLR2004 (an HTTP error status)
        msg = f"HTTP ERROR {status}: {path} does not exist." if bad else f"Opened {path}."
        log(
            ctx,
            "open_path",
            {"path": path},
            msg,
            status=status,
            path=urlparse(url).path,
            from_texts=left,
        )
        return blocks(ctx, msg, await look(ctx))

    return open_path


def make_nav_tools(ctx: Ctx) -> list[BaseTool]:
    """scroll, open_path (the notebook's TOOLS order)."""
    return [_make_scroll(ctx), _make_open_path(ctx)]
