"""Лёгкий клиент Jira Cloud/Server (REST API v3 совместимо с Cloud)."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class JiraError(RuntimeError):
    pass


class JiraClient:
    def __init__(
        self, base_url: str, email: str, api_token: str, timeout: float = 30.0
    ):
        """
        base_url: например, https://your-domain.atlassian.net
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        token = base64.b64encode(f"{email}:{api_token}".encode("utf-8")).decode("ascii")
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
                except Exception as e:
                    logger.debug(f"Failed to parse error response JSON: {e}")
                    detail = {"text": r.text}
                raise JiraError(f"Jira API error {r.status_code}: {detail}")
            try:
                return r.json()
            except Exception as e:
                logger.debug(f"Failed to parse response JSON, returning empty dict: {e}")
                return {}

    async def create_issue(
        self,
        *,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        fields_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт задачу в Jira:
        returns JSON с полями issue (id, key, self, ...)
        """
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
        }
        if fields_extra:
            payload["fields"].update(fields_extra)
        return await self._request("POST", "/rest/api/3/issue", json=payload)

    async def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        payload = {"body": comment}
        return await self._request(
            "POST", f"/rest/api/3/issue/{issue_key}/comment", json=payload
        )

    async def transition_issue(
        self, issue_key: str, transition_id: str
    ) -> Dict[str, Any]:
        payload = {"transition": {"id": transition_id}}
        return await self._request(
            "POST", f"/rest/api/3/issue/{issue_key}/transitions", json=payload
        )
