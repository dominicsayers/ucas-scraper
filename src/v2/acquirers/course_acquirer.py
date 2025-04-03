from functools import cached_property
import json
from typing import Any
from utils.config import Config
from utils.fetcher.fetcher import Fetcher
from utils.output import Output
from utils.course_id_parser import CourseIdParser
from v2.models.course import Course
from .historic_grades_acquirer import HistoricGrades


class CourseAcquirer:
    ENTRY_REQUIREMENT_TYPES = {"A level": "a_level", "UCAS Tariff": "ucas_tariff"}

    TEMPLATE_ENTRY_REQUIREMENTS = {
        "a_level": {"offer": False, "requirements": ""},
        "ucas_tariff": {"offer": False, "requirements": ""},
    }

    def __init__(self, config: Config = Config(), fetcher: Fetcher = Fetcher()) -> None:
        self.config = config
        self.fetcher = fetcher
        self.output = Output()
        self.historic_grades_api = HistoricGrades(self.fetcher)

    def process(self, id_or_url: str) -> None:
        self.ucas_id = CourseIdParser.parse(id_or_url)

        # Fetch course details
        self.__fetch_basic_details()
        self.__fetch_historic_data()
        self.__fetch_confirmation_rates()

    def __fetch_basic_details(self) -> None:
        print(f"Fetching course details for {self.ucas_id}", end="")
        self.details = self.fetcher.fetch_json(self.__url)
        self.course = Course()

        # Basic details
        self.course.course_code = self.details["course"]["applicationCode"]
        self.course.institution_code = self.provider["institutionCode"]
        self.course.location = self.options["location"]["name"]
        self.course.provider_sort = self.provider["providerSort"]
        self.course.provider_url = self.options["providerCourseUrl"]
        self.course.provider = self.provider["name"]
        self.course.qualification = self.options["outcomeQualification"]["caption"]
        self.course.study_mode = self.options["studyMode"]["caption"]
        self.course.title = self.details["course"]["courseTitle"]
        self.course.ucas_id = self.ucas_id
        self.course.duration = self.course_duration

        print(
            f" - {self.course.provider}, {self.course.title} ({self.course.qualification})"
        )

        # Entry requirements
        self.course.a_level_text = self.entry_requirements["a_level"]["requirements"]
        self.course.a_level = self.entry_requirements["a_level"]["offer"]
        self.course.ucas_tariff_text = self.entry_requirements["ucas_tariff"][
            "requirements"
        ]
        self.course.ucas_tariff = self.entry_requirements["ucas_tariff"]["offer"]

        # Cache basic details
        self.output.write(self.__file_location, "course", self.details)

    def __fetch_historic_data(self) -> None:
        """Fetch historic grade data"""
        historic_data = self.output.read(self.__file_location, "historic")

        if not historic_data:
            historic_data = self.historic_grades_api.historic_grades(self.ucas_id)
            self.output.write(self.__file_location, "historic", historic_data)

        self.course.most_common_grade = historic_data.get("mostCommonGrade", "")
        self.course.minimum_grade = historic_data.get("minimumGrade", "")
        self.course.maximum_grade = historic_data.get("maximumGrade", "")

    def __fetch_confirmation_rates(self) -> dict[str, str]:
        """Fetch confirmation rates"""
        confirmation_rates = (
            self.output.read(self.__file_location, "confirmation_rates") or {}
        )

        for predicted_grade in self.predicted_grades_list:
            if predicted_grade in confirmation_rates:
                continue

            results = self.historic_grades_api.confirmation_rate(
                self.ucas_id, predicted_grade
            )

            confirmation_rate = (
                results["results"][0]["confirmationRate"]
                if len(results["results"]) > 0
                else ""
            )

            confirmation_rates[predicted_grade] = confirmation_rate

        confirmation_rates["ucas_id"] = self.ucas_id
        self.output.write(
            self.__file_location, "confirmation_rates", confirmation_rates
        )
        return confirmation_rates

    @cached_property
    def predicted_grades_list(self) -> list[str]:
        """Get list of predicted grades"""
        return self.config.predicted_grades.split(",")

    @cached_property
    def entry_requirements(self) -> dict[str, Any]:
        qualifications = self.options["academicEntryRequirements"]["qualifications"]
        entry_requirements = self.TEMPLATE_ENTRY_REQUIREMENTS.copy()

        for qualification in qualifications:
            valid_type = self.ENTRY_REQUIREMENT_TYPES.get(
                qualification["qualificationName"], None
            )

            if not valid_type:
                continue

            entry_requirements[valid_type] = qualification["summary"]

        return entry_requirements

    @cached_property
    def provider(self) -> dict[str, Any]:
        provider = self.details["course"]["provider"]

        if isinstance(provider, dict):
            return provider

        return {}

    @cached_property
    def options(self) -> dict[str, Any]:
        options_data = self.details["course"]["options"]
        options = options_data[0] if len(options_data) > 0 else options_data

        if isinstance(options, dict):
            return options

        return {}

    @cached_property
    def course_duration(self) -> str:
        try:
            duration = self.options["duration"]
            return (
                f"{int(duration['quantity'])} {duration['durationType']['caption']}"
                if duration
                else "Unknown"
            )
        except KeyError as e:
            print(self.options)
            raise e
        except TypeError as e:
            print(json.dumps(self.options, indent=4))
            print(
                f"{self.ucas_id} - {self.course.provider}, {self.course.title} ({self.course.qualification})"
            )
            print(duration)
            raise e

    @cached_property
    def __file_location(self) -> list[str]:
        """Create file location path elements"""
        return [
            "providers",
            self.course.provider_sort,
            self.course.title,
            self.course.qualification,
            str(self.config.academic_year),
        ]

    @cached_property
    def __url(self) -> str:
        return (
            "https://services.ucas.com/search/api/v3/courses"
            + f"?courseDetailsRequest.coursePrimaryId={self.ucas_id}"
            + f"&courseDetailsRequest.academicYearId={self.config.academic_year}"
            + f"&courseDetailsRequest.courseType={self.config.destination}"
        )


if __name__ == "__main__":
    url = "https://digital.ucas.com/coursedisplay/courses/508f8040-1309-e5cb-ff57-c4ff9c902ed3?academicYearId=2025"

    course = CourseAcquirer()
    course.process(url)
