from typing import Any
import httpx
from v1.utils.fetcher.fetcher_config import FetcherConfig


class HttpClient:
    """Wrapper for HTTP client operations"""

    def __init__(self, config: FetcherConfig):
        self.config = config
        self.client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """Create new HTTP client"""
        return httpx.Client(
            http2=self.config.http2_enabled, timeout=self.config.timeout
        )

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute GET request"""
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute POST request"""
        return self.client.post(url, **kwargs)
