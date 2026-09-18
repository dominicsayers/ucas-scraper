from unittest.mock import MagicMock

import pytest

from v3.scripts import acquire_course_by_id


def test_main_processes_the_example_course_id(monkeypatch: pytest.MonkeyPatch) -> None:
    acquirer = MagicMock()
    monkeypatch.setattr(acquire_course_by_id, "CourseAcquirer", lambda: acquirer)

    acquire_course_by_id.main()

    acquirer.process.assert_called_once_with("508f8040-1309-e5cb-ff57-c4ff9c902ed3")
