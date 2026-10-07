#!/usr/bin/env python3
"""Fetch British IPA from Youdao as a non-persistent runtime fallback.

Only British-pronunciation fields are accepted. Query failures are classified so
callers can distinguish a genuine no-IPA response from DNS/network/HTTP/schema
failures and hand unresolved lemmas to a host-level web fallback when available.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

YOUDAO_JSONAPI_URL = "https://dict.youdao.com/jsonapi_s"
DEFAULT_TIMEOUT_SECONDS = 3.0

STATUS_FOUND = "found"
STATUS_NO_UK_IPA = "no_uk_ipa"
STATUS_HTTP_ERROR = "http_error"
STATUS_DNS_ERROR = "dns_error"
STATUS_NETWORK_ERROR = "network_error"
STATUS_TIMEOUT = "timeout"
STATUS_INVALID_JSON = "invalid_json"
STATUS_INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True)
class YoudaoIpaResult:
    status: str
    ipa: Optional[str] = None
    detail: str = ""
    http_status: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"status": self.status, "ipa": self.ipa, "detail": self.detail}
        if self.http_status is not None:
            data["http_status"] = self.http_status
        return data


def ipa_inner_value(value: Any) -> str:
    """Return a pronunciation string without surrounding slash delimiters."""
    if not isinstance(value, str):
        return ""
    inner = value.strip()
    while inner.startswith("/"):
        inner = inner[1:].lstrip()
    while inner.endswith("/"):
        inner = inner[:-1].rstrip()
    return inner


def normalise_youdao_ipa(value: Any) -> str:
    """Apply mechanical notation cleanup only; never alter phoneme identity."""
    inner = ipa_inner_value(value)
    if not inner:
        return ""
    inner = inner.replace("'", "\u02c8")
    inner = inner.replace("\u2019", "\u02c8")
    inner = inner.replace("\u02bc", "\u02c8")
    inner = inner.replace(",", "\u02cc")
    return inner.strip()


def _first_string(value: Any) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def extract_uk_phone(payload: Any) -> Optional[str]:
    """Extract a British phone from supported Youdao response shapes."""
    if not isinstance(payload, dict):
        return None

    simple = payload.get("simple")
    if isinstance(simple, dict):
        words = simple.get("word")
        if isinstance(words, list):
            for item in words:
                if not isinstance(item, dict):
                    continue
                for key in ("ukphone", "ukPhone", "ukPhonetic"):
                    value = _first_string(item.get(key))
                    if value:
                        return value

    basic = payload.get("basic")
    if isinstance(basic, dict):
        for key in ("ukPhonetic", "ukphone", "ukPhone"):
            value = _first_string(basic.get(key))
            if value:
                return value

    def walk(node: Any) -> Optional[str]:
        if isinstance(node, dict):
            for key in ("ukPhonetic", "ukphone", "ukPhone"):
                value = _first_string(node.get(key))
                if value:
                    return value
            for child in node.values():
                found = walk(child)
                if found:
                    return found
        elif isinstance(node, list):
            for child in node:
                found = walk(child)
                if found:
                    return found
        return None

    return walk(payload)


def _is_dns_error(exc: BaseException) -> bool:
    if isinstance(exc, socket.gaierror):
        return True
    reason = getattr(exc, "reason", None)
    return isinstance(reason, socket.gaierror)


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    reason = getattr(exc, "reason", None)
    return isinstance(reason, (TimeoutError, socket.timeout))


def query_youdao_uk_ipa_result(word: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> YoudaoIpaResult:
    """Return a structured Youdao result without persisting anything."""
    if not isinstance(word, str) or not word.strip():
        return YoudaoIpaResult(STATUS_INVALID_RESPONSE, detail="empty query")

    query = urlencode({"doctype": "json", "jsonversion": "4", "q": word.strip()})
    request = Request(
        f"{YOUDAO_JSONAPI_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            try:
                payload = json.load(response)
            except (json.JSONDecodeError, ValueError) as exc:
                return YoudaoIpaResult(STATUS_INVALID_JSON, detail=str(exc))
    except HTTPError as exc:
        return YoudaoIpaResult(
            STATUS_HTTP_ERROR,
            detail=f"HTTP {exc.code}",
            http_status=exc.code,
        )
    except URLError as exc:
        if _is_dns_error(exc):
            return YoudaoIpaResult(STATUS_DNS_ERROR, detail=str(exc.reason))
        if _is_timeout_error(exc):
            return YoudaoIpaResult(STATUS_TIMEOUT, detail=str(exc.reason))
        return YoudaoIpaResult(STATUS_NETWORK_ERROR, detail=str(exc.reason))
    except (TimeoutError, socket.timeout) as exc:
        return YoudaoIpaResult(STATUS_TIMEOUT, detail=str(exc))
    except OSError as exc:
        if _is_dns_error(exc):
            return YoudaoIpaResult(STATUS_DNS_ERROR, detail=str(exc))
        return YoudaoIpaResult(STATUS_NETWORK_ERROR, detail=str(exc))

    if not isinstance(payload, dict):
        return YoudaoIpaResult(STATUS_INVALID_RESPONSE, detail="top-level JSON is not an object")

    raw = extract_uk_phone(payload)
    normalized = normalise_youdao_ipa(raw)
    if not normalized:
        return YoudaoIpaResult(STATUS_NO_UK_IPA, detail="no supported British-pronunciation field")
    return YoudaoIpaResult(STATUS_FOUND, ipa=normalized)


def query_youdao_uk_ipa(word: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Optional[str]:
    """Backward-compatible convenience wrapper returning IPA or None."""
    result = query_youdao_uk_ipa_result(word, timeout=timeout)
    return result.ipa if result.status == STATUS_FOUND else None
