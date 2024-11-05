import os
import re
import time
import httpx
import csv
from typing import Any
from urllib.parse import quote
from bs4 import BeautifulSoup
from bs4.css import CSS


class Search:
    MAX_RETRIES = 3
    COLUMN_HEADERS = [
        "provider",
        "location",
        "title",
        "qualification",
        "duration",
        "start-date",
        "study-mode",
        "entry-requirements",
        "entry-grades",
        "url",
    ]

    def __init__(self) -> None:
        self.path = "coursedisplay/results/courses"
        self.url = os.environ.get("UCAS_URL", "https://digital.ucas.com")
        self.client = self.__get_client()

    def course_search(
        self,
        search_term: str,
        study_year: int = 2025,
        destination: str = "Undergraduate",
    ) -> None:
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

            new_courses = self.__process_page(response)

            if not new_courses:
                break

            courses += new_courses

        with open("tmp/courses.csv", "w", newline="") as output_file:
            dict_writer = csv.DictWriter(output_file, self.COLUMN_HEADERS)
            dict_writer.writeheader()
            dict_writer.writerows(courses)

        self.client.close()

    def __fetch_page(
        self, page: int, search_term: str, study_year: int, destination: str
    ) -> bytes | None:
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.get(
                    f"{self.url}/{self.path}?searchTerm={search_term}&studyYear={study_year}&destination={destination}&pageNumber={page}",
                    follow_redirects=True,
                )

                result = None

                match response.status_code:
                    case 200:
                        result = response.content
                        print(" ✅")
                    case 404:
                        print(" - doesn't exist")
                    case _:
                        content = re.sub("\\s+", " ", response.text)[:79]
                        print(f" ❌ {response.status_code}: {content}")

                return result
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError):
                print(f"  Retrying page {page}")
                time.sleep(1)
                self.client = self.__get_client()
                continue
            else:
                break
        else:
            with open("tmp/errors.txt", "a") as f:
                f.write(f"{self.url}/{self.path}/{page}\n")

            print(f"Error in {self.url}/{self.path}/{page}")

            raise httpx.HTTPError("Unhandled HTTP error")

    def __process_page(self, result: bytes | None) -> list[dict[str, str]]:
        html = BeautifulSoup(str(result), "html.parser")

        if not html.css:
            return []

        new_courses = []

        for course_html in html.css.select("app-courses-view app-course article"):
            course = {}
            css = course_html.css

            course["provider"] = self.__get_text_from(css, "div.provider")
            course["location"] = self.__get_text_from(css, "div.location")
            course["title"] = self.__get_text_from(css, "header h2")
            course["qualification"] = self.__get_text_from(css, "div.qualification dd")
            course["duration"] = self.__get_text_from(css, "div.duration dd")
            course["start-date"] = self.__get_text_from(css, "div.start-date dd")
            course["study-mode"] = self.__get_text_from(css, "div.study-mode dd")
            course["entry-requirements"] = self.__get_text_from(
                css, "div.ucas-points dd"
            )
            course["entry-grades"] = self.__get_text_from(css, "div.entry-grades")
            course["url"] = self.url + self.__get_link_from(
                css, "a.link-container__link"
            )

            new_courses.append(course)

            print(f"📃 {course["provider"]}: {course["title"]}")

            folder = f"tmp/courses/{course["provider"]}"
            os.makedirs(folder, exist_ok=True)

            with open(f"{folder}/{course["title"].replace("/","¦")}.html", "w") as f:
                f.write(course_html.prettify())

        return new_courses

    def __get_text_from(self, html: CSS | Any | None, selector: str) -> str:
        if type(html) is not CSS:
            return ""

        try:
            return str(html.select(selector)[0].string)  # type: ignore
        except IndexError:
            return ""

    def __get_link_from(self, html: CSS | Any | None, selector: str) -> str:
        if type(html) is not CSS:
            return ""

        try:
            return str(html.select(selector)[0].attrs["href"])  # type: ignore
        except IndexError:
            return ""

    def __get_client(self) -> httpx.Client:
        return httpx.Client(http2=True, timeout=10.0)


if __name__ == "__main__":
    search = Search()
    search.course_search("physics")
