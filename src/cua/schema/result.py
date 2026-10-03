"""What a replay run returns: its Status, the Stop that ends a run early, and ReplayResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import JsonValue


class Status(StrEnum):
    """R17 run statuses. A member is a plain str, so ``Status.SUCCESS == "SUCCESS"``."""

    SUCCESS = "SUCCESS"
    BUSINESS_OUTCOME = "BUSINESS_OUTCOME"
    DECLINED = "DECLINED"
    STUCK = "STUCK"
    FAILED = "FAILED"


class Stop(Exception):
    """Ends the run with a status (R17). The reason never holds a value; `observed` is masked on
    save."""

    def __init__(self, status: str, reason: str, expected: str = "", observed: str = "") -> None:
        super().__init__(reason)
        self.status, self.reason, self.expected, self.observed = status, reason, expected, observed


@dataclass(frozen=True)
class ReplayResult:
    status: str  # SUCCESS | BUSINESS_OUTCOME | DECLINED | STUCK | FAILED (R17), see Status
    outputs: dict[str, str | list[dict[str, str]] | list[str]]  # a table: rows; options: list
    drift: list[dict[str, JsonValue]]  # per step: rung, point, attempt. No values (R18)
    reason: str = ""
    human: list[dict[str, JsonValue]] = field(
        default_factory=list
    )  # R17: take-overs + option choices ("kind": "option"); [] = alone
    failure: dict[str, JsonValue] | None = None  # {step, action, expected, observed} if not SUCCESS
    recoveries: int = 0  # R17 recoverable errors fixed by a re-login
    cleanup: str = ""  # "" = no cleanup steps (or never logged in) | "done" | "failed: <why>"

    @property
    def outputs_line(self) -> str:
        head = "outputs" if self.status == "SUCCESS" else "partial outputs (run did not succeed)"
        return f"{head}: {self.outputs}"

    @property
    def summary(self) -> str:
        """`SUCCESS`, or e.g. `SUCCESS (human input at step 2; human intervened at step 4)`:
        "input" = a mid-run option choice (kind "option"), "intervened" = a take-over."""
        parts = []
        for words, picked in (("human input", True), ("human intervened", False)):
            hits = [h for h in self.human if (h.get("kind") == "option") == picked]
            steps = [str(h["step"] + 1) for h in hits]  # type: ignore[operator]
            if steps:
                plural = "s" if len(steps) > 1 else ""
                parts.append(f"{words} at step{plural} {', '.join(steps)}")
        return f"{self.status} ({'; '.join(parts)})" if parts else self.status
