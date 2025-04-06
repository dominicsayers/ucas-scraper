import os
from dataclasses import dataclass


@dataclass
class Config:
    """Overall configuration"""

    academic_year: str = os.environ.get("STUDY_YEAR", "2026")
    search_course: str = os.environ.get("COURSE", "Engineering")
    destination: str = os.environ.get("DESTINATION", "Undergraduate")
    predicted_grades: str = os.environ.get("PREDICTED_GRADES", "ABC,DEF")
