"""What a held request sends, and the same request rebuilt with edited values.

Moved unchanged from notebooks/discovery/discovery.py 724-770 (== replay.py 388-432 apart from
docstrings). Generic: query string, form body, or JSON body (nested keys dotted).
"""

from __future__ import annotations

import functools
import json
import re
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlparse

JsonObj = dict[str, object]


class Request(Protocol):
    """The fields of a ``playwright.async_api.Request`` the guard reads."""

    @property
    def url(self) -> str: ...

    @property
    def method(self) -> str: ...

    @property
    def post_data(self) -> str | None: ...


def _flat(obj: JsonObj, pre: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out |= _flat(v, f"{pre}{k}.")
        elif not isinstance(v, list):
            out[f"{pre}{k}"] = "" if v is None else str(v)
    return out


def _json(body: str | None) -> JsonObj | None:
    try:
        data = json.loads(body or "")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def sent_fields(req: Request) -> dict[str, str]:
    """Every value a request sends, from its query, a form body, or a JSON body (nested keys
    dotted)."""
    data = _json(req.post_data)
    body = _flat(data) if data is not None else dict(parse_qsl(req.post_data or ""))
    return dict(parse_qsl(urlparse(req.url).query)) | body


def rebuilt(req: Request, fields: dict[str, str]) -> tuple[str, str | None]:
    """The request's url and body with these values put back in, in the same format."""
    u = urlparse(req.url)
    query = {k: fields.get(k, v) for k, v in parse_qsl(u.query)}
    url = u._replace(query=urlencode(query)).geturl() if query else req.url
    data = _json(req.post_data)
    if data is not None:
        for key in _flat(data):
            *path, last = key.split(".")
            node = functools.reduce(lambda d, p: d[p], path, data)  # type: ignore[arg-type,return-value]
            old, new = node.get(last), fields.get(key, "")
            is_num = isinstance(old, (int, float)) and not isinstance(old, bool)
            node[last] = type(old)(new) if is_num and new else new  # type: ignore[call-arg]
        return url, json.dumps(data)
    form = dict(parse_qsl(req.post_data or ""))
    return url, (
        urlencode({k: fields.get(k, v) for k, v in form.items()}) if form else req.post_data
    )


def pretty(key: str) -> str:
    """'address.zipCode' -> 'Address zip code' (for the human; the key itself is kept)."""
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key.replace(".", " ").replace("_", " ")).split()
    return " ".join(words).capitalize()
