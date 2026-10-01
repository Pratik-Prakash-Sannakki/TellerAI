"""A human in the loop: the control window, the hand-back toolbar button, the take-over pieces.

Imports only ``cua.config`` (plus Playwright's error type); see ``README.md``.
"""

from __future__ import annotations

from cua.handoff.control_window import (
    AGENT,
    REPLAY,
    ControlWindow,
    Side,
    Tab,
    discovery_control,
    replay_control,
)
from cua.handoff.extension import (
    Extension,
    button_clicked,
    ext_call,
    handback_button,
    watch_button,
)
from cua.handoff.takeover import hand_back, takeover_text, wait_held_send

__all__ = [
    "AGENT",
    "REPLAY",
    "ControlWindow",
    "Extension",
    "Side",
    "Tab",
    "button_clicked",
    "discovery_control",
    "ext_call",
    "hand_back",
    "handback_button",
    "replay_control",
    "takeover_text",
    "wait_held_send",
    "watch_button",
]
