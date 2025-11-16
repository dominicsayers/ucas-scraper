from typing import Any
from v3.utils.config import Config
from v3.utils.file_handler import FileHandler
from v3.models.course import Course

"""
{
  "criteria": [
    {
      "include": {
        "study_mode": [
          "Full-time",
          "Full-time with time abroad",
          "Full-time with year in industry"
        ]
      }
    },
    {
      "exclude": {
        "minimum_grade": ["A*A*A*", "A*A*A", "A*AA"],
        "qualification": [
          "Certificate - Cert",
          "Certificate of Higher Education - CertHE",
          "Diploma of Higher Education - DipHE",
          "Foundation Degree - FD",
          "Foundation Degree in Engineering - FdEng",
          "Foundation Degree in Science - FdSc",
          "Higher National Certificate - HNC",
          "Higher National Diploma - HND"
        ]
      }
    }
  ]
}
"""


class CourseFilter:
    DEFAULT_CRITERIA: dict[str, list[dict[str, dict[str, list[str]]]]] = {
        "criteria": []
    }

    def __init__(self, config: Config = Config()) -> None:
        self.config = config
        self.file_handler = FileHandler("data")

        criteria_file = self.config.course_filter_criteria_file
        if criteria_file:
            self.filter = (
                self.file_handler.read([], criteria_file, False)
                or self.DEFAULT_CRITERIA
            )
            print(f"Loaded course filter criteria from {criteria_file}")
            print(f"Filter criteria: {self.filter}")
        else:
            self.filter = self.DEFAULT_CRITERIA

    def exclude(self, course: Course) -> bool:
        print(f"     🔬 Checking course: {course.title} for exclusion criteria")

        for criterion in self.filter.get("criteria", []):
            if self._should_exclude_by_include(course, criterion.get("include")):
                return True
            if self._should_exclude_by_exclude(course, criterion.get("exclude")):
                return True
        return False

    def _should_exclude_by_include(
        self, course: Course, include_criterion: dict[str, list[str]] | Any | None
    ) -> bool:
        if not include_criterion:
            return False
        for field, allowed_values in include_criterion.items():
            print(
                f"     🔬 Checking field: {field} (include only if {getattr(course, field, None)} in {allowed_values})",
                end="",
            )
            if getattr(course, field, None) not in allowed_values:
                print(" ❌")
                return True
            else:
                print(" ✅")
        return False

    def _should_exclude_by_exclude(
        self, course: Course, exclude_criterion: dict[str, list[str]] | Any | None
    ) -> bool:
        if not exclude_criterion:
            return False
        for field, excluded_values in exclude_criterion.items():
            print(
                f"     🔬 Checking field: {field} (exclude if {getattr(course, field, None)} in {excluded_values})",
                end="",
            )
            if getattr(course, field, None) in excluded_values:
                print(" ❌")
                return True
            else:
                print(" ✅")
        return False
