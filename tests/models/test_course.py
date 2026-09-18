from dataclasses import asdict
from typing import Any
from unittest.mock import MagicMock

from v3.models.course import Course
from v3.models.ucas_course import UCASCourse


def _mock_ucas_course(**overrides: Any) -> MagicMock:
    ucas_course = MagicMock(spec=UCASCourse)
    ucas_course.id = "ucas-id-1"
    ucas_course.course = {"applicationCode": "H101", "courseTitle": "Engineering"}
    ucas_course.provider = {
        "institutionCode": "E84",
        "providerSort": "Example, University of",
        "name": "University of Example",
    }
    ucas_course.options = {
        "location": {"name": "Main Campus"},
        "providerCourseUrl": "https://example.com/course",
        "outcomeQualification": {"caption": "BEng (Hons)"},
        "studyMode": {"caption": "Full-time"},
    }
    ucas_course.course_duration = "3 Years"
    ucas_course.entry_requirements = {
        "a_level": {"offer": "AAB", "requirements": "Maths required"},
        "ucas_tariff": {"offer": False, "requirements": ""},
    }
    for key, value in overrides.items():
        setattr(ucas_course, key, value)
    return ucas_course


def test_add_ucas_course_populates_all_fields() -> None:
    course = Course()

    course.add_ucas_course(_mock_ucas_course())

    assert course.ucas_id == "ucas-id-1"
    assert course.course_code == "H101"
    assert course.institution_code == "E84"
    assert course.location == "Main Campus"
    assert course.provider_sort == "Example, University of"
    assert course.provider_url == "https://example.com/course"
    assert course.provider == "University of Example"
    assert course.qualification == "BEng (Hons)"
    assert course.study_mode == "Full-time"
    assert course.title == "Engineering"
    assert course.duration == "3 Years"
    assert course.a_level_text == "Maths required"
    assert course.a_level == "AAB"
    assert course.ucas_tariff_text == ""
    assert course.ucas_tariff is False  # type: ignore[comparison-overlap]


def test_add_historic_grades_populates_grade_fields() -> None:
    course = Course()

    course.add_historic_grades(
        {
            "mostCommonGrade": "AAB",
            "minimumGrade": "BBB",
            "maximumGrade": "A*A*A",
        }
    )

    assert course.most_common_grade == "AAB"
    assert course.minimum_grade == "BBB"
    assert course.maximum_grade == "A*A*A"


def test_course_is_a_plain_dataclass() -> None:
    course = Course()

    assert asdict(course)["ucas_id"] == ""
    assert Course.VALID_GRADE_TYPES == {"UCAS tariff", "A level"}
