import json
import os
from typing import Any
from fetcher import Fetcher


class HistoricGrades:
    CONFIRMATION_RATE_URL = "https://services.ucas.com/historic-grades-api/loggedIn"
    CONFIRMATION_RATE_HEADERS = {
        "Content-type": "application/json; charset=UTF-8",
    }

    def __init__(self, fetcher: Fetcher, course_id: str) -> None:
        self.course_id = self.parse_course_id(course_id)
        self.fetcher = fetcher
        self.predicted_grades = os.environ.get("PREDICTED_GRADES", "ABB")

    def historic_grades(self) -> dict[str, Any]:
        url = (
            f"https://services.ucas.com/historic-grades-api/loggedOut/{self.course_id}"
        )
        print(f"Fetching historic grades for course id {self.course_id}", end="")
        response = self.fetcher.fetch(url)

        if isinstance(response, int):
            return {}

        grade_data = dict(json.loads(response))
        return grade_data

    def confirmation_rate(self) -> dict[str, str | list[dict[str, str]]]:
        print(
            f"Fetching confirmation rate at {self.predicted_grades} for course id {self.course_id}",
            end="",
        )

        payload = {
            "courseIds": [self.course_id],
            "qualificationType": "A_level",
            "grade": self.predicted_grades,
        }

        response = self.fetcher.post(
            self.CONFIRMATION_RATE_URL, payload, self.CONFIRMATION_RATE_HEADERS
        )

        if isinstance(response, int):
            return {}

        grade_data = dict(json.loads(response))
        return grade_data

    def parse_course_id(self, unparsed_id: str) -> str:
        # We might get passed a course URL, in which case we need to extract the course
        # id from it, otherwise just send back what we received. If it's a URL it will
        # be in the form:
        #
        #    https://digital.ucas.com/coursedisplay/courses/b68ba80a-b8c5-5f4c-09c8-72b7d5ef519c?academicYearId=2025
        if unparsed_id[0:4].lower() == "http":
            return unparsed_id.split("/")[-1].split("?")[0]
        else:
            return unparsed_id


if __name__ == "__main__":
    url = "https://digital.ucas.com/coursedisplay/courses/e2b8d5b9-9b09-f90e-d7a3-8a7c9a607f6e?academicYearId=2025"
    grades = HistoricGrades(Fetcher(), url)

    print(grades.historic_grades())
    print(grades.confirmation_rate())
