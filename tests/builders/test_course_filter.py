from pathlib import Path

import pytest

from v3.builders.course_filter import CourseFilter
from v3.models.course import Course
from v3.utils.config import Config


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))


def test_uses_default_criteria_when_config_omitted() -> None:
    course_filter = CourseFilter()

    assert course_filter.filter == CourseFilter.DEFAULT_CRITERIA


def test_uses_default_criteria_when_no_file_present() -> None:
    course_filter = CourseFilter(Config(course_filter_criteria_file="missing"))

    assert course_filter.filter == CourseFilter.DEFAULT_CRITERIA


def test_uses_default_criteria_when_criteria_file_disabled() -> None:
    course_filter = CourseFilter(Config(course_filter_criteria_file=""))

    assert course_filter.filter == CourseFilter.DEFAULT_CRITERIA


def test_loads_criteria_from_file_when_present(tmp_path: Path) -> None:
    criteria = {"criteria": [{"include": {"study_mode": ["Full-time"]}}]}
    config = Config(course_filter_criteria_file="my_criteria")
    course_filter = CourseFilter(config)
    course_filter.file_handler.write([], "my_criteria", criteria)

    reloaded = CourseFilter(config)

    assert reloaded.filter == criteria


def _course(**overrides: str) -> Course:
    course = Course()
    for key, value in overrides.items():
        setattr(course, key, value)
    return course


def test_exclude_returns_false_when_no_criteria_configured() -> None:
    course_filter = CourseFilter()

    assert course_filter.exclude(_course(title="Engineering")) is False


def test_exclude_returns_true_when_include_criterion_not_matched(
    tmp_path: Path,
) -> None:
    config = Config(course_filter_criteria_file="criteria")
    course_filter = CourseFilter(config)
    course_filter.filter = {"criteria": [{"include": {"study_mode": ["Full-time"]}}]}

    assert course_filter.exclude(_course(study_mode="Part-time")) is True


def test_exclude_returns_false_when_include_criterion_matched() -> None:
    course_filter = CourseFilter()
    course_filter.filter = {"criteria": [{"include": {"study_mode": ["Full-time"]}}]}

    assert course_filter.exclude(_course(study_mode="Full-time")) is False


def test_exclude_returns_true_when_exclude_criterion_matched() -> None:
    course_filter = CourseFilter()
    course_filter.filter = {"criteria": [{"exclude": {"minimum_grade": ["A*A*A"]}}]}

    assert course_filter.exclude(_course(minimum_grade="A*A*A")) is True


def test_exclude_returns_false_when_exclude_criterion_not_matched() -> None:
    course_filter = CourseFilter()
    course_filter.filter = {"criteria": [{"exclude": {"minimum_grade": ["A*A*A"]}}]}

    assert course_filter.exclude(_course(minimum_grade="ABB")) is False


def test_exclude_ignores_criteria_without_include_or_exclude() -> None:
    course_filter = CourseFilter()
    course_filter.filter = {"criteria": [{}]}

    assert course_filter.exclude(_course(title="Engineering")) is False
