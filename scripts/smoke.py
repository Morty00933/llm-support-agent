#!/usr/bin/env python3
"""Simple smoke test that verifies the default stack on localhost:8080."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8080").rstrip("/")
TENANT_ID = os.environ.get("SMOKE_TENANT_ID", "1")
EMAIL = os.environ.get("SMOKE_EMAIL", "user@example.com")
PASSWORD = os.environ.get("SMOKE_PASSWORD", "secret")


def _request(method: str, path: str, *, headers: dict[str, str] | None = None, body: Any | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    payload: bytes | None = None
    req_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
            return {
                "status": response.status,
                "body": json.loads(text) if "application/json" in content_type else text,
            }
    except urllib.error.HTTPError as exc:  # pragma: no cover - depends on runtime
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"HTTP {exc.code} for {method} {path}: {detail}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - depends on runtime
        raise RuntimeError(f"Network error calling {method} {path}: {exc}") from exc


def main() -> int:
    print(f"→ GET /health @ {BASE_URL}")
    health = _request("GET", "/health")
    if health["status"] != 200 or health["body"] != "ok":
        raise RuntimeError(f"Health check failed: {health}")

    print("→ POST /v1/auth/login")
    login = _request(
        "POST",
        "/v1/auth/login",
        body={"email": EMAIL, "password": PASSWORD, "tenant": int(TENANT_ID)},
    )
    token = login["body"].get("access_token")
    if not token:
        raise RuntimeError(f"Login failed: {login}")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": TENANT_ID,
    }

    print("→ POST /v1/kb/upsert")
    upsert = _request(
        "POST",
        "/v1/kb/upsert",
        headers=headers,
        body={
            "source": "smoke-test",
            "chunks": [
                {"content": "Reset your password through the email link."},
                {"content": "Contact support if MFA codes fail."},
            ],
        },
    )
    summary = upsert["body"].get("summary", {})
    if upsert["status"] != 200 or not summary:
        raise RuntimeError(f"KB upsert failed: {upsert}")

    print("→ POST /v1/kb/search")
    search = _request(
        "POST",
        "/v1/kb/search",
        headers=headers,
        body={"query": "password reset", "limit": 3},
    )
    results = search["body"].get("results", [])
    if search["status"] != 200:
        raise RuntimeError(f"KB search failed: {search}")
    if not isinstance(results, list):
        raise RuntimeError(f"Unexpected KB search payload: {search}")
    print(f"✔ smoke test succeeded with {len(results)} search results")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - runtime guard
        print(f"✖ smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)
