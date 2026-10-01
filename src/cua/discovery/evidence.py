"""One masked folder per discovery run: goal, answer, events, transcript, crops, take-over shots,
the final screen, the saved capability with its crops, ``summary.json`` and ``run.json``.

Moved from discovery.py 2257-2305 (``_text``, ``transcript``, ``save_evidence``). ``HANDOFF`` is
``ctx.run``, ``SECRETS`` is ``ctx.secrets``; ``_clean``/``_png`` are the shared ``cua.evidence``
ones (``_png`` takes the OCR function the notebook read as a global). ``run.json`` is new
(Decision 5): prompt version, model name, config hash, git sha. Never a value.
"""

from __future__ import annotations

import json
import shutil
import time
from collections.abc import Sequence
from pathlib import Path

from cua.discovery.agent.prompt import PROMPT_VERSION
from cua.discovery.context import Ctx
from cua.discovery.recorder.events import input_name
from cua.discovery.run import DiscoveryRun
from cua.evidence import Redact, _clean, _png, run_info
from cua.safety.redact import OcrFn, redactor
from cua.vision import ocr


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    return " ".join(
        b.get("text", "")
        for b in content  # type: ignore[attr-defined]
        if isinstance(b, dict) and b.get("type") == "text"
    )


def transcript(messages: Sequence[object], redact: Redact) -> list[dict[str, object]]:
    """What the agent said and which tools it called, in order. Tool results (screenshots)
    skipped."""
    ai = [m for m in messages if m.type == "ai"]  # type: ignore[attr-defined]
    return [
        {"i": i, "text": redact(_text(m.content)), "tools": [c["name"] for c in m.tool_calls]}  # type: ignore[attr-defined]
        for i, m in enumerate(ai)
    ]


def _events(
    run: DiscoveryRun, folder: Path, redact: Redact, ocr_fn: OcrFn
) -> tuple[list[str], list[dict[str, object]]]:
    lines: list[str] = []
    takeovers: list[dict[str, object]] = []
    for i, event in enumerate(run.log):
        ev = dict(event)
        if ev["tool"] == "take_over":
            n = len(takeovers)
            reason = ev["args"].get("reason", "")  # type: ignore[attr-defined]
            takeovers.append({"reason": reason, "actions": ev.get("actions", [])})
            for key, part in (("shot_before", "before"), ("shot_after", "after")):
                ev[key] = _png(folder / f"take_over_{n}_{part}.png", ev.get(key), redact, ocr_fn)  # type: ignore[arg-type]
        ev["crop"] = _png(folder / f"step_{i}.png", ev.get("crop"), redact, ocr_fn)  # type: ignore[arg-type]
        lines.append(json.dumps(_clean(ev, redact), default=str))
    return lines, takeovers


def _copy_capability(folder: Path, capability: Path, yml: str) -> None:
    """The saved artifact + its crops, paths still relative to it."""
    (folder / "capability.yaml").write_text(yml)
    crops = capability.parent / "crops" / capability.stem
    if crops.is_dir():
        shutil.copytree(crops, folder / "crops" / crops.name)


def _summary(
    run: DiscoveryRun, takeovers: list[dict[str, object]], capability: Path | None
) -> dict[str, object]:
    head = run.answer.split(":", 1)[0]
    return {
        "status": head if head in ("STUCK", "DECLINED") else "done" if run.answer else "no answer",
        "events": len(run.log),
        "take_over": bool(takeovers),
        "take_overs": takeovers,
        "capability_saved": str(capability) if capability else None,
    }


def _folder(out_dir: Path, run: DiscoveryRun, redact: Redact) -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    folder = out_dir / f"{stamp}-{input_name(redact(run.goal))[:40]}"  # the name is masked too
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_evidence(
    ctx: Ctx,
    out_dir: Path,
    capability: Path | None = None,
    model: str | None = None,
    ocr_fn: OcrFn | None = None,
) -> Path:
    """Write this run's evidence, masked. Call after any run, successful or not. ``model`` is the
    model name for ``run.json``; ``ocr_fn`` defaults to the shared OCR at the browser's min score.
    """
    run = ctx.run
    ocr_fn = ocr_fn or (lambda img: ocr(img, ctx.session.cfg.ocr_min_score))
    redact = redactor(run.redact | {v for v in ctx.secrets.values() if v})
    capability = Path(capability) if capability else None
    yml = capability.read_text() if capability else ""
    if redact(yml) != yml:  # the artifact must hold names only: never copy a leak
        raise ValueError("a run value is in the artifact")
    folder = _folder(Path(out_dir), run, redact)
    lines, takeovers = _events(run, folder, redact, ocr_fn)
    (folder / "goal.txt").write_text(redact(run.goal) + "\n")
    (folder / "answer.txt").write_text(redact(run.answer) + "\n")
    (folder / "events.jsonl").write_text("\n".join(lines) + "\n")
    rows = transcript(run.messages, redact)
    (folder / "transcript.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    _png(folder / "final.png", run.final_shot, redact, ocr_fn)
    if capability:
        _copy_capability(folder, capability, yml)
    summary = _clean(_summary(run, takeovers, capability), redact)
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    info = run_info(PROMPT_VERSION, model, (ctx.session.cfg, ctx.cfg), ctx.site)
    (folder / "run.json").write_text(json.dumps(info, indent=2) + "\n")
    return folder
