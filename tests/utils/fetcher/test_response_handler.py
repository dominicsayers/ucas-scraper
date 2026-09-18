from v3.utils.fetcher.response_handler import ResponseHandler


def test_200_returns_content() -> None:
    result = ResponseHandler(200, content=b"hello", text="hello").process()

    assert result == b"hello"


def test_200_with_no_content_returns_empty_bytes() -> None:
    result = ResponseHandler(200, content=None, text=None).process()

    assert result == b""


def test_404_returns_status_code() -> None:
    result = ResponseHandler(404, content=None, text="not found").process()

    assert result == 404


def test_other_status_with_text_returns_status_code() -> None:
    long_text = "error " * 20
    result = ResponseHandler(500, content=None, text=long_text).process()

    assert result == 500


def test_other_status_without_text_returns_status_code() -> None:
    result = ResponseHandler(503, content=None, text=None).process()

    assert result == 503
