"""Клиент Zendesk Support (v2) с Basic-аутентификацией."""

from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import httpx


class ZendeskError(RuntimeError):
    pass


class ZendeskClient:
    def __init__(
        self, subdomain: str, email: str, api_token: str, timeout: float = 30.0
    ):
        """
        subdomain: поддомен вашей учётки — например, 'acme' для acme.zendesk.com
        email: агентский email
        api_token: созданный API токен (не пароль!)
        """
        self.base_url = f"https://{subdomain}.zendesk.com"
        self.timeout = timeout
        token = base64.b64encode(f"{email}/token:{api_token}".encode("utf-8")).decode(
            "ascii"
        )
        self._auth_header = {"Authorization": f"Basic {token}"}
        self._common_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self._auth_header,
        }

    async def _request(
        self, method: str, path: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.request(
                method, url, json=json, headers=self._common_headers
            )
            if r.status_code >= 400:
                try:
                    detail = r.json()
                except Exception:
                    detail = {"text": r.text}
                raise ZendeskError(f"Zendesk API error {r.status_code}: {detail}")
            try:
                return r.json()
            except Exception:
                return {}

    async def create_ticket(
        self,
        *,
        subject: str,
        comment: str,
        requester_email: Optional[str] = None,
        priority: Optional[str] = None,  # "low"|"normal"|"high"|"urgent"
        tags: Optional[list[str]] = None,
        custom_fields: Optional[list[dict]] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт тикет: возвращает JSON с ticket {id, url, ...}
        """
        ticket: Dict[str, Any] = {
            "subject": subject,
            "comment": {"body": comment},
        }
        if requester_email:
            ticket["requester"] = {"email": requester_email}
        if priority:
            ticket["priority"] = priority
        if tags:
            ticket["tags"] = tags
        if custom_fields:
            ticket["custom_fields"] = custom_fields

        payload = {"ticket": ticket}
        return await self._request("POST", "/api/v2/tickets.json", json=payload)

    async def add_comment(
        self, ticket_id: int, body: str, public: bool = True
    ) -> Dict[str, Any]:
        payload = {"ticket": {"comment": {"body": body, "public": public}}}
        return await self._request(
            "PUT", f"/api/v2/tickets/{ticket_id}.json", json=payload
        )
