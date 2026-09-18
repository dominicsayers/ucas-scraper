from collections.abc import Callable
from typing import Any

import httpx
import pytest


class ScriptedHttpClient:
    """Test double for HttpClient driven by a shared, mutable script.

    Each call to get()/post() pops the next scripted item: an httpx.Response
    is returned, an Exception instance is raised. The script list is shared
    across reconnects, since Fetcher replaces self.client with a brand new
    HttpClient instance on every retry.
    """

    def __init__(self, script: list[httpx.Response | Exception]) -> None:
        self.script = script
        self.closed = False

    def get(self, _url: str, **_kwargs: Any) -> httpx.Response:
        return self._next()

    def post(self, _url: str, **_kwargs: Any) -> httpx.Response:
        return self._next()

    def close(self) -> None:
        self.closed = True

    def _next(self) -> httpx.Response:
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def scripted_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[list[httpx.Response | Exception]], None]:
    """Patch Fetcher's HttpClient with a scripted fake and disable sleeps."""

    def install(script: list[httpx.Response | Exception]) -> None:
        monkeypatch.setattr(
            "v3.utils.fetcher.fetcher.HttpClient",
            lambda _config: ScriptedHttpClient(script),
        )
        monkeypatch.setattr(
            "v3.utils.fetcher.fetcher.time.sleep", lambda _seconds: None
        )

    return install
