from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict, Tuple, Union
from datetime import datetime
import os
import time
from functools import cached_property
from urllib.parse import quote

from v1.utils.fetcher.fetcher import Fetcher
from v1.utils.output import Output
from .parser import Parser, ParserContent
from v1.course_v1 import Course
from v1.historic_grades_v1 import HistoricGrades
from v1.utils.course_id_parser import CourseIdParser


@dataclass
class RateLimit:
    requests: int
    seconds: int
    counter: int = 0


@dataclass
class SearchConfig:
    url: str = field(
        default_factory=lambda: os.environ.get("UCAS_URL", "https://digital.ucas.com")
    )
    path: str = "coursedisplay/results/courses"
    predicted_grades: str = field(
        default_factory=lambda: os.environ.get("PREDICTED_GRADES", "EEE")
    )
    study_year: int = field(
        default_factory=lambda: int(os.environ.get("STUDY_YEAR", datetime.now().year))
    )
    destination: str = field(
        default_factory=lambda: os.environ.get("DESTINATION", "Undergraduate")
    )
    rate_limits: Dict[str, RateLimit] = field(
        default_factory=lambda: {"universal": RateLimit(requests=20, seconds=60)}
    )


@dataclass
class CourseData:
    basic_info: Dict[str, str]
    extra_details: Dict[str, str]
    historic_data: Dict[str, str]
    confirmation_rates: Dict[str, str]


