from dataclasses import asdict
from v2.utils.config import Config
from v2.utils.output import Output
from v2.models.course import Course
from v2.models.ucas_course import UCASCourse


class CourseBuilder:
    def __init__(self, config: Config = Config()) -> None:
        self.config = config
        self.output = Output()

    def list_courses(self) -> None:
        for course_location in self.output.cached_courses(["providers"]):
            print(course_location)

    def from_file_cache(self) -> None:
        courses = []
        confirmation_rates = []

        for course_location in self.output.cached_courses(["providers"]):
            # Course details
            details = self.output.read(course_location, "course")
            historic_data = self.output.read(course_location, "historic")

            if details:
                ucas_id = details["course"]["id"]
                ucas_course = UCASCourse(ucas_id, details)
                course = Course()

                course.add_ucas_course(ucas_course)

            if (
                historic_data
                and "results" in historic_data
                and len(historic_data["results"]) > 0
            ):
                course.add_historic_grades(historic_data["results"][0])

            courses.append(asdict(course))

            # Confirmation rates
            confirmation_rates.append(
                self.output.read(course_location, "confirmation_rates") or {}
            )

        # Write output data to files
        confirmation_rates_headers = (
            list(confirmation_rates[0].keys())
            if len(confirmation_rates) > 0 and isinstance(confirmation_rates[0], dict)
            else []
        )
        confirmation_rates_headers.sort(reverse=True)

        self.output.write_csv("courses", courses, list(courses[0].keys()))

        if len(confirmation_rates) > 0:
            self.output.write_csv(
                "confirmation-rates", confirmation_rates, confirmation_rates_headers
            )
