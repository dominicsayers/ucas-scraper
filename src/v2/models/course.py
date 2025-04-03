from dataclasses import dataclass


@dataclass
class Course:
    VALID_GRADE_TYPES = {"UCAS tariff", "A level"}

    # Id
    ucas_id: str = ""

    # From basic details API
    course_code: str = ""
    duration: str = ""
    institution_code: str = ""
    location: str = ""
    provider_sort: str = ""
    provider_url: str = ""
    provider: str = ""
    qualification: str = ""
    study_mode: str = ""
    title: str = ""

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

    # From confirmation rate API

    # Unknown
    entry_grades: str = ""
    entry_requirements: str = ""
