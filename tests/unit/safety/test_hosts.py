"""host_allowed: only the site's own hosts (D15); about:blank always."""

from __future__ import annotations

from cua import config
from cua.config import SiteProfile
from cua.safety.hosts import host_allowed

SITE = SiteProfile(name="t", start_url="https://good.test/", allowed_hosts=frozenset({"good.test"}))


def test_only_allowed_hosts_and_blank() -> None:
    assert host_allowed("about:blank", SITE)
    assert host_allowed("https://good.test/x?y=1", SITE)
    assert not host_allowed("https://evil.test/", SITE)


def test_config_reexports_the_same_function() -> None:
    assert config.host_allowed is host_allowed
