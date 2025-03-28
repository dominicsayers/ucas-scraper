from typing import Any, Optional
from bs4.element import Tag
from dataclasses import asdict, dataclass
from fetcher import Fetcher
from parser import Parser, ParserContent


@dataclass
class GradeRequirement:
    level: str
    text: str


@dataclass
class CourseDetails:
    VALID_GRADE_TYPES = {"UCAS tariff", "A level"}

    course_code: str = ""
    institution_code: str = ""
    provider_url: str = ""
    ucas_tariff: GradeRequirement = GradeRequirement("Not accepted", "")
    a_level: GradeRequirement = GradeRequirement("No data", "")


class Course:
    def __init__(self, fetcher: Fetcher, url: str) -> None:
        self.fetcher = fetcher
        self.url = url
        self.details = CourseDetails()

    def process(self) -> dict[str, Any]:
        print(f"Fetching course from {self.url}", end="")

        try:
            response = self._fetch_and_parse()
            if not response:
                return asdict(self.details)

            self._extract_basic_details(response)
            self._extract_requirements(response)

            return asdict(self.details)
        except Exception as e:
            raise e
            print(f"Error processing course: {str(e)}")
            return asdict(self.details)

    def _fetch_and_parse(self) -> Optional[Parser]:
        response = self.fetcher.fetch(self.url)
        if isinstance(response, int):
            return None

        html = Parser(response)
        return None if html.empty else html

    def _extract_basic_details(self, html: Parser) -> None:
        summary = ParserContent(html.soup)
        self.details.course_code = summary.get_content_from("dd#application-code") or ""
        self.details.institution_code = (
            summary.get_content_from("dd#institution-code") or ""
        )
        self.details.provider_url = (
            summary.get_content_from("a#provider-course-url", "link") or ""
        )

    def _extract_requirements(self, html: Parser) -> None:
        content = html.select("section#entry-requirements-section li")

        for fragment in content:
            requirement = self._parse_requirement(fragment)
            if requirement:
                self._update_requirement(requirement)

    def _parse_requirement(self, fragment: Tag | str) -> Optional[dict[str, str]]:
        if isinstance(fragment, str):
            return None

        item = ParserContent(fragment)
        type_and_level = item.get_content_from("h2")

        if not type_and_level:
            return None

        grade_type, *level = type_and_level.split(" - ")
        if grade_type not in self.details.VALID_GRADE_TYPES:
            return None

        return {
            "type": grade_type,
            "level": level[0] if level else "",
            "text": item.get_content_from("div.accordion__inner-wrapper") or "",
        }

    def _update_requirement(self, requirement: dict[str, str]) -> None:
        grade_req = GradeRequirement(requirement["level"], requirement["text"])

        if requirement["type"] == list(self.details.VALID_GRADE_TYPES)[0]:
            self.details.ucas_tariff = grade_req
        elif requirement["type"] == list(self.details.VALID_GRADE_TYPES)[1]:
            self.details.a_level = grade_req


if __name__ == "__main__":
    url = "https://digital.ucas.com/coursedisplay/courses/b68ba80a-b8c5-5f4c-09c8-72b7d5ef519c?academicYearId=2025"

    course = Course(Fetcher(), url)
    course.process()
