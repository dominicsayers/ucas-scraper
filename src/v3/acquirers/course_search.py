from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union
from datetime import datetime
import os
from urllib.parse import quote

from v3.utils.fetcher.fetcher import Fetcher
from v3.utils.file_handler import FileHandler
from v3.utils.html_parser import HTMLParser


@dataclass
class SearchConfig:
    url: str = field(
        default_factory=lambda: os.environ.get("UCAS_URL", "https://digital.ucas.com")
    )
    path: str = "coursedisplay/results/courses"
    study_year: int = field(
        default_factory=lambda: int(os.environ.get("STUDY_YEAR", datetime.now().year))
    )
    course: str = field(
        default_factory=lambda: os.environ.get("COURSE", "Computer Science")
    )
    destination: str = field(
        default_factory=lambda: os.environ.get("DESTINATION", "Undergraduate")
    )


@dataclass
class CourseData:
    basic_info: Dict[str, str]


class SearchService:
    """Handles course search and data collection from UCAS"""

    def __init__(self, config: Optional[SearchConfig] = None) -> None:
        self.config = config or SearchConfig()
        self.fetcher = Fetcher()
        self.file_handler = FileHandler("data")

    def search_courses(self, search_term: Optional[str] = None) -> None:
        """
        Execute course search and collect data.

        Args:
            search_term: Term to search for
        """
        effective_search_term = search_term or self.config.course
        print(f"Searching for courses with term: {effective_search_term}")

        try:
            courses = self.__collect_course_ids(effective_search_term)
            self.__write_output(effective_search_term, courses)
        finally:
            self.fetcher.close()

    def __collect_course_ids(self, search_term: str) -> List[str]:
        """Collect course ids page by page"""
        page = 0
        course_ids = []
        encoded_term = quote(search_term, safe="")
        encoded_destination = quote(self.config.destination, safe="")

        while True:
            page += 1
            print(f"Fetching course search page {page}", end="")

            response = self.__fetch_page(page, encoded_term, encoded_destination)
            new_course_ids = self.__process_page(response)

            if not new_course_ids:
                break

            course_ids.extend(new_course_ids)

        return course_ids

    def __fetch_page(
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

    def __process_page(self, response: bytes | int | None) -> List[str]:
        """Process a single page of search results"""
        if isinstance(response, int):
            return []

        html = HTMLParser(response)
        new_course_ids = []

        for course_html in html.select("app-courses-view app-course article"):
            try:
                new_course_ids.append(f"{course_html.get('id')}\n")
            except Exception as e:
                print(f"\nError processing course: {e}")

        return new_course_ids

    def __write_output(
        self,
        search_term: str,
        course_ids: List[str],
    ) -> None:
        """Write output data to files"""
        # No subdirectory specified for output location
        output_location: list[str] = []
        self.file_handler.write(
            output_location, f"course-ids-{search_term}", course_ids
        )


def main() -> None:
    """Main entry point"""
    search_service = SearchService()
    search_service.search_courses(os.environ.get("COURSE", "Computer Science"))


if __name__ == "__main__":
    main()
