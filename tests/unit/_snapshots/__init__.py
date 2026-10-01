"""Frozen notebook sources for the parity tests (step 10 replaced the notebooks with thin demos).

``DISCOVERY`` / ``REPLAY`` hold the verbatim top-level definitions the parity tests read, cut from
``notebooks/discovery/discovery.py`` and ``notebooks/replay/replay.py`` at commit fb1dcf7.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
DISCOVERY = HERE / "discovery_notebook.py.snapshot"
REPLAY = HERE / "replay_notebook.py.snapshot"
