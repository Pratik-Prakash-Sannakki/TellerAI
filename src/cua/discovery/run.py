"""DiscoveryRun: one discovery run's working state (was the notebook's ``HandoffState``).

Moved from discovery.py 419-457 and the ``run_goal`` finally block (1828-1832). A fresh object per
run (``cua.discovery.wiring.new_run``); the notebook's ``NAVS["main"]`` and ``ACT_LOCK`` globals
are now the ``navs`` counter and the ``act_lock`` field. It satisfies ``cua.safety.SendState``,
so the send guard reads and writes it without knowing it is discovery's.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field

from cua.discovery.recorder.events import flag_leaks
from cua.safety.redact import norm
from cua.schema.events import Event
from cua.vision.look import Look

DECLINED = "DECLINED by a human. Do not retry or work around it. Reply 'DECLINED: <why>' and stop."

Saved = dict[str, str | list[dict[str, str]] | list[str]]  # a table: rows; a dropdown: options


@dataclass
class DiscoveryRun:
    goal: str = ""
    look: Look | None = None
    saved: Saved = field(default_factory=dict)  # a table: its rows
    tables: dict[str, list[object]] = field(default_factory=dict)  # save_as -> column spans
    declined: set[str] = field(default_factory=set)
    recent: list[str] = field(default_factory=list)
    log: list[Event] = field(default_factory=list)  # the one event log
    login_tries: int = 0
    typed_secrets: set[str] = field(default_factory=set)
    typed_texts: set[str] = field(default_factory=set)
    login_blocked: bool = False
    stuck: str = ""
    entered: dict[str, str] = field(default_factory=dict)  # label -> value shown to the reviewer
    steps: int = 0
    fails: int = 0
    allow_send: bool = False  # set only around a login click
    given: list[str] = field(default_factory=list)  # what the human said: goal + every answer
    verdict: str = ""  # what the send gate decided during the last action
    takeover: list[dict[str, str]] | None = None  # the human's pages and sends, while in control
    dropdowns: list[dict[str, object]] = field(default_factory=list)  # read before each action
    redact: set[str] = field(default_factory=set)  # run values, only to mask evidence (in memory)
    answer: str = ""  # the agent's final message
    why: str = ""  # the model's masked reason for its latest tool calls (RecordWhy)
    messages: list[object] = field(default_factory=list)  # the run's chat, for the transcript
    final_shot: bytes | None = None  # the page when a run ends STUCK/DECLINED or crashes
    navs: int = 0  # main-frame navigations so far (a link back to the same URL is one too)
    act_lock: asyncio.Lock = field(default_factory=asyncio.Lock)  # one tool call at a time

    def given_text(self) -> str:
        """What the human gave: the goal and every answer (the send guard's mismatch text)."""
        return " ".join([self.goal, *self.given])


def run_values(run: DiscoveryRun, secrets: Mapping[str, str]) -> set[str]:
    """Every value typed, entered, given or sent this run, plus the secrets (in memory only).
    ``secrets`` maps a secret name to its value."""
    return {
        norm(v)
        for v in (
            *run.typed_texts,
            *run.given,
            *run.entered.values(),
            *run.redact,
            *secrets.values(),
        )
        if norm(v) and v != "******"
    }


def saved_texts(saved: Saved) -> set[str]:
    """Every saved text, table cells and dropdown options included (evidence masking only)."""
    return {
        t
        for v in saved.values()
        for t in (
            [v]
            if isinstance(v, str)
            else [c for r in v for c in (r.values() if isinstance(r, dict) else [r])]
        )
        if t
    }


def wipe(run: DiscoveryRun, secrets: Mapping[str, str]) -> None:
    """Banking: values live only for the run. Keep the log (labels only), drop the rest.
    (run_goal's ``finally``.) ``redact`` stays, for save_evidence only."""
    flag_leaks(run.log, run_values(run, secrets))
    run.redact |= run_values(run, secrets) | saved_texts(run.saved)
    run.entered, run.given, run.look = {}, [], None
    run.typed_texts.clear()
