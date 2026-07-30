"""Shared async HTTP client with retries and timeouts."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ResilientHttpClient:
    """HTTP client with explicit timeouts and retry logic."""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3, retry_delay: float = 1.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        client = await self.get_client()
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                logger.warning("HTTP GET failed (attempt %s/%s) %s: %s", attempt, self.max_retries, url, exc)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)

        logger.error("HTTP GET exhausted retries for %s: %s", url, last_error)
        return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
