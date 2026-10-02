"""One replay run's working state: :class:`ReplayRun` (was the notebook's ``ReplayState``/``STATE``)
and :class:`LastRun` (was ``LAST_RUN``).

Moved from notebooks/replay/replay.py 312-337 (``ReplayState``, ``url_path``) and 1571
(``LAST_RUN``). ``ReplayRun`` satisfies :class:`cua.safety.send_guard.SendState`; its
``given_text()`` is replay's mismatch text (the input values and human edits, no goal). A run is
wiped after every ``replay()`` (R7): the engine swaps in a fresh ``ReplayRun``; only
``LastRun.values`` (the mask set for evidence) and ``LastRun.final`` (the last screen) survive,
in memory only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from pydantic import JsonValue

from cua.vision import Look


@dataclass
class ReplayRun:
    """Working values for one run. Replaced by a new one in ``replay``'s ``finally`` (R7)."""

    look: Look | None = None
    values: dict[str, str] = field(default_factory=dict)
    given: list[str] = field(default_factory=list)  # input values + human edits (mismatch check)
    outputs: dict[str, str | list[dict[str, str]] | list[str]] = field(default_factory=dict)
    allow_send: bool = False  # set only around a login click
    sent: bool = False  # a non-GET request went out during this action
    gated: bool = False  # this run sent something through the human gates (not the login)
    rung: str = ""  # the rung that found the current step's target
    http: tuple[int, str] | None = None  # the last main-document response: (status, path)
    navs: int = 0  # main-document responses so far (a same-URL reload is one too)
    verdict: str = ""  # what the send gate decided during the last action
    takeover: dict[str, list[str]] | None = None  # during a take-over: page and send paths
    human: list[dict[str, JsonValue]] = field(default_factory=list)  # one per take-over
    dropdowns: list[dict[str, object]] = field(default_factory=list)  # read before a click
    step: int | None = None  # where the run is, for failure.json (len(steps) = the checkpoint)
    outcomes: list[dict[str, str]] = field(default_factory=list)  # R17 rules for this run
    recoveries: int = 0  # re-logins done (at most one per run)
    action: str = ""

    def given_text(self) -> str:
        """What the mismatch check compares a send against (SendState)."""
        return " ".join(self.given)


@dataclass
class LastRun:
    """The last run's mask set and final screen, memory only (was ``LAST_RUN``)."""

    values: set[str] = field(default_factory=set)
    final: bytes | None = None


def url_path(url: str) -> str:
    """Path only: no query, no `;jsessionid`, so no values."""
    return urlparse(url).path.split(";")[0]
