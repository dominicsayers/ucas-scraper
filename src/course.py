from typing import Any
from bs4.element import Tag
from fetcher import Fetcher
from parser import Parser, ParserContent


class Course:
    DEFAULT_DETAILS = {
        "course-code": "",
        "institution-code": "",
        "provider-url": "",
        "UCAS tariff": {"level": "Not accepted", "text": ""},
        "A level": {"level": "No data", "text": ""},
    }

    def __init__(self, fetcher: Fetcher, url: str) -> None:
        self.fetcher = fetcher
        self.url = url

    def process(self) -> dict[str, Any]:
        print(f"Fetching course from {self.url}", end="")
        response = self.fetcher.fetch(self.url)

        html = Parser(response)

        if html.empty:
            return {}

        content = html.select("section#entry-requirements-section li")
        summary = ParserContent(html.soup)
        details = self.DEFAULT_DETAILS

        details["course-code"] = summary.get_content_from("dd#application-code")
        details["institution-code"] = summary.get_content_from("dd#institution-code")
        details["provider-url"] = summary.get_content_from(
            "a#provider-course-url", "link"
        )

        for fragment in content:
            fragment_data = self.__get_data_from(fragment)

            if fragment_data is None:
                continue

            details[fragment_data["type"]] = {
                "level": fragment_data["level"],
                "text": fragment_data["text"],
            }

        return details

    def __get_data_from(self, fragment: Tag | None) -> dict[str, str] | None:
        item = ParserContent(fragment)
        type_and_level = item.get_content_from("h2")
        text = item.get_content_from("div.accordion__inner-wrapper")

        if type_and_level is None:
            return None

        type, *level = type_and_level.split(" - ")

        if type not in ["UCAS tariff", "A level"]:
            return None

        if not level:
            level = [""]

        return {"type": type, "level": level[0], "text": text}


if __name__ == "__main__":
    url = "https://digital.ucas.com/coursedisplay/courses/b68ba80a-b8c5-5f4c-09c8-72b7d5ef519c?academicYearId=2025"

    course = Course(Fetcher(), url)
    course.process()
