from pathlib import Path
from unittest.mock import MagicMock

import pytest

from v3.acquirers.course_search import SearchService, main
from v3.utils.config import Config
from v3.utils.fetcher.fetcher import Fetcher
from v3.utils.html_parser import HTMLParser

PAGE_HTML = b"""
<app-courses-view>
    <app-course><article id="course-1"></article></app-course>
    <app-course><article id="course-2"></article></app-course>
</app-courses-view>
"""

EMPTY_PAGE_HTML = b"<app-courses-view></app-courses-view>"


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))


def _make_service(
    monkeypatch: pytest.MonkeyPatch, **config_kwargs: object
) -> tuple[SearchService, MagicMock]:
    fetcher = MagicMock(spec=Fetcher)
    monkeypatch.setattr("v3.acquirers.course_search.Fetcher", lambda: fetcher)
    service = SearchService(Config(**config_kwargs))  # type: ignore[arg-type]
    return service, fetcher


def test_search_courses_collects_ids_across_pages_and_closes_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, fetcher = _make_service(monkeypatch)
    fetcher.fetch.side_effect = [PAGE_HTML, EMPTY_PAGE_HTML]

    service.search_courses("physics")

    assert fetcher.fetch.call_count == 2
    fetcher.close.assert_called_once()

    output = service.file_handler.base_path / "course-ids-physics.txt"
    assert output.read_text() == "course-1\ncourse-2\n"


def test_search_courses_defaults_search_term_to_config_course(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, fetcher = _make_service(monkeypatch, course="Chemistry")
    fetcher.fetch.side_effect = [EMPTY_PAGE_HTML]

    service.search_courses()

    output = service.file_handler.base_path / "course-ids-Chemistry.txt"
    assert output.exists()


def test_search_courses_closes_fetcher_even_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, fetcher = _make_service(monkeypatch)
    fetcher.fetch.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        service.search_courses("physics")

    fetcher.close.assert_called_once()


def test_process_page_returns_no_ids_when_response_is_status_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, fetcher = _make_service(monkeypatch)
    fetcher.fetch.side_effect = [404]

    service.search_courses("physics")

    output = service.file_handler.base_path / "course-ids-physics.txt"
    assert output.read_text() == ""


def test_process_page_logs_and_skips_elements_missing_get(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service, fetcher = _make_service(monkeypatch)
    fetcher.fetch.side_effect = [PAGE_HTML, EMPTY_PAGE_HTML]
    monkeypatch.setattr(HTMLParser, "select", lambda self, selector: ["not-a-tag"])

    service.search_courses("physics")

    assert "Error processing course" in capsys.readouterr().out


def test_main_uses_course_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.fetch.side_effect = [EMPTY_PAGE_HTML]
    monkeypatch.setattr("v3.acquirers.course_search.Fetcher", lambda: fetcher)
    monkeypatch.setenv("COURSE", "Physics")

    main()

    fetcher.fetch.assert_called_once()
    assert "searchTerm=Physics" in fetcher.fetch.call_args[0][0]
