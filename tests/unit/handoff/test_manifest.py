"""The hand-back extension never touches any site: no content scripts, no host access.

Ported from tests/discovery/test_extension_manifest.py and tests/replay/test_handback_manifest.py
(identical copies).
"""

from __future__ import annotations

import json
from pathlib import Path

EXT = Path(__file__).parents[3] / "extensions/handback"
MV3 = 3


def test_manifest_has_no_site_access() -> None:
    manifest = json.loads((EXT / "manifest.json").read_text())
    assert manifest["manifest_version"] == MV3
    assert manifest["name"] == "Agent hand-back"
    assert "content_scripts" not in manifest
    assert "host_permissions" not in manifest
    forbidden = {"<all_urls>", "tabs", "scripting"}
    assert not [p for p in manifest.get("permissions", []) if "://" in p or p in forbidden]
    assert manifest["background"]["service_worker"] == "background.js"
    for rel in [*manifest["icons"].values(), manifest["background"]["service_worker"]]:
        assert (EXT / rel).is_file()
