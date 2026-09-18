import pytest

from v3.utils.fetcher.http_error import HttpError


def test_is_an_exception() -> None:
    with pytest.raises(HttpError, match="boom"):
        raise HttpError("boom")
