"""LatestScreenshotOnly keeps only the newest image in the model's context."""
import ast
from pathlib import Path
from types import SimpleNamespace

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import HumanMessage, ToolMessage

SRC = Path(__file__).parents[2] / "notebooks/discovery/discovery.py"


def _cls():
    tree = ast.parse(SRC.read_text())
    node = next(n for n in tree.body if getattr(n, "name", None) == "LatestScreenshotOnly")
    ns = {"AgentMiddleware": AgentMiddleware}
    exec(compile(ast.Module([node], []), str(SRC), "exec"), ns)
    return ns["LatestScreenshotOnly"]


def _shot(i: int) -> ToolMessage:
    return ToolMessage(tool_call_id=str(i), content=[{"type": "text", "text": f"look {i}"},
                                                     {"type": "image", "base64": "x", "mime_type": "image/png"}])


def test_only_last_image_survives() -> None:
    msgs = [HumanMessage("goal"), _shot(1), _shot(2), _shot(3)]
    req = SimpleNamespace(messages=msgs, override=lambda messages: messages)
    out = _cls()()._trim(req)
    images = [sum(b.get("type") == "image" for b in m.content) for m in out[1:]]
    assert images == [0, 0, 1]
    assert [m.content[0]["text"] for m in out[1:]] == ["look 1", "look 2", "look 3"]
