import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from v3.acquirers.course import CourseAcquirer
from v3.utils.config import Config
from v3.utils.fetcher.fetcher import Fetcher


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))


def _course_details(ucas_id: str) -> dict[str, Any]:
    return {
        "course": {
            "id": ucas_id,
            "applicationCode": "H101",
            "courseTitle": "Engineering",
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


def _make_acquirer(**config_kwargs: object) -> tuple[CourseAcquirer, MagicMock]:
    fetcher = MagicMock(spec=Fetcher)
    defaults: dict[str, object] = {
        "destination": "Undergraduate",
        "study_year": 2025,
        "predicted_grades": "AAB,BBB",
    }
    defaults.update(config_kwargs)
    config = Config(**defaults)  # type: ignore[arg-type]
    return CourseAcquirer(config, fetcher), fetcher


def test_process_writes_course_historic_and_confirmation_rate_files() -> None:
    acquirer, fetcher = _make_acquirer()
    fetcher.fetch_json_with_rate_limit.side_effect = [
        _course_details("ucas-1"),
        {
            "results": [
                {
                    "mostCommonGrade": "AAB",
                    "minimumGrade": "BBB",
                    "maximumGrade": "A*A*A",
                }
            ]
        },
    ]
    fetcher.post_with_rate_limit.return_value = json.dumps(
        {"results": [{"confirmationRate": "19 in 20"}]}
    ).encode()

    acquirer.process("ucas-1")

    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    course_data = acquirer.output.read(location, "course")
    assert course_data is not None
    assert course_data["course"]["id"] == "ucas-1"

    historic_data = acquirer.output.read(location, "historic")
    assert historic_data is not None
    assert historic_data["results"][0]["mostCommonGrade"] == "AAB"

    confirmation_rates = acquirer.output.read(location, "confirmation_rates")
    assert confirmation_rates is not None
    assert confirmation_rates["AAB"] == "19 in 20"
    assert confirmation_rates["BBB"] == "19 in 20"
    assert confirmation_rates["ucas_id"] == "ucas-1"


def test_process_reuses_cached_historic_data() -> None:
    acquirer, fetcher = _make_acquirer()
    fetcher.fetch_json_with_rate_limit.return_value = _course_details("ucas-1")
    fetcher.post_with_rate_limit.return_value = json.dumps({"results": []}).encode()

    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    acquirer.output.write(
        location, "historic", {"results": [{"mostCommonGrade": "cached"}]}
    )

    acquirer.process("ucas-1")

    # historic_grades API should never be called because the cache was used.
    fetcher.fetch_json_with_rate_limit.assert_called_once()
    historic_data = acquirer.output.read(location, "historic")
    assert historic_data is not None
    assert historic_data["results"][0]["mostCommonGrade"] == "cached"


def test_process_skips_predicted_grades_already_confirmed() -> None:
    acquirer, fetcher = _make_acquirer(predicted_grades="AAB")
    fetcher.fetch_json_with_rate_limit.side_effect = [
        _course_details("ucas-1"),
        {"results": []},
    ]

    location = [
        "providers",
        "Example, University of",
        "Engineering",
        "BEng (Hons)",
        "2025",
    ]
    acquirer.output.write(
        location, "confirmation_rates", {"AAB": "already-known", "ucas_id": "ucas-1"}
    )

    acquirer.process("ucas-1")

    fetcher.post_with_rate_limit.assert_not_called()
    confirmation_rates = acquirer.output.read(location, "confirmation_rates")
    assert confirmation_rates is not None
    assert confirmation_rates["AAB"] == "already-known"


def test_constructs_default_config_and_fetcher_when_omitted() -> None:
    acquirer = CourseAcquirer()

    assert isinstance(acquirer.config, Config)
    assert isinstance(acquirer.fetcher, Fetcher)
