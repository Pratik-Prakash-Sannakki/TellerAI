"""``cua eval``: replay a capability N times, then say how stable it is (the "multi-run stability"
stretch goal). Pure: no browser, no LLM. The CLI runs the replays and hands the results here.

What it measures: status counts and success rate, runs a human had to help, a per-step rung
histogram from each run's drift log, and the drift signal itself: ``fallback_steps``, the steps
whose first-choice rung (``rung1`` / ``table``) was not used every time. Given the capability, a
step whose target has no OCR text (an empty login box) has rung 2 as its first choice, so rung 2
there is not drift. Outputs are compared in memory only; the report keeps one bool per output
name and, for an unstable one, a value-free description of what differs (row counts, column
names, cell shape and length per run), never a value.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import JsonValue

from cua.replay.loader import PLACEHOLDER, step_inputs
from cua.safety.redact import REPLAY_NUMBER, redactor
from cua.schema import Capability, ReplayResult
from cua.vision.table import cell_shape

FIRST_CHOICE = ("rung1", "table")  # "rung1+anchor" is still rung 1, disambiguated by a label
NO_OCR_FIRST = (*FIRST_CHOICE, "rung2")  # a target with no OCR text of its own starts at rung 2
NOT_A_LOCATE = ("-", "recover", "skipped")  # no target, a re-login, a cleanup step not yet run

Histogram = dict[int, dict[str, int]]


@dataclass(frozen=True)
class EvalReport:
    runs: int
    status_counts: dict[str, int]
    success_rate: float
    assisted: int  # runs where a human stepped in (result.human non-empty)
    rungs: Histogram  # main steps: step index -> {rung: rows}
    cleanup_rungs: Histogram  # the cleanup steps (the final logout), kept apart
    fallback_steps: list[int]  # the drift signal: first-choice rung not used every time
    output_stable: dict[str, bool]  # per output name: same value in every SUCCESS run
    outputs_stable: bool
    flaky: bool  # not every run had the same status
    output_diffs: dict[str, str] = field(default_factory=dict)  # unstable name -> what differs

    @property
    def all_success(self) -> bool:
        return self.runs > 0 and self.status_counts.get("SUCCESS", 0) == self.runs


def _histograms(results: Iterable[ReplayResult]) -> tuple[Histogram, Histogram]:
    main: dict[int, Counter[str]] = {}
    clean: dict[int, Counter[str]] = {}
    for result in results:
        for row in result.drift:
            rung, step = str(row.get("rung", "")), row.get("step")
            if not isinstance(step, int) or rung == "skipped":
                continue
            into = clean if row.get("cleanup") else main
            into.setdefault(step, Counter())[rung] += 1
    return ({s: dict(c) for s, c in sorted(h.items())} for h in (main, clean))  # type: ignore[return-value]


def _is_fallback(rung: str, first: tuple[str, ...] = FIRST_CHOICE) -> bool:
    return rung not in NOT_A_LOCATE and not rung.startswith(first)


def _no_ocr_steps(cap: Capability | None) -> set[int]:
    """Steps whose target has no OCR text: rung 1 cannot apply, so rung 2 is the first choice."""
    if cap is None:
        return set()
    return {
        i
        for i, step in enumerate(cap.steps)
        if (target := getattr(step, "target", None)) is not None
        and target.ocr_text is None
        and target.anchor is not None
    }


def fallback_steps(rungs: Histogram, cap: Capability | None = None) -> list[int]:
    no_ocr = _no_ocr_steps(cap)
    return [
        step
        for step, seen in rungs.items()
        if any(_is_fallback(r, NO_OCR_FIRST if step in no_ocr else FIRST_CHOICE) for r in seen)
    ]


def _output_stability(results: list[ReplayResult]) -> dict[str, bool]:
    wins = [r.outputs for r in results if r.status == "SUCCESS"]
    names = sorted({k for out in wins for k in out})
    return {
        n: all(n in out for out in wins) and all(out.get(n) == wins[0].get(n) for out in wins)
        for n in names
    }


def _per_run(items: Iterable[object]) -> str:
    return "[" + ", ".join(str(i) for i in items) + "]"


def _cells(values: list[str | None]) -> str:
    shapes = ", ".join("-" if v is None else cell_shape(v) for v in values)
    lengths = ", ".join("-" if v is None else str(len(v)) for v in values)
    return f"shape {shapes}; length {lengths}"


def _table_diff(tables: list[list[dict[str, str]]]) -> str:
    parts = [f"rows per run: {_per_run(len(t) for t in tables)}"]
    common = min(len(t) for t in tables)
    columns = list(dict.fromkeys(c for t in tables for row in t[:common] for c in row))
    differ = []
    for col in columns:
        for i in range(common):
            cells = [t[i].get(col) for t in tables]
            if any(c != cells[0] for c in cells):
                differ.append(f"{col} (row {i + 1}: {_cells(cells)})")
                break
    if differ:
        parts.append("differ in " + ", ".join(differ))
    return "; ".join(parts)


def _describe(values: list[object]) -> str:
    """What differs between runs for one output, never a value: counts, names, shapes, lengths."""
    lists = [v for v in values if isinstance(v, list)]
    if len(lists) == len(values):
        if all(isinstance(r, dict) for v in lists for r in v):
            return _table_diff([[{str(k): str(c) for k, c in r.items()} for r in v] for v in lists])
        return f"items per run: {_per_run(len(v) for v in lists)}"
    texts = [v for v in values if isinstance(v, str)]
    if len(texts) == len(values):
        shapes, lengths = _per_run(cell_shape(t) for t in texts), _per_run(len(t) for t in texts)
        return f"shape per run: {shapes}; length per run: {lengths}"
    return f"type per run: {_per_run(type(v).__name__ for v in values)}"


def _output_diffs(results: list[ReplayResult], stable: Mapping[str, bool]) -> dict[str, str]:
    wins = [r.outputs for r in results if r.status == "SUCCESS"]
    diffs: dict[str, str] = {}
    for name in (n for n, ok in stable.items() if not ok):
        missing = [i for i, out in enumerate(wins, start=1) if name not in out]
        diffs[name] = (
            f"missing in runs: {_per_run(missing)}"
            if missing
            else _describe([out[name] for out in wins])
        )
    return diffs


def summarize(results: list[ReplayResult], cap: Capability | None = None) -> EvalReport:
    counts = dict(Counter(r.status for r in results))
    rungs, cleanup = _histograms(results)
    stable = _output_stability(results)
    wins = counts.get("SUCCESS", 0)
    return EvalReport(
        runs=len(results),
        status_counts=counts,
        success_rate=wins / len(results) if results else 0.0,
        assisted=sum(1 for r in results if r.human),
        rungs=rungs,
        cleanup_rungs=cleanup,
        fallback_steps=fallback_steps(rungs, cap),
        output_stable=stable,
        outputs_stable=wins > 0 and all(stable.values()),
        flaky=len(counts) > 1,
        output_diffs=_output_diffs(results, stable),
    )


def _hist_line(seen: Mapping[str, int]) -> str:
    return ", ".join(f"{rung} x{n}" for rung, n in sorted(seen.items()))


def render(report: EvalReport) -> str:
    """A short plain-text table for the terminal. Step numbers are 1-based, like the CLI's."""
    counts = "  ".join(f"{s} {n}" for s, n in sorted(report.status_counts.items()))
    unstable = [n for n, ok in report.output_stable.items() if not ok]
    lines = [
        f"runs: {report.runs}  |  {counts}  |  success rate: {report.success_rate:.0%}",
        f"flaky: {'yes' if report.flaky else 'no'}  |  human assisted: {report.assisted}",
        f"outputs stable: {'yes' if report.outputs_stable else 'no'}"
        + (f" (differ: {', '.join(unstable)})" if unstable else ""),
        *(f"  {name}: {diff}" for name, diff in report.output_diffs.items()),
        "step  rungs",
    ]
    for step, seen in report.rungs.items():
        mark = "  <- fallback" if step in report.fallback_steps else ""
        lines.append(f"{step + 1:>4}  {_hist_line(seen)}{mark}")
    for step, seen in report.cleanup_rungs.items():
        lines.append(f"{step + 1:>4}  {_hist_line(seen)}  (cleanup)")
    drift = ", ".join(str(s + 1) for s in report.fallback_steps) or "none"
    lines.append(f"fallback steps (drift signal): {drift}")
    return "\n".join(lines)


