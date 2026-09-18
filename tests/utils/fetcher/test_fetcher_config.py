import logging

from v3.utils.fetcher.fetcher_config import FetcherConfig, RateLimit


def test_rate_limit_defaults() -> None:
    rate_limit = RateLimit(requests=10, seconds=60)

    assert rate_limit.requests == 10
    assert rate_limit.seconds == 60
    assert rate_limit.counter == 0


def test_fetcher_config_defaults() -> None:
    config = FetcherConfig()

    assert config.max_retries == 3
    assert config.timeout == 10.0
    assert config.error_log_path == "tmp/errors.txt"
    assert config.http2_enabled is True
    assert config.log_level == logging.WARNING
    assert "universal" in config.rate_limits
    assert "course" in config.rate_limits
    assert config.rate_limits["universal"].requests == 10
    assert config.rate_limits["course"].requests == 49


def test_rate_limits_are_independent_between_instances() -> None:
    first = FetcherConfig()
    second = FetcherConfig()

    first.rate_limits["universal"].counter = 5

    assert second.rate_limits["universal"].counter == 0
