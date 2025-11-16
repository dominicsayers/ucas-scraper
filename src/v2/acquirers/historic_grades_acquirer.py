from dataclasses import dataclass
from typing import Any
from enum import Enum
import json
from v2.utils.fetcher.fetcher import Fetcher


class QualificationType(Enum):
    """Enumeration of supported qualification types"""

    A_LEVEL = "A_level"


@dataclass
class ApiConfig:
    """Configuration for API endpoints"""

    BASE_URL = "https://services.ucas.com/historic-grades-api"
    LOGGED_IN_ENDPOINT = f"{BASE_URL}/loggedIn"
    LOGGED_OUT_ENDPOINT = f"{BASE_URL}/loggedOut"

    @classmethod
    def get_historic_grades_url(cls, course_id: str) -> str:
        return f"{cls.LOGGED_OUT_ENDPOINT}/{course_id}"


@dataclass
class ApiHeaders:
    """Default headers for API requests"""

    CONFIRMATION_RATE = {
        "Content-type": "application/json; charset=UTF-8",
    }


class HistoricGrades:
    """Handles fetching and processing of historic grade data from UCAS"""

    def __init__(self, fetcher: Fetcher = Fetcher()) -> None:
        """
        Initialize HistoricGrades instance.

        Args:
            fetcher: Fetcher instance for making HTTP requests
        """
        self.fetcher = fetcher

    def historic_grades(self, ucas_id: str) -> dict[str, Any]:
        """
        Fetch historic grades for the course.

        Returns:
            Dictionary containing historic grade data
        """
        url = ApiConfig.get_historic_grades_url(ucas_id)
        print(f"   🔹Fetching historic grades for course id {ucas_id}", end="")

        return self.fetcher.fetch_json_with_rate_limit(url)

    def confirmation_rate(
        self,
        ucas_id: str,
        predicted_grades: str,
        qualification_type: QualificationType = QualificationType.A_LEVEL,
    ) -> dict[str, Any]:
        """
        Fetch confirmation rate for specific predicted grades.

        Args:
            predicted_grades: Predicted grade string
            qualification_type: Type of qualification (default: A_LEVEL)

        Returns:
            Dictionary containing confirmation rate data
        """
        print(
            f"   🔸Fetching confirmation rate at {predicted_grades} for course id {ucas_id}",
            end="",
        )

        payload = self._build_confirmation_rate_payload(
            ucas_id, predicted_grades, qualification_type
        )

        response = self.fetcher.post_with_rate_limit(
            ApiConfig.LOGGED_IN_ENDPOINT, payload, ApiHeaders.CONFIRMATION_RATE
        )

        if not response or isinstance(response, int):
            return {"results": []}

        try:
            return dict(json.loads(response))
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON response: {e}")
            return {"results": []}

    def _build_confirmation_rate_payload(
        self, ucas_id: str, predicted_grades: str, qualification_type: QualificationType
    ) -> dict[str, Any]:
        """Build payload for confirmation rate request"""
        return {
            "courseIds": [ucas_id],
            "qualificationType": qualification_type.value,
            "grade": predicted_grades,
        }


def main() -> None:
    """Example usage of HistoricGrades class"""
    ucas_id = "508f8040-1309-e5cb-ff57-c4ff9c902ed3"
    historic_grades_api = HistoricGrades(Fetcher())

    # Fetch historic grades
    historic_data = historic_grades_api.historic_grades(ucas_id)
    print(historic_data)

    # Fetch confirmation rate for specific grades
    confirmation_data = historic_grades_api.confirmation_rate(ucas_id, "AAB")
    print(confirmation_data)


if __name__ == "__main__":
    main()
