"""Replay test helpers: ``make_replay_ctx`` (a real Ctx on fakes), ``mk_look``, step builders.

Replaces the old tests/replay/conftest.py ``ns`` fixture (ast-exec of the notebook): where those
tests swapped a notebook global, these pass a fake into the Ctx or ``monkeypatch`` the module
attribute the code looks up at call time (``steps.ACTIONS``, ``steps.shows``, ``engine.snap``...).
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import cast

import yaml

from cua.browser.session import Session
from cua.config import BrowserConfig, ReplayConfig, load_site
from cua.handoff.control_window import ControlWindow
from cua.replay.context import Ctx
from cua.schema import Capability, Click, Extract, Navigate, Select, Type
from cua.vision import Box, Element, Look, RefCounter

SITE = load_site("parabank")
BASE = "https://parabank.parasoft.com/p"
URL = "https://parabank.parasoft.com/parabank/x.htm"


class FakeLock:
    """SiteLock stand-in: open() unlocks for the block."""

    @contextlib.asynccontextmanager
    async def open(self) -> AsyncIterator[None]:
        yield


def mk_look(
    items: list[tuple[str, tuple[int, int, int, int]]], png: bytes = b"", url: str = URL
) -> Look:
    els = tuple(Element(i + 1, t, Box(*b)) for i, (t, b) in enumerate(items))
    return Look(png, png, els, url)


def make_replay_ctx(  # noqa: PLR0913 - a test factory with defaults
    page: object = None,
    control: object = None,
    *,
    cfg: ReplayConfig | None = None,
    bcfg: BrowserConfig | None = None,
    ext: object = None,
    look: Look | None = None,
) -> Ctx:
    """A real Ctx (real SendGuard, real ReplayRun) over a fake page/control/lock. ``shoot``
    returns the run's current look unless a test replaces ``ctx.shoot``."""
    session = Session(
        pw=None,  # type: ignore[arg-type]
        context=None,  # type: ignore[arg-type]
        page=page,  # type: ignore[arg-type]
        control_page=None,  # type: ignore[arg-type]
        ext=ext,  # type: ignore[arg-type]
        cfg=bcfg or BrowserConfig(),
        site=SITE,
        lock=FakeLock(),  # type: ignore[arg-type]
        refs=RefCounter(),
    )
    secrets = {"username": "u-secret", "password": "p-secret"}
    holder: list[Ctx] = []

    async def shoot() -> Look:
        return cast(Look, holder[0].run.look)

    ctx = Ctx(session, cfg or ReplayConfig(), cast(ControlWindow, control), secrets, shoot)
    holder.append(ctx)
    ctx.run.look = look
    return ctx


def set_control(ctx: Ctx, control: object) -> None:
    """The guard keeps its own reference to the control window: swap both."""
    ctx.control = ctx.guard.control = cast(ControlWindow, control)


def set_shoot(ctx: Ctx, fn: Callable[[], Awaitable[Look]]) -> None:
    ctx.shoot = fn


def screen(ctx: Ctx, lk: Look) -> None:
    """``take_look`` always returns this look."""

    async def shoot() -> Look:
        return lk

    ctx.shoot = shoot
    ctx.run.look = lk


def cap(steps: list[object], checkpoint: str = "Done", **kw: object) -> Capability:
    return Capability(
        name="t",
        description="t",
        base_url=BASE,
        viewport=(1280, 800),
        steps=steps,  # type: ignore[arg-type]
        checkpoint=checkpoint,
        **kw,  # type: ignore[arg-type]
    )


def click(text: str, cleanup: bool = False) -> Click:
    return Click.model_validate(
        {
            "target": {"ocr_text": {"text": text}, "anchor": {"label": text, "offset": [0, 0]}},
            "cleanup": cleanup,
        }
    )


def type_(value: str, label: str = "Username", offset: tuple[int, int] = (150, 0)) -> Type:
    return Type.model_validate(
        {"value": value, "target": {"anchor": {"label": label, "offset": list(offset)}}}
    )


def select(name: str, **kw: object) -> Select:
    return Select.model_validate(
        {
            "option": f"{{{{{name}}}}}",
            "target": {"anchor": {"label": name, "offset": [60, 0]}},
            **kw,
        }
    )


def extract(save_as: str, target: dict[str, object], **kw: object) -> Extract:
    return Extract.model_validate({"save_as": save_as, "target": target, **kw})


def navigate(path: str) -> Navigate:
    return Navigate(path=path)


CAP = {
    "schema_version": 2,
    "name": "get_balance",
    "description": "Read a balance.",
    "base_url": "https://parabank.parasoft.com/parabank",
    "viewport": [1280, 800],
    "device_scale_factor": 1,
    "inputs": [{"name": "account_id"}],
    "outputs": [{"name": "balance", "type": "currency", "description": "Balance"}],
    "secrets": ["username"],
    "steps": [
        {
            "action": "type",
            "value": "{{secret:username}}",
            "target": {
                "anchor": {"label": "Username", "offset": [150, 0]},
                "template": "crops/s0.png",
            },
        },
        {
            "action": "extract",
            "save_as": "balance",
            "target": {"table_cell": {"row_key": "{{account_id}}", "column": "Balance"}},
        },
    ],
    "checkpoint": "Accounts Overview",
}


def write_cap(tmp_path: Path, data: dict[str, object] = CAP) -> Path:
    (tmp_path / "crops").mkdir(exist_ok=True)
    (tmp_path / "crops/s0.png").write_bytes(b"png")
    path = tmp_path / "cap.yaml"
    path.write_text(yaml.safe_dump(data))
    return path
