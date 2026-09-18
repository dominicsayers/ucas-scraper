import json
from pathlib import Path
from typing import Any

import pytest

from v3.models.ucas_course import UCASCourse

EXAMPLE_COURSE_PATH = Path(__file__).parents[2] / "examples" / "course.json"


def _minimal_details(**overrides: Any) -> dict[str, Any]:
    option: dict[str, Any] = {
        "applicationCode": "H101",
        "providerCourseUrl": "https://example.com/course",
        "outcomeQualification": {"caption": "BEng (Hons)"},
        "studyMode": {"caption": "Full-time"},
        "location": {"name": "Main Campus"},
        "duration": {"quantity": 3.0, "durationType": {"caption": "Years"}},
        "academicEntryRequirements": {
            "qualifications": [
                {
                    "qualificationName": "A level",
                    "summary": {"offer": "AAB", "requirements": "Maths required"},
                },
                {
                    "qualificationName": "UCAS Tariff",
                    "summary": {"offer": None, "requirements": None},
                },
                {
                    "qualificationName": "Scottish Higher",
                    "summary": {"offer": "AAAB", "requirements": None},
                },
            ]
        },
    }
    option.update(overrides.pop("option_overrides", {}))

    details: dict[str, Any] = {
        "course": {
            "applicationCode": "H101",
            "courseTitle": "Engineering",
            "provider": {
                "name": "University of Example",
                "institutionCode": "E84",
                "providerSort": "Example, University of",
            },
            "options": [option],
        }
    }
    details.update(overrides)
    return details


def test_course_returns_dict_when_present() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    assert ucas_course.course["applicationCode"] == "H101"


def test_course_returns_empty_dict_when_not_a_dict() -> None:
    ucas_course = UCASCourse("id1", {"course": "not-a-dict"})

    assert ucas_course.course == {}


def test_provider_returns_dict_when_present() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    assert ucas_course.provider["name"] == "University of Example"


def test_provider_returns_empty_dict_when_not_a_dict() -> None:
    details = _minimal_details()
    details["course"]["provider"] = None
    ucas_course = UCASCourse("id1", details)

    assert ucas_course.provider == {}


def test_options_returns_first_option_when_list_has_items() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    assert ucas_course.options["applicationCode"] == "H101"


def test_options_returns_options_data_when_empty_list() -> None:
    details = _minimal_details()
    details["course"]["options"] = []
    ucas_course = UCASCourse("id1", details)

    assert ucas_course.options == {}


def test_options_returns_empty_dict_when_not_a_dict() -> None:
    details = _minimal_details()
    details["course"]["options"] = ["not-a-dict"]
    ucas_course = UCASCourse("id1", details)

    assert ucas_course.options == {}


def test_course_duration_formats_quantity_and_caption() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    assert ucas_course.course_duration == "3 Years"


def test_course_duration_returns_unknown_when_no_duration() -> None:
    details = _minimal_details(option_overrides={"duration": None})
    ucas_course = UCASCourse("id1", details)

    assert ucas_course.course_duration == "Unknown"


def test_course_duration_reraises_key_error(capsys: pytest.CaptureFixture[str]) -> None:
    details = _minimal_details(option_overrides={"duration": {"quantity": 3.0}})
    ucas_course = UCASCourse("id1", details)

    with pytest.raises(KeyError):
        _ = ucas_course.course_duration

    assert "applicationCode" in capsys.readouterr().out


def test_course_duration_reraises_type_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    details = _minimal_details(
        option_overrides={
            "duration": {"quantity": None, "durationType": {"caption": "Years"}}
        }
    )
    ucas_course = UCASCourse("id1", details)

    with pytest.raises(TypeError):
        _ = ucas_course.course_duration

    captured = capsys.readouterr()
    assert "Engineering" in captured.out


def test_entry_requirements_maps_known_qualification_types() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    entry_requirements = ucas_course.entry_requirements

    assert entry_requirements["a_level"] == {
        "offer": "AAB",
        "requirements": "Maths required",
    }
    assert entry_requirements["ucas_tariff"] == {"offer": None, "requirements": None}


def test_entry_requirements_ignores_unrecognised_qualification_types() -> None:
    ucas_course = UCASCourse("id1", _minimal_details())

    entry_requirements = ucas_course.entry_requirements

    assert set(entry_requirements.keys()) == {"a_level", "ucas_tariff"}


def test_entry_requirements_defaults_when_qualification_missing() -> None:
    details = _minimal_details(
        option_overrides={"academicEntryRequirements": {"qualifications": []}}
    )
    ucas_course = UCASCourse("id1", details)

    entry_requirements = ucas_course.entry_requirements

    assert entry_requirements["a_level"] == {"offer": False, "requirements": ""}
    assert entry_requirements["ucas_tariff"] == {"offer": False, "requirements": ""}


def test_parses_real_world_example() -> None:
    details = json.loads(EXAMPLE_COURSE_PATH.read_text())
    ucas_course = UCASCourse(details["course"]["id"], details)

    assert ucas_course.provider["name"] == "University of Exeter"
    assert ucas_course.course_duration == "3 Years"
    assert ucas_course.entry_requirements["a_level"]["offer"] == "AAB - ABB"