class SearchService:
    """Handles course search and data collection from UCAS"""

    def __init__(self, config: Optional[SearchConfig] = None) -> None:
        self.config = config or SearchConfig()
        self.fetcher = Fetcher()
        self.output = Output("data")

    def search_courses(self, search_term: str) -> None:
        """
        Execute course search and collect data.

        Args:
            search_term: Term to search for
        """
        try:
            courses, confirmation_rates = self._collect_course_data(search_term)
            self._write_output(search_term, courses, confirmation_rates)
        finally:
            self.fetcher.close()

    def _collect_course_data(
        self, search_term: str
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Collect course data page by page"""
        page = 0
        courses = []
        confirmation_rates = []
        encoded_term = quote(search_term, safe="")
        encoded_destination = quote(self.config.destination, safe="")

        while True:
            page += 1
            print(f"Fetching courses page {page}", end="")

            response = self._fetch_page(page, encoded_term, encoded_destination)
            new_courses, new_rates = self._process_page(response)

            if not new_courses:
                break

            courses.extend(new_courses)
            confirmation_rates.extend(new_rates)

        return courses, confirmation_rates

    def _fetch_page(
        self, page: int, search_term: str, destination: str
    ) -> Union[bytes, int, None]:
        """Fetch a single page of search results"""
        url = (
            f"{self.config.url}/{self.config.path}"
            f"?searchTerm={search_term}"
            f"&studyYear={self.config.study_year}"
            f"&destination={destination}"
            f"&pageNumber={page}"
        )
        return self.fetcher.fetch(url)

    def _process_page(
        self, response: bytes | int | None
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Process a single page of search results"""
        if isinstance(response, int):
            return [], []

        html = Parser(response)
        new_courses = []
        new_confirmation_rates = []

        for course_html in html.select("app-courses-view app-course article"):
            try:
                course_data = self._process_course(course_html)
                merged_course_data = self._merge_course_data(course_data)
                new_courses.append(merged_course_data)
                new_confirmation_rates.append(course_data.confirmation_rates)
                print(
                    f"📃 {course_data.basic_info['provider']}: {course_data.basic_info['title']} ({course_data.basic_info['ucas_id']})"
                )
            except Exception as e:
                print(f"\nError processing course: {e}")

        return new_courses, new_confirmation_rates

    def _process_course(self, course_html: Any) -> CourseData:
        """Process individual course data"""
        basic_info = self._extract_basic_info(course_html)
        location = self._get_location_info(basic_info)

        course_data = Course(self.fetcher, basic_info["url"])
        extra_details = course_data.process()

        historic_data = self._get_historic_data(basic_info["url"], location)
        confirmation_rates = self._get_confirmation_rates(basic_info["url"], location)

        return CourseData(basic_info, extra_details, historic_data, confirmation_rates)

    def _extract_basic_info(self, course_html: Any) -> Dict[str, str]:
        """Extract basic course information from HTML"""
        item = ParserContent(course_html)
        url = self.config.url + item.get_content_from("a.link-container__link", "link")
        ucas_id = CourseIdParser.parse(url) if url else None

        return {
            "provider": item.get_content_from("div.provider").replace("\\", ""),
            "location": item.get_content_from("div.location"),
            "title": item.get_content_from("header h2"),
            "qualification": item.get_content_from("div.qualification dd"),
            "duration": item.get_content_from("div.duration dd"),
            "start-date": item.get_content_from("div.start-date dd"),
            "study-mode": item.get_content_from("div.study-mode dd"),
            "entry-requirements": item.get_content_from("div.ucas-points dd"),
            "entry-grades": item.get_content_from("div.entry-grades"),
            "url": url,
            "ucas_id": ucas_id or "",
        }

    def _get_location_info(self, course_info: Dict[str, str]) -> List[str]:
        """Create location information list"""
        return [
            "providers",
            course_info["provider"],
            course_info["title"],
            course_info["qualification"],
            str(self.config.study_year),
        ]

    def _get_historic_data(self, url: str, location: List[str]) -> Dict[str, str]:
        """Fetch historic grade data"""
        historic_data = self.output.read(location, "historic")
        if historic_data:
            return historic_data

        self._apply_rate_limit("universal")
        grades = HistoricGrades(self.fetcher, url)
        results = grades.historic_grades()

        historic_data = {
            "most-common-grade": results.get("mostCommonGrade", ""),
            "minimum-grade": results.get("minimumGrade", ""),
            "maximum-grade": results.get("maximumGrade", ""),
        }

        self.output.write(location, "historic", historic_data)
        return historic_data

    def _get_confirmation_rates(self, url: str, location: List[str]) -> Dict[str, str]:
        """Fetch confirmation rates"""
        confirmation_rates = self.output.read(location, "confirmation-rates") or {}
        grades = HistoricGrades(self.fetcher, url)

        for predicted_grade in self.predicted_grades_list:
            if predicted_grade in confirmation_rates:
                continue

            self._apply_rate_limit("universal")
            results = grades.confirmation_rate(predicted_grade)
            confirmation_rates[predicted_grade] = results.get("confirmationRate", "")

        confirmation_rates["ucas_id"] = grades.course_id
        self.output.write(location, "confirmation-rates", confirmation_rates)
        return confirmation_rates

    def _merge_course_data(self, course_data: CourseData) -> Dict[str, str]:
        """Merge all course data into single dictionary"""
        return {
            **course_data.basic_info,
            **course_data.extra_details,
            **course_data.historic_data,
        }

    def _apply_rate_limit(self, limit_type: str) -> None:
        """Apply rate limiting"""
        if limit_type not in self.config.rate_limits:
            raise KeyError(f"Rate limit type {limit_type} not found")

        rate_limit = self.config.rate_limits[limit_type]
        rate_limit.counter += 1

        if rate_limit.counter > rate_limit.requests:
            rate_limit.counter = 0
            time.sleep(rate_limit.seconds)

    def _write_output(
        self,
        search_term: str,
        courses: List[Dict[str, str]],
        confirmation_rates: List[Dict[str, str]],
    ) -> None:
        """Write output data to files"""
        self.output.write_csv(
            f"courses-{search_term}", courses, self.course_column_headers
        )
        self.output.write_csv(
            f"confirmation-rates-{search_term}",
            confirmation_rates,
            self.confirmation_rate_column_headers,
        )

    @cached_property
    def predicted_grades_list(self) -> List[str]:
        """Get list of predicted grades"""
        return self.config.predicted_grades.split(",")

    @cached_property
    def course_column_headers(self) -> List[str]:
        """Get course column headers"""
        return [
            "provider",
            "institution_code",
            "course_code",
            "location",
            "title",
            "qualification",
            "duration",
            "start-date",
            "study-mode",
            "most-common-grade",
            "minimum-grade",
            "maximum-grade",
            "entry-requirements",
            "entry-grades",
            "a_level",
            "ucas_tariff",
            "a_level_text",
            "ucas_tariff_text",
            "ucas_id",
            "url",
            "provider_url",
        ]

    @cached_property
    def confirmation_rate_column_headers(self) -> List[str]:
        """Get confirmation rate column headers"""
        return ["ucas_id"] + self.predicted_grades_list


def main() -> None:
    """Main entry point"""
    search_service = SearchService()
    search_service.search_courses(os.environ.get("COURSE", "physics"))


if __name__ == "__main__":
    main()
