from unittest.mock import MagicMock

import pytest

from v3.scripts import step_03_build_course_data


def test_main_builds_course_data_from_file_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = MagicMock()
    monkeypatch.setattr(step_03_build_course_data, "CourseBuilder", lambda: builder)

    step_03_build_course_data.main()

    builder.from_file_cache.assert_called_once_with()
