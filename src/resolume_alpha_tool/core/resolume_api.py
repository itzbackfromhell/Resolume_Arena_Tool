"""Minimal local Resolume REST client scaffold.

This client deliberately keeps operations generic because Resolume API coverage
can differ by version and composition state. The processing tool remains useful
without this integration.
"""

from __future__ import annotations

from typing import Any

import requests

from .exceptions import ResolumeApiError
from .models import ResolumeConfig


class ResolumeClient:
    """Small wrapper around Resolume's local webserver API."""

    def __init__(self, config: ResolumeConfig | None = None) -> None:
        self.config = config or ResolumeConfig()

    def _url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.config.base_url}{normalized}"

    def get(self, path: str) -> Any:
        try:
            response = requests.get(self._url(path), timeout=self.config.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ResolumeApiError(f"Resolume GET failed for {path}: {exc}") from exc
        if not response.text:
            return None
        content_type = response.headers.get("content-type", "")
        return response.json() if "json" in content_type else response.text

    def put(self, path: str, payload: dict[str, Any]) -> Any:
        try:
            response = requests.put(
                self._url(path), json=payload, timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ResolumeApiError(f"Resolume PUT failed for {path}: {exc}") from exc
        return response.json() if response.text else None

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.post(
                self._url(path), json=payload or {}, timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ResolumeApiError(f"Resolume POST failed for {path}: {exc}") from exc
        return response.json() if response.text else None

    def healthcheck(self) -> bool:
        """Return True if a local Resolume webserver appears reachable."""

        for path in ("/api/v1/product", "/api/v1/composition", "/"):
            try:
                self.get(path)
                return True
            except ResolumeApiError:
                continue
        return False