def run_rows(results: list[ReplayResult], masks: list[set[str]]) -> list[dict[str, JsonValue]]:
    """Per run: status and reason, the reason masked with that run's own values + secrets."""
    rows: list[dict[str, JsonValue]] = []
    for n, (result, values) in enumerate(zip(results, masks, strict=True), start=1):
        redact = redactor({v for v in values if v}, number=REPLAY_NUMBER)
        rows.append({"run": n, "status": result.status, "reason": redact(result.reason)})
    return rows


def save_report(
    report: EvalReport,
    rows: list[dict[str, JsonValue]],
    name: str,
    out_dir: Path,
    info: Mapping[str, JsonValue],
) -> Path:
    """``<out_dir>/<UTC stamp>-<name>/report.json`` + ``run.json``. Never an output value."""
    folder = Path(out_dir) / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{name}"
    folder.mkdir(parents=True, exist_ok=True)
    body = {"report": asdict(report), "runs": rows}
    (folder / "report.json").write_text(json.dumps(body, indent=2) + "\n")
    (folder / "run.json").write_text(json.dumps(dict(info), indent=2) + "\n")
    return folder


def missing_inputs(cap: Capability, inputs: Mapping[str, str]) -> list[str]:
    """Every input the capability needs that ``inputs`` does not give (names in any case)."""
    given = {k.casefold() for k, v in inputs.items() if v}
    return [n for n in step_inputs(cap) if n.casefold() not in given]


def _uses_input(step: object) -> bool:
    dump = step.model_dump_json() if hasattr(step, "model_dump_json") else ""
    return any(not secret for secret, _ in PLACEHOLDER.findall(dump))


def sends_data(cap: Capability) -> bool:
    """A non-cleanup click after an input was typed or selected: a form submit, so a send that
    meets the two human gates. The login (secrets only) is not one."""
    filled = False
    for step in cap.steps:
        filled = filled or (step.action in ("type", "select") and _uses_input(step))
        if filled and step.action == "click" and not getattr(step, "cleanup", False):
            return True
    return False
