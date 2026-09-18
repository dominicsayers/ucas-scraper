import json
from unittest.mock import MagicMock

import pytest

from v3.acquirers.historic_grades import HistoricGrades, QualificationType, main
from v3.utils.fetcher.fetcher import Fetcher


def test_historic_grades_fetches_via_rate_limited_json() -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.fetch_json_with_rate_limit.return_value = {"results": []}
    api = HistoricGrades(fetcher)

    result = api.historic_grades("ucas-1")

    assert result == {"results": []}
    fetcher.fetch_json_with_rate_limit.assert_called_once_with(
        "https://services.ucas.com/historic-grades-api/loggedOut/ucas-1"
    )


def test_historic_grades_constructs_default_fetcher_when_none_given() -> None:
    api = HistoricGrades()

    assert isinstance(api.fetcher, Fetcher)


def test_confirmation_rate_posts_payload_and_parses_response() -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.post_with_rate_limit.return_value = json.dumps(
        {"results": [{"confirmationRate": "19 in 20"}]}
    ).encode()
    api = HistoricGrades(fetcher)

    result = api.confirmation_rate("ucas-1", "AAB")

    assert result == {"results": [{"confirmationRate": "19 in 20"}]}
    args, _kwargs = fetcher.post_with_rate_limit.call_args
    assert args[0] == "https://services.ucas.com/historic-grades-api/loggedIn"
    assert args[1] == {
        "courseIds": ["ucas-1"],
        "qualificationType": "A_level",
        "grade": "AAB",
    }
    assert args[2] == {"Content-type": "application/json; charset=UTF-8"}


def test_confirmation_rate_accepts_explicit_qualification_type() -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.post_with_rate_limit.return_value = json.dumps({"results": []}).encode()
    api = HistoricGrades(fetcher)

    api.confirmation_rate("ucas-1", "AAB", QualificationType.A_LEVEL)

    args, _kwargs = fetcher.post_with_rate_limit.call_args
    assert args[1]["qualificationType"] == "A_level"


def test_confirmation_rate_returns_empty_results_when_response_falsy() -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.post_with_rate_limit.return_value = None
    api = HistoricGrades(fetcher)

    assert api.confirmation_rate("ucas-1", "AAB") == {"results": []}


def test_confirmation_rate_returns_empty_results_when_response_is_status_code() -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.post_with_rate_limit.return_value = 404
    api = HistoricGrades(fetcher)

    assert api.confirmation_rate("ucas-1", "AAB") == {"results": []}


def test_confirmation_rate_returns_empty_results_on_invalid_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.post_with_rate_limit.return_value = b"not json"
    api = HistoricGrades(fetcher)

    assert api.confirmation_rate("ucas-1", "AAB") == {"results": []}
    assert "Error decoding JSON response" in capsys.readouterr().out


def test_main_prints_historic_and_confirmation_data(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fetcher = MagicMock(spec=Fetcher)
    fetcher.fetch_json_with_rate_limit.return_value = {"mostCommonGrade": "AAB"}
    fetcher.post_with_rate_limit.return_value = json.dumps({"results": []}).encode()
    monkeypatch.setattr("v3.acquirers.historic_grades.Fetcher", lambda: fetcher)

    main()

    captured = capsys.readouterr()
    assert "mostCommonGrade" in captured.out
    assert "results" in captured.out
