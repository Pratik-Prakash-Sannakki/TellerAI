"""Playwright, no decisions: the open session, the site lock, our own input, native dropdowns.

Imports only ``cua.vision`` and ``cua.config`` (see ``README.md``).
"""

from __future__ import annotations

from cua.browser.dropdown import (
    DROPDOWNS_JS,
    DROPDOWNS_WITH_BOX_JS,
    SELECT_AT_INDEX_JS,
    SELECT_AT_POINT_JS,
    choose_option_at_index,
    choose_option_at_point,
    list_options,
    read_dropdowns,
)
from cua.browser.input import act, into_box, wait_for_change
from cua.browser.session import Session, check_viewport, handback_dir, open_session
from cua.browser.site_lock import SiteLock

__all__ = [
    "DROPDOWNS_JS",
    "DROPDOWNS_WITH_BOX_JS",
    "SELECT_AT_INDEX_JS",
    "SELECT_AT_POINT_JS",
    "Session",
    "SiteLock",
    "act",
    "check_viewport",
    "choose_option_at_index",
    "choose_option_at_point",
    "handback_dir",
    "into_box",
    "list_options",
    "open_session",
    "read_dropdowns",
    "wait_for_change",
]
