import json
from typing import Any
from functools import cached_property


class UCASCourse:
    ENTRY_REQUIREMENT_TYPES = {"A level": "a_level", "UCAS Tariff": "ucas_tariff"}

    TEMPLATE_ENTRY_REQUIREMENTS = {
        "a_level": {"offer": False, "requirements": ""},
        "ucas_tariff": {"offer": False, "requirements": ""},
    }

    def __init__(self, id: str, details: dict[str, Any]) -> None:
        self.id = id
        self.details = details

    @cached_property
    def course(self) -> dict[str, Any]:
        course = self.details["course"]

        if isinstance(course, dict):
            return course

        return {}

    @cached_property
    def provider(self) -> dict[str, Any]:
        provider = self.course["provider"]

        if isinstance(provider, dict):
            return provider

        return {}

    @cached_property
    def options(self) -> dict[str, Any]:
        options_data = self.course["options"]
        options = options_data[0] if len(options_data) > 0 else options_data

        if isinstance(options, dict):
            return options

        return {}

    @cached_property
    def course_duration(self) -> str:
        try:
            duration = self.options["duration"]
            return (
                f"{int(duration['quantity'])} {duration['durationType']['caption']}"
                if duration
                else "Unknown"
            )
        except KeyError as e:
            print(self.options)
            raise e
        except TypeError as e:
            print(json.dumps(self.options, indent=4))
            print(
                f"{self.id} - {self.provider['name']}, {self.course['courseTitle']} ({self.options['outcomeQualification']['caption']})"
            )
            print(duration)
            raise e

    @cached_property
    def entry_requirements(self) -> dict[str, Any]:
        qualifications = self.options["academicEntryRequirements"]["qualifications"]
        entry_requirements = self.TEMPLATE_ENTRY_REQUIREMENTS.copy()

        for qualification in qualifications:
            valid_type = self.ENTRY_REQUIREMENT_TYPES.get(
                qualification["qualificationName"], None
            )

            if not valid_type:
                continue

            entry_requirements[valid_type] = qualification["summary"]

        return entry_requirements
