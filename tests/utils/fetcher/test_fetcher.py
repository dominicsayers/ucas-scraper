import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from v3.utils.fetcher.fetcher import Fetcher, create_fetcher, main
from v3.utils.fetcher.fetcher_config import FetcherConfig, RateLimit
from v3.utils.fetcher.http_error import HttpError

ScriptInstaller = Callable[[list[httpx.Response | Exception]], None]


def _config(tmp_path: Path, **overrides: object) -> FetcherConfig:
    defaults: dict[str, object] = {"error_log_path": str(tmp_path / "errors.txt")}
    defaults.update(overrides)
    return FetcherConfig(**defaults)  # type: ignore[arg-type]


def test_fetch_returns_content_on_success(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"hello")])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch("https://example.com") == b"hello"


def test_fetch_returns_status_code_on_404(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(404, text="not found")])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch("https://example.com") == 404


def test_post_returns_content_on_success(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"created")])
    fetcher = Fetcher(_config(tmp_path))

    result = fetcher.post("https://example.com", payload={"a": 1}, headers={"X": "Y"})

    assert result == b"created"


def test_fetch_json_parses_json_body(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=json.dumps({"a": 1}).encode())])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch_json("https://example.com") == {"a": 1}


def test_fetch_json_returns_empty_dict_for_empty_body(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"")])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch_json("https://example.com") == {}


def test_fetch_json_returns_empty_dict_on_invalid_json(
    scripted_http_client: ScriptInstaller,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    scripted_http_client([httpx.Response(200, content=b"not json")])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch_json("https://example.com") == {}
    assert "Error decoding JSON response" in capsys.readouterr().out


def test_fetch_json_raises_http_error_when_status_code_returned(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(404, text="not found")])
    fetcher = Fetcher(_config(tmp_path))

    with pytest.raises(HttpError):
        fetcher.fetch_json("https://example.com")


def test_fetch_json_with_rate_limit_applies_limit_and_fetches(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b'{"a": 1}')])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch_json_with_rate_limit("https://example.com") == {"a": 1}


def test_fetch_with_rate_limit_applies_limit_and_fetches(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"hello")])
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch_with_rate_limit("https://example.com") == b"hello"


def test_post_with_rate_limit_applies_limit_and_posts(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"created")])
    fetcher = Fetcher(_config(tmp_path))

    result = fetcher.post_with_rate_limit(
        "https://example.com", payload={"a": 1}, headers={"X": "Y"}
    )

    assert result == b"created"


def test_apply_rate_limit_raises_key_error_for_unknown_limit_type(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([httpx.Response(200, content=b"hello")])
    fetcher = Fetcher(_config(tmp_path))

    with pytest.raises(KeyError):
        fetcher.fetch_with_rate_limit("https://example.com", "nonexistent")


def test_apply_rate_limit_pauses_after_threshold(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client(
        [
            httpx.Response(200, content=b"one"),
            httpx.Response(200, content=b"two"),
        ]
    )
    config = _config(
        tmp_path, rate_limits={"universal": RateLimit(requests=1, seconds=0)}
    )
    fetcher = Fetcher(config)

    fetcher.fetch_with_rate_limit("https://example.com")
    fetcher.fetch_with_rate_limit("https://example.com")

    assert fetcher.config.rate_limits["universal"].counter == 0


def test_request_retries_on_timeout_then_succeeds(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client(
        [httpx.ConnectTimeout("boom"), httpx.Response(200, content=b"hello")]
    )
    fetcher = Fetcher(_config(tmp_path, max_retries=3))

    assert fetcher.fetch("https://example.com") == b"hello"


def test_request_applies_rate_limit_and_retries_on_429(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client(
        [httpx.Response(429, text="slow down"), httpx.Response(200, content=b"hello")]
    )
    fetcher = Fetcher(_config(tmp_path))

    assert fetcher.fetch("https://example.com") == b"hello"


def test_request_raises_value_error_for_unknown_verb(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([])
    fetcher = Fetcher(_config(tmp_path))

    with pytest.raises(ValueError, match="Unknown HTTP verb"):
        fetcher.request("delete", "https://example.com")  # type: ignore[arg-type]


def test_request_raises_http_error_and_logs_after_exhausting_retries(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client(
        [
            httpx.ConnectTimeout("boom"),
            httpx.ReadTimeout("boom"),
            httpx.RemoteProtocolError("boom"),
        ]
    )
    error_log_path = tmp_path / "nested" / "errors.txt"
    fetcher = Fetcher(
        _config(tmp_path, max_retries=3, error_log_path=str(error_log_path))
    )

    with pytest.raises(HttpError, match="Failed to fetch"):
        fetcher.fetch("https://example.com")

    assert error_log_path.read_text() == "https://example.com\n"


def test_close_closes_underlying_client(
    scripted_http_client: ScriptInstaller, tmp_path: Path
) -> None:
    scripted_http_client([])
    fetcher = Fetcher(_config(tmp_path))

    fetcher.close()

    assert fetcher.client.closed  # type: ignore[attr-defined]


def test_create_fetcher_uses_defaults() -> None:
    fetcher = create_fetcher()

    assert fetcher.config.max_retries == 3
    assert fetcher.config.timeout == 10.0


def test_create_fetcher_applies_overrides() -> None:
    fetcher = create_fetcher(max_retries=5, timeout=2.5)

    assert fetcher.config.max_retries == 5
    assert fetcher.config.timeout == 2.5


def test_main_fetches_and_posts_successfully(
    scripted_http_client: ScriptInstaller,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripted_http_client(
        [
            httpx.Response(200, content=b"hello"),
            httpx.Response(200, content=b"created"),
        ]
    )
    monkeypatch.chdir(tmp_path)

    main()


def test_main_handles_http_error(
    scripted_http_client: ScriptInstaller,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    scripted_http_client([httpx.ConnectTimeout("boom")] * 3)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "v3.utils.fetcher.fetcher.create_fetcher",
        lambda **_kwargs: Fetcher(_config(tmp_path, max_retries=3)),
    )

    main()

    assert "Request failed" in capsys.readouterr().out
