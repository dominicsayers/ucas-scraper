from unittest.mock import MagicMock

import pytest

from v3.scripts import step_01_course_search


def test_main_runs_a_default_search(monkeypatch: pytest.MonkeyPatch) -> None:
    search_service = MagicMock()
    monkeypatch.setattr(step_01_course_search, "SearchService", lambda: search_service)

    step_01_course_search.main()

    search_service.search_courses.assert_called_once_with()
