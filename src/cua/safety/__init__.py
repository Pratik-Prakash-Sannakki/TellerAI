"""Safety: what may leave the tab (hosts, the two send gates) and keeping values out of what is
stored, logged or shown (redact)."""

from cua.safety.hosts import host_allowed
from cua.safety.mismatch import dropdown_options, mismatches
from cua.safety.redact import (
    NUMBER,
    REPLAY_NUMBER,
    hide_secrets,
    is_sensitive,
    mask_png,
    norm,
    redactor,
)
from cua.safety.request import Request, pretty, rebuilt, sent_fields
from cua.safety.send_guard import (
    DISCOVERY_OPTIONS,
    REPLAY_OPTIONS,
    ControlLike,
    GuardOptions,
    SendGuard,
    SendHooks,
    SendState,
)

__all__ = [
    "DISCOVERY_OPTIONS",
    "NUMBER",
    "REPLAY_NUMBER",
    "REPLAY_OPTIONS",
    "ControlLike",
    "GuardOptions",
    "Request",
    "SendGuard",
    "SendHooks",
    "SendState",
    "dropdown_options",
    "hide_secrets",
    "host_allowed",
    "is_sensitive",
    "mask_png",
    "mismatches",
    "norm",
    "pretty",
    "rebuilt",
    "redactor",
    "sent_fields",
]
