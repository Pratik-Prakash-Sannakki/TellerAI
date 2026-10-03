"""NeMo Guardrails adapter for the discovery goal (optional ``rails`` extra)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

TAG = re.compile(r"^\s*(ALLOW|REFUSED (\w+))\s*$")


class NemoClassifier:
    """One NeMo ``LLMRails`` over ``configs/rails/``. Embeddings decide clear goals; below the
    similarity threshold NeMo asks ``llm`` (Haiku, injected: cua.safety never imports cua.llm)."""

    def __init__(self, config_dir: Path, llm: BaseChatModel | None) -> None:
        from nemoguardrails import LLMRails, RailsConfig  # noqa: PLC0415 (optional extra)

        self.rails = LLMRails(RailsConfig.from_path(str(config_dir)), llm=llm)

    async def classify(self, text: str) -> tuple[str | None, float]:
        res: Any = await self.rails.generate_async(messages=[{"role": "user", "content": text}])
        content = res["content"] if isinstance(res, dict) else str(res)
        m = TAG.match(content)
        if m is None:  # an untagged reply = NeMo did not map the goal to any intent: fail closed
            raise RuntimeError("guardrails returned no decision")
        return (m.group(2), 1.0) if m.group(2) else (None, 1.0)


def load_classifier(config_dir: Path, llm: BaseChatModel | None) -> NemoClassifier | None:
    """None when the ``rails`` extra is not installed."""
    try:
        import nemoguardrails  # noqa: F401, PLC0415
    except ImportError:
        return None
    return NemoClassifier(config_dir, llm)
