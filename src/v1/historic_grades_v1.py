from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum
import json
from utils.fetcher.fetcher import Fetcher
from utils.course_id_parser import CourseIdParser


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

    def __init__(self, fetcher: Fetcher, course_id: Optional[str] = None) -> None:
        """
        Initialize HistoricGrades instance.

        Args:
            fetcher: Fetcher instance for making HTTP requests
            course_id: Course ID or URL (optional)
        """
        self.course_id = CourseIdParser.parse(course_id) if course_id else None
        self.fetcher = fetcher

    def historic_grades(self) -> dict[str, Any]:
        """
        Fetch historic grades for the course.

        Returns:
            Dictionary containing historic grade data
        """
        if not self.course_id:
            return {}

        url = ApiConfig.get_historic_grades_url(self.course_id)
        print(f"Fetching historic grades for course id {self.course_id}", end="")

        try:
            response = self.fetcher.fetch(url)
            return self._process_response(response)
        except Exception as e:
            print(f"\nError fetching historic grades: {e}")
            return {}

    def confirmation_rate(
        self,
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
        if not self.course_id:
            return {}

        print(
            f"Fetching confirmation rate at {predicted_grades} for course id {self.course_id}",
            end="",
        )

        payload = self._build_confirmation_rate_payload(
            predicted_grades, qualification_type
        )

        try:
            response = self.fetcher.post(
                ApiConfig.LOGGED_IN_ENDPOINT, payload, ApiHeaders.CONFIRMATION_RATE
            )
            return self._process_response(response)
        except Exception as e:
            print(f"\nError fetching confirmation rate: {e}")
            return {}

    def _build_confirmation_rate_payload(
        self, predicted_grades: str, qualification_type: QualificationType
    ) -> dict[str, Any]:
        """Build payload for confirmation rate request"""
        return {
            "courseIds": [self.course_id],
            "qualificationType": qualification_type.value,
            "grade": predicted_grades,
        }

    def _process_response(self, response: Any) -> dict[str, Any]:
        """
        Process API response and convert to dictionary.

        Args:
            response: Raw API response

        Returns:
            Processed response as dictionary
        """
        if isinstance(response, int):
            return {}

        try:
            return dict(json.loads(response))
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON response: {e}")
            return {}


def main() -> None:
    """Example usage of HistoricGrades class"""
    url = "https://digital.ucas.com/coursedisplay/courses/508f8040-1309-e5cb-ff57-c4ff9c902ed3?academicYearId=2025"
    grades = HistoricGrades(Fetcher(), url)

    # Fetch historic grades
    historic_data = grades.historic_grades()
    print(historic_data)

    # Fetch confirmation rate for specific grades
    confirmation_data = grades.confirmation_rate("AAB")
    print(confirmation_data)


if __name__ == "__main__":
    main()
