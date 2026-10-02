"""One folder per replay run (spec 3.5, 6.3): summary, drift, failure, the final screen, take-over
shots, a copy of the capability, and ``run.json``. Every value the human gave and every secret is
masked: ``***`` in text, a black box over its OCR text in a PNG.

Moved from notebooks/replay/replay.py 1621-1652 (``masked_outputs``, ``save_evidence``). The
redactor is replay's variant (``number=REPLAY_NUMBER``: whole numbers only, never 'rung1').
``LAST_RUN`` is ``ctx.last``; ``SECRETS`` is ``ctx.secrets``. ``run.json`` (Decision 5) is new:
``prompt_version`` null (replay has no prompt), model null (no LLM), config hash, git sha.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import yaml
from pydantic import JsonValue

from cua.evidence import Redact, _clean, _png, run_info
from cua.replay.context import Ctx
from cua.safety.redact import REPLAY_NUMBER, IdMask, OcrFn, safe_redactor
from cua.schema import ReplayResult
from cua.vision import ocr


def masked_outputs(
    outputs: dict[str, str | list[dict[str, str]] | list[str]],
) -> dict[str, JsonValue]:
    """Names and shape only: a value is ***, a table keeps its rows and columns, every cell ***,
    an option list keeps its length, every option ***."""
    return {
        k: (
            [dict.fromkeys(r, "***") if isinstance(r, dict) else "***" for r in v]
            if isinstance(v, list)
            else "***"
        )
        for k, v in outputs.items()
    }


def _drift_lines(
    result: ReplayResult, run: Path, redact: Redact, ocr_fn: OcrFn, ids: IdMask
) -> list[str]:
    lines: list[str] = []
    for item in result.drift:
        row = dict(item)
        if "shots" in row:
            n, shots = sum(1 for x in lines if '"shots"' in x), row["shots"]
            row["shots"] = {
                part: _png(run / f"take_over_{n}_{part}.png", shots.get(key), redact, ocr_fn, ids)  # type: ignore[union-attr, arg-type]
                for part, key in (("before", "start"), ("after", "end"))
            }
        lines.append(json.dumps(_clean(row, redact), default=str))
    return lines


def _summary(result: ReplayResult) -> dict[str, object]:
    return {
        "status": result.status,
        "reason": result.reason,
        "summary": result.summary,
        "outputs": masked_outputs(result.outputs),
        "human": result.human,
        "failing_step": result.failure["step"] if result.failure else None,
        "cleanup": result.cleanup,
    }


def save_evidence(
    ctx: Ctx,
    result: ReplayResult,
    cap_path: str | Path,
    out_dir: Path,
    ocr_fn: OcrFn | None = None,
) -> Path:
    """Write the last run's evidence, masked. Call right after `replay`, successful or not.
    Account ids (screen text, the capability name) keep only their last digits."""
    ocr_fn = ocr_fn or (lambda img: ocr(img, ctx.bcfg.ocr_min_score))
    ids = IdMask.for_site(ctx.site)
    redact = safe_redactor(ctx.last.values, ctx.secrets, ids, number=REPLAY_NUMBER)
    cap_path = Path(cap_path)
    name = ids.name(str(yaml.safe_load(cap_path.read_text()).get("name", cap_path.stem)))
    run = Path(out_dir) / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{name}"
    run.mkdir(parents=True, exist_ok=True)
    (run / "drift.jsonl").write_text(
        "\n".join(_drift_lines(result, run, redact, ocr_fn, ids)) + "\n"
    )
    summary = _clean(_summary(result), redact)
    (run / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if result.failure:
        failure = _clean(result.failure, redact)
        (run / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
    _png(run / "final.png", ctx.last.final, redact, ocr_fn, ids)
    (run / "capability.yaml").write_text(ids(cap_path.read_text()))
    info = run_info(None, None, (ctx.bcfg, ctx.cfg), ctx.site)
    (run / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return run
