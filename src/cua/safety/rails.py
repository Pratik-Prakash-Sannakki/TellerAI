"""Guardrails at discovery's edges.

Output rail (this part): the agent's final answer is the only discovery text that leaves. Card
numbers, SSNs and unmasked account ids are masked; a credential or a secret value withholds the
whole answer. Pure Python, no NeMo: a regex needs no LLM round trip.

Spec: docs/superpowers/specs/2026-10-03-nemo-guardrails-design.md
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from cua.safety.redact import IdMask

WITHHELD = "Response withheld: it looked like it contained a credential."
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-(\d{4})(?!\d)")
CREDENTIAL = re.compile(r"\b(?:password|passwd|pwd|token|api[_-]?key|secret)\s*[:=]\s*\S+", re.I)

# Very short secret values (a 1-2 character password) withhold aggressively by design: fail safe.
# CREDENTIAL needs ':' or '=' after the keyword; a known secret value is caught by the secret
# check whatever the wording.

# Luhn algorithm constants
LUHN_MULTIPLIER = 2
LUHN_THRESHOLD = 9

# Card number digit length constraints
MIN_CARD_DIGITS = 13
MAX_CARD_DIGITS = 19


@dataclass(frozen=True)
class OutputVerdict:
    answer: str
    withheld: bool
    hits: tuple[str, ...]


def _luhn(digits: str) -> bool:
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d) * (LUHN_MULTIPLIER if i % 2 else 1)
        total += n - LUHN_THRESHOLD if n > LUHN_THRESHOLD else n
    return total % 10 == 0


def _cards(text: str, hits: list[str]) -> str:
    """Mask every Luhn-valid 13-19 digit card number. A separated run can swallow neighbouring
    digits ("4111 1111 1111 1111 12/25"), so within each run try every window of whole digit
    groups, longest first. A run with no Luhn-valid window is left alone (ids and references are
    long digit runs too; the site's id mask handles those)."""

    def mask(m: re.Match[str]) -> str:
        groups = [(g.start(), g.end()) for g in re.finditer(r"\d+", m.group())]
        out, i, pos = [], 0, 0
        while i < len(groups):
            found = None
            for j in range(len(groups), i, -1):  # longest window starting at group i first
                digits = "".join(m.group()[a:b] for a, b in groups[i:j])
                if MIN_CARD_DIGITS <= len(digits) <= MAX_CARD_DIGITS and _luhn(digits):
                    found = (j, digits)
                    break
            if found is None:
                i += 1
                continue
            j, digits = found
            hits.append("card_number")
            out.append(m.group()[pos : groups[i][0]] + "***" + digits[-4:])
            pos, i = groups[j - 1][1], j
        return "".join(out) + m.group()[pos:]

    return CARD.sub(mask, text)


def check_output(
    answer: str,
    ids: IdMask,
    secrets: Mapping[str, str] | None = None,
) -> OutputVerdict:
    """The answer, masked; withheld on credential or secret value. ``hits``: rule names only."""
    secrets = secrets or {}
    if CREDENTIAL.search(answer):
        return OutputVerdict(WITHHELD, True, ("credential",))
    if any(v and v in answer for v in secrets.values()):
        return OutputVerdict(WITHHELD, True, ("secret",))
    hits: list[str] = []
    text = _cards(answer, hits)
    if SSN.search(text):
        hits.append("ssn")
        text = SSN.sub(lambda m: "***-**-" + m.group(1), text)
    masked = ids(text)
    if masked != text:
        hits.append("account_id")
    return OutputVerdict(masked, False, tuple(dict.fromkeys(hits)))


def safe_output(
    answer: str, ids: IdMask, secrets: Mapping[str, str] | None = None
) -> OutputVerdict:
    """``check_output`` that fails CLOSED: any error withholds the answer and logs a warning
    naming the error type only (never a value)."""
    try:
        return check_output(answer, ids, secrets)
    except Exception as e:  # noqa: BLE001  fail closed
        log = logging.getLogger(__name__)
        log.warning("output rail failed (%s); answer withheld", type(e).__name__)
        return OutputVerdict(WITHHELD, True, ("error",))


# --- input rail ------------------------------------------------------------------------------

REFUSALS = {
    "off_topic": "I'm Teller, a banking agent. I can only do banking tasks on this site.",
    "jailbreak": "I can't change my role or ignore my safety rules.",
    "steering": "I can't hand over control or skip the approval gates from a goal. Give me the"
    " banking task itself.",
    "sensitive": "I can only carry out a clear banking task. Please describe the exact task.",
    "empty_goal": "Give me a banking task to do.",
    "guardrails_unavailable": "Guardrails are unavailable, so I won't start. Try again later.",
}
SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass(frozen=True)
class RailVerdict:
    allowed: bool
    rail: str | None = None
    score: float | None = None
    message: str | None = None


class Classifier(Protocol):
    async def classify(self, text: str) -> tuple[str | None, float]: ...


def sentences(goal: str) -> list[str]:
    return [s.strip() for s in SPLIT.split(goal) if s.strip()]


def _refuse(rail: str, score: float | None = None) -> RailVerdict:
    return RailVerdict(False, rail, score, REFUSALS[rail])


async def _classify_all(goal: str, classifier: Classifier) -> RailVerdict:
    parts = sentences(goal)
    result: tuple[str, float] | None = None
    allowed_scores: list[float] = []
    for text in [*parts, goal] if len(parts) > 1 else [goal]:
        rail, score = await classifier.classify(text)
        if rail is not None and result is None:
            result = (rail, score)
        elif rail is None:
            allowed_scores.append(score)
    if result:
        return _refuse(result[0], result[1])
    return RailVerdict(True, score=min(allowed_scores, default=None))


async def check_goal(
    goal: str, mode: str, classifier: Classifier | None, timeout_s: float = 20.0
) -> RailVerdict:
    """Before the browser or the agent: refuse an off-topic, jailbreak, steering or sensitive
    goal. Fails CLOSED: any classifier error or a timeout refuses (``guardrails_unavailable``).
    ``classifier`` None = the extra is not installed: ``off``/``on`` allow, ``required`` refuses."""
    if mode == "off":
        return RailVerdict(True)
    if not goal.strip():
        return _refuse("empty_goal")
    if classifier is None:
        return _refuse("guardrails_unavailable") if mode == "required" else RailVerdict(True)
    try:
        return await asyncio.wait_for(_classify_all(goal, classifier), timeout_s)
    except Exception:  # noqa: BLE001  the type only; fail closed
        return _refuse("guardrails_unavailable")
