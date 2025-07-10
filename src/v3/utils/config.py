import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Config:
    """Overall configuration"""

    course: str = field(
        default_factory=lambda: os.environ.get("COURSE", "Computer Science")
    )
    destination: str = field(
        default_factory=lambda: os.environ.get("DESTINATION", "Undergraduate")
    )
    predicted_grades: str = field(
        default_factory=lambda: os.environ.get("PREDICTED_GRADES", "ABC,DEF")
    )
    url: str = field(
        default_factory=lambda: os.environ.get("UCAS_URL", "https://digital.ucas.com")
    )
    study_year: int = field(
        default_factory=lambda: int(
            os.environ.get("STUDY_YEAR", datetime.now().year + 1)
        )
    )
    path: str = "coursedisplay/results/courses"
    course_filter_criteria_file: str = "course_filter_criteria"
