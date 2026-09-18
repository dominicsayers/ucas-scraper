from pathlib import Path
from unittest.mock import MagicMock

import pytest

from v3.scripts import step_02_get_course_details
from v3.utils.file_handler import FileHandler


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))
    monkeypatch.setenv("COURSE", "Physics")


def test_main_processes_every_cached_course_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = FileHandler("data")
    (handler.base_path / "course-ids-Physics.txt").write_text("id-1\nid-2\n")
    acquirer = MagicMock()
    monkeypatch.setattr(step_02_get_course_details, "CourseAcquirer", lambda: acquirer)

    step_02_get_course_details.main()

    assert acquirer.process.call_args_list == [
        (("id-1",), {}),
        (("id-2",), {}),
    ]


def test_main_does_nothing_when_id_list_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    acquirer = MagicMock()
    monkeypatch.setattr(step_02_get_course_details, "CourseAcquirer", lambda: acquirer)

    step_02_get_course_details.main()

    acquirer.process.assert_not_called()
