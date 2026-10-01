"""Which hosts the browser may reach (D15). The allowlist itself lives in the site profile."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from cua.config import SiteProfile


def host_allowed(url: str, site: SiteProfile) -> bool:
    """True if `url`'s host is on the site's allowlist (D15). ``about:blank`` is always allowed
    (the browser's own blank starting page, not a real navigation anywhere)."""
    if url == "about:blank":
        return True
    return urlparse(url).hostname in site.allowed_hosts
