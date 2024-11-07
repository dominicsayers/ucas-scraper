import os
import time
from urllib.parse import quote
from fetcher import Fetcher
from output import Output
from parser import Parser, ParserContent
from course import Course
from historic_grades import HistoricGrades


class Search:
    COLUMN_HEADERS = [
        "provider",
        "institution-code",
        "course-code",
        "location",
        "title",
        "qualification",
        "duration",
        "start-date",
        "study-mode",
        "most-common-grade",
        "minimum-grade",
        "maximum-grade",
        "confirmation-rate",
        "entry-requirements",
        "entry-grades",
        "a-level",
        "ucas-tariff",
        "a-level-text",
        "ucas-tariff-text",
        "url",
        "provider-url",
    ]

    def __init__(self) -> None:
        self.url = os.environ.get("UCAS_URL", "https://digital.ucas.com")
        self.path = "coursedisplay/results/courses"
        self.fetcher = Fetcher()
        self.counter = 0

    def course_search(
        self,
        search_term: str,
        study_year: int = 2025,
        destination: str = "Undergraduate",
    ) -> None:
        output = Output(study_year)

        page = 0
        encoded_search_term = quote(search_term, safe="")
        encoded_destination = quote(destination, safe="")
        courses = []

        while True:
            page += 1
            print(f"Fetching courses page {page}", end="")
            response = self.__fetch_page(
                page, encoded_search_term, study_year, encoded_destination
            )

            new_courses = self.__process_page(response, output)

            if not new_courses:
                break

            courses += new_courses

        output.write_csv(search_term, courses, self.COLUMN_HEADERS)
        self.fetcher.close()

    def __fetch_page(
        self, page: int, search_term: str, study_year: int, destination: str
    ) -> bytes | int:
        return self.fetcher.fetch(
            f"{self.url}/{self.path}?searchTerm={search_term}&studyYear={study_year}&destination={destination}&pageNumber={page}"
        )

    def __process_page(
        self, response: bytes | int, output: Output
    ) -> list[dict[str, str]]:
        if isinstance(response, int):
            return []

        html = Parser(response)
        new_courses = []

        for course_html in html.select("app-courses-view app-course article"):
            item = ParserContent(course_html)
            course = {}

            course["provider"] = item.get_content_from("div.provider").replace("\\", "")
            course["location"] = item.get_content_from("div.location")
            course["title"] = item.get_content_from("header h2")
            course["qualification"] = item.get_content_from("div.qualification dd")
            course["duration"] = item.get_content_from("div.duration dd")
            course["start-date"] = item.get_content_from("div.start-date dd")
            course["study-mode"] = item.get_content_from("div.study-mode dd")
            course["entry-requirements"] = item.get_content_from("div.ucas-points dd")
            course["entry-grades"] = item.get_content_from("div.entry-grades")
            course["url"] = self.url + item.get_content_from(
                "a.link-container__link", "link"
            )

            output.write(course["provider"], course["title"], "source", item.prettify())
            output.write(course["provider"], course["title"], "search", course)

            course_data = Course(self.fetcher, course["url"])
            extra_details = course_data.process()
            course_extra = {}

            course_extra["course-code"] = extra_details["course-code"]
            course_extra["institution-code"] = extra_details["institution-code"]
            course_extra["provider-url"] = extra_details["provider-url"]
            course_extra["ucas-tariff"] = extra_details["UCAS tariff"]["level"]
            course_extra["ucas-tariff-text"] = extra_details["UCAS tariff"]["text"]
            course_extra["a-level"] = extra_details["A level"]["level"]
            course_extra["a-level-text"] = extra_details["A level"]["text"]

            output.write(course["provider"], course["title"], "course", course_extra)

            course_historic = output.read(
                course["provider"], course["title"], "historic"
            )

            if not course_historic:
                self.counter += 1

                if self.counter > 10:
                    self.counter = 0
                    time.sleep(
                        60
                    )  # To defeat the historical grades per-minute rate limiter

                grades = HistoricGrades(self.fetcher, course["url"])
                course_historic = {}

                results_list = grades.historic_grades()["results"]
                results = results_list[0] if results_list else {}
                course_historic["most-common-grade"] = results.get(
                    "mostCommonGrade", ""
                )
                course_historic["minimum-grade"] = results.get("minimumGrade", "")
                course_historic["maximum-grade"] = results.get("maximumGrade", "")

                results_list = grades.confirmation_rate()["results"]
                results = results_list[0] if results_list else {}
                course_historic["confirmation-rate"] = results.get(
                    "confirmationRate", ""
                )

                output.write(
                    course["provider"], course["title"], "historic", course_historic
                )

            new_courses.append(course | course_extra | course_historic)
            print(f"📃 {course["provider"]}: {course["title"]}")

        return new_courses


if __name__ == "__main__":
    search = Search()
    search.course_search("physics")
