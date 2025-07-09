from functools import cached_property
from v2.utils.config import Config
from v2.utils.fetcher.fetcher import Fetcher
from v2.utils.output import Output
from v2.utils.course_id_parser import CourseIdParser
from v2.models.course import Course
from v2.models.ucas_course import UCASCourse
from .historic_grades_acquirer import HistoricGrades


class CourseAcquirer:
    def __init__(self, config: Config = Config(), fetcher: Fetcher = Fetcher()) -> None:
        self.config = config
        self.fetcher = fetcher
        self.output = Output()
        self.historic_grades_api = HistoricGrades(self.fetcher)

    def process(self, id_or_url: str) -> None:
        self.ucas_id = CourseIdParser.parse(id_or_url)

        # Fetch course details
        self.__fetch_basic_details()
        self.__fetch_historic_data()
        self.__fetch_confirmation_rates()

    def __fetch_basic_details(self) -> None:
        print(f"Fetching course details for {self.ucas_id}", end="")
        self.details = self.fetcher.fetch_json_with_rate_limit(self.__url, "course")
        self.ucas_course = UCASCourse(self.ucas_id, self.details)
        self.course = Course()
        self.course.add_ucas_course(self.ucas_course)

        print(
            f" 🎓 {self.course.provider}, {self.course.title} ({self.course.qualification})"
        )

        # Cache basic details
        self.output.write(self.__file_location, "course", self.details)

    def __fetch_historic_data(self) -> None:
        """Fetch historic grade data"""
        historic_data = self.output.read(self.__file_location, "historic")

        if not historic_data:
            historic_data = self.historic_grades_api.historic_grades(self.ucas_id)

        self.output.write(self.__file_location, "historic", historic_data)

    def __fetch_confirmation_rates(self) -> dict[str, str]:
        """Fetch confirmation rates"""
        confirmation_rates = (
            self.output.read(self.__file_location, "confirmation_rates") or {}
        )

        for predicted_grade in self.predicted_grades_list:
            if predicted_grade in confirmation_rates:
                continue

            results = self.historic_grades_api.confirmation_rate(
                self.ucas_id, predicted_grade
            )

            confirmation_rate = (
                results["results"][0]["confirmationRate"]
                if len(results["results"]) > 0
                else ""
            )

            confirmation_rates[predicted_grade] = confirmation_rate

        confirmation_rates["ucas_id"] = self.ucas_id
        self.output.write(
            self.__file_location, "confirmation_rates", confirmation_rates
        )
        return confirmation_rates

    @cached_property
    def predicted_grades_list(self) -> list[str]:
        """Get list of predicted grades"""
        return self.config.predicted_grades.split(",")

    @cached_property
    def __file_location(self) -> list[str]:
        """Create file location path elements"""
        return [
            "providers",
            self.course.provider_sort,
            self.course.title,
            self.course.qualification,
            str(self.config.academic_year),
        ]

    @cached_property
    def __url(self) -> str:
        return (
            "https://services.ucas.com/search/api/v3/courses"
            + f"?courseDetailsRequest.coursePrimaryId={self.ucas_id}"
            + f"&courseDetailsRequest.academicYearId={self.config.academic_year}"
            + f"&courseDetailsRequest.courseType={self.config.destination}"
        )


if __name__ == "__main__":
    url = "https://digital.ucas.com/coursedisplay/courses/508f8040-1309-e5cb-ff57-c4ff9c902ed3?academicYearId=2025"

    course = CourseAcquirer()
    course.process(url)
