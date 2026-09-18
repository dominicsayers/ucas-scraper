import httpx

from v3.utils.fetcher.fetcher_config import FetcherConfig
from v3.utils.fetcher.http_client import HttpClient


def _mock_client(handler: httpx.MockTransport | None = None) -> HttpClient:
    client = HttpClient(FetcherConfig(http2_enabled=False))
    if handler is not None:
        client.client = httpx.Client(transport=handler)
    return client


def test_get_returns_response() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(200, json={"ok": True})

    client = _mock_client(httpx.MockTransport(handle))

    response = client.get("https://example.com")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_post_returns_response() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"created": True})

    client = _mock_client(httpx.MockTransport(handle))

    response = client.post("https://example.com", json={"key": "value"})

    assert response.status_code == 201
    assert response.json() == {"created": True}


def test_close_closes_underlying_client() -> None:
    client = _mock_client()

    client.close()

    assert client.client.is_closed
