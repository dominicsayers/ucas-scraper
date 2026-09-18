import csv
from pathlib import Path
from typing import Any

import pytest

from v3.builders.course_builder import CourseBuilder
from v3.utils.file_handler import FileHandler


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))


def _course_details(ucas_id: str, title: str) -> dict[str, Any]:
    return {
        "course": {
            "id": ucas_id,
            "applicationCode": "H101",
            "courseTitle": title,
            "provider": {
                "name": "University of Example",
                "institutionCode": "E84",
                "providerSort": "Example, University of",
            },
            "options": [
                {
                    "providerCourseUrl": "https://example.com/course",
                    "outcomeQualification": {"caption": "BEng (Hons)"},
                    "studyMode": {"caption": "Full-time"},
                    "location": {"name": "Main Campus"},
                    "duration": {
                        "quantity": 3.0,
                        "durationType": {"caption": "Years"},
                    },
                    "academicEntryRequirements": {
                        "qualifications": [
                            {
                                "qualificationName": "A level",
                                "summary": {
                                    "offer": "AAB",
                                    "requirements": "Maths required",
                                },
                            }
                        ]
                    },
                }
            ],
        }
    }


def _seed_course(
    file_handler: FileHandler,
    location: list[str],
    *,
    with_details: bool = True,
    with_historic: bool = True,
    with_confirmation_rates: bool = True,
    ucas_id: str = "ucas-1",
    title: str = "Engineering",
) -> None:
    if with_details:
        file_handler.write(location, "course", _course_details(ucas_id, title))
    if with_historic:
        file_handler.write(
            location,
            "historic",
            {
                "results": [
                    {
                        "mostCommonGrade": "AAB",
                        "minimumGrade": "BBB",
                        "maximumGrade": "A*A*A",
                    }
                ]
            },
        )
    if with_confirmation_rates:
        file_handler.write(
            location, "confirmation_rates", {"AAB": "19 in 20", "ucas_id": ucas_id}
        )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def test_from_file_cache_writes_courses_and_confirmation_rates() -> None:
    builder = CourseBuilder()
    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    _seed_course(builder.file_handler, location)

    builder.from_file_cache()

    courses_csv = builder.file_handler.base_path / "courses.csv"
    rows = _read_csv_rows(courses_csv)
    assert len(rows) == 1
    assert rows[0]["title"] == "Engineering"
    assert rows[0]["most_common_grade"] == "AAB"

    confirmation_csv = builder.file_handler.base_path / "confirmation-rates.csv"
    confirmation_rows = _read_csv_rows(confirmation_csv)
    assert confirmation_rows[0]["ucas_id"] == "ucas-1"


def test_from_file_cache_handles_no_cached_courses() -> None:
    builder = CourseBuilder()

    builder.from_file_cache()

    assert not (builder.file_handler.base_path / "courses.csv").exists()
    assert not (builder.file_handler.base_path / "confirmation-rates.csv").exists()


def test_from_file_cache_skips_courses_without_details() -> None:
    builder = CourseBuilder()
    location = [
        "providers",
        "Example, University of",
        "Untitled",
        "BEng (Hons)",
        "2025",
    ]
    _seed_course(builder.file_handler, location, with_details=False)

    builder.from_file_cache()

    rows = _read_csv_rows(builder.file_handler.base_path / "courses.csv")
    assert rows[0]["title"] == ""


def test_from_file_cache_skips_historic_grades_when_no_results() -> None:
    builder = CourseBuilder()
    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    builder.file_handler.write(
        location, "course", _course_details("ucas-1", "Engineering")
    )
    builder.file_handler.write(location, "historic", {"results": []})

    builder.from_file_cache()

    rows = _read_csv_rows(builder.file_handler.base_path / "courses.csv")
    assert rows[0]["most_common_grade"] == ""


def test_from_file_cache_excludes_courses_matching_filter() -> None:
    builder = CourseBuilder()
    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    _seed_course(builder.file_handler, location)
    builder.course_filter.exclude = lambda course: True  # type: ignore[method-assign]

    builder.from_file_cache()

    assert not (builder.file_handler.base_path / "courses.csv").exists()


def test_list_courses_prints_cached_locations(
    capsys: pytest.CaptureFixture[str],
) -> None:
    builder = CourseBuilder()
    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    _seed_course(builder.file_handler, location)

    builder.list_courses()

    assert "Example, University of" in capsys.readouterr().out
