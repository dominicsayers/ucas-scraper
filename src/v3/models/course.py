from dataclasses import dataclass
from typing import Any

from v3.models.ucas_course import UCASCourse


@dataclass
class Course:
    VALID_GRADE_TYPES = {"UCAS tariff", "A level"}

    # Id
    ucas_id: str = ""

    # From basic details API
    provider: str = ""
    title: str = ""
    qualification: str = ""
    study_mode: str = ""
    duration: str = ""

    # Entry requirements
    # Also from basic details API
    a_level_text: str = ""
    a_level: str = "No data"
    ucas_tariff_text: str = ""
    ucas_tariff: str = "Not accepted"

    # From historic grades API
    most_common_grade: str = ""
    minimum_grade: str = ""
    maximum_grade: str = ""

    # Boring details from basic details API
    location: str = ""
    institution_code: str = ""
    course_code: str = ""
    provider_sort: str = ""
    provider_url: str = ""

    def add_ucas_course(self, ucas_course: UCASCourse) -> None:
        # Basic details
        self.ucas_id = ucas_course.id
        self.course_code = ucas_course.course["applicationCode"]
        self.institution_code = ucas_course.provider["institutionCode"]
        self.location = ucas_course.options["location"]["name"]
        self.provider_sort = ucas_course.provider["providerSort"]
        self.provider_url = ucas_course.options["providerCourseUrl"]
        self.provider = ucas_course.provider["name"]
        self.qualification = ucas_course.options["outcomeQualification"]["caption"]
        self.study_mode = ucas_course.options["studyMode"]["caption"]
        self.title = ucas_course.course["courseTitle"]
        self.duration = ucas_course.course_duration

        # Entry requirements
        a_level = ucas_course.entry_requirements["a_level"]
        ucas_tariff = ucas_course.entry_requirements["ucas_tariff"]

        self.a_level_text = a_level["requirements"]
        self.a_level = a_level["offer"]
        self.ucas_tariff_text = ucas_tariff["requirements"]
        self.ucas_tariff = ucas_tariff["offer"]

    def add_historic_grades(self, historic_grades: dict[str, Any]) -> None:
        self.most_common_grade = historic_grades["mostCommonGrade"]
        self.minimum_grade = historic_grades["minimumGrade"]
        self.maximum_grade = historic_grades["maximumGrade"]
