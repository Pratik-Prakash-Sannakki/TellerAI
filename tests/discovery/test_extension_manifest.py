"""The hand-back extension never touches any site: no content scripts, no host access."""
import json
from pathlib import Path

EXT = Path(__file__).parents[2] / "extensions/handback"


def test_manifest_has_no_site_access() -> None:
    manifest = json.loads((EXT / "manifest.json").read_text())
    assert manifest["manifest_version"] == 3 and manifest["name"] == "Agent hand-back"
    assert "content_scripts" not in manifest and "host_permissions" not in manifest
    assert not [p for p in manifest.get("permissions", []) if "://" in p or p in {"<all_urls>", "tabs", "scripting"}]
    assert manifest["background"]["service_worker"] == "background.js"
    for rel in [*manifest["icons"].values(), manifest["background"]["service_worker"]]:
        assert (EXT / rel).is_file()
