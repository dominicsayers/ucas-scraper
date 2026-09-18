from datetime import UTC, datetime

import pytest

from v3.utils.config import Config


def test_defaults_when_no_environment_variables_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "COURSE",
        "DESTINATION",
        "PREDICTED_GRADES",
        "UCAS_URL",
        "STUDY_YEAR",
    ):
        monkeypatch.delenv(name, raising=False)

    config = Config()

    assert config.course == "Computer Science"
    assert config.destination == "Undergraduate"
    assert config.predicted_grades == "ABC,DEF"
    assert config.url == "https://digital.ucas.com"
    assert config.study_year == datetime.now(UTC).year + 1
    assert config.path == "coursedisplay/results/courses"
    assert config.course_filter_criteria_file == "course_filter_criteria"


def test_values_are_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COURSE", "Physics")
    monkeypatch.setenv("DESTINATION", "Postgraduate")
    monkeypatch.setenv("PREDICTED_GRADES", "AAA,AAB")
    monkeypatch.setenv("UCAS_URL", "https://example.com")
    monkeypatch.setenv("STUDY_YEAR", "2030")

    config = Config()

    assert config.course == "Physics"
    assert config.destination == "Postgraduate"
    assert config.predicted_grades == "AAA,AAB"
    assert config.url == "https://example.com"
    assert config.study_year == 2030
