import os
import csv
import json
from typing import Any


class Output:
    def __init__(self, top_level: str | int) -> None:
        self.output_directory = os.environ.get("OUTPUT", "tmp")
        self.top_level = str(top_level)
        self.base_directory = os.path.join(self.output_directory, self.top_level)

        os.makedirs(self.base_directory, exist_ok=True)

    def write_csv(
        self, name: str, content: list[dict[str, str]], column_headers: list[str]
    ) -> None:
        with open(
            os.path.join(self.base_directory, f"{name}.csv"), "w", newline=""
        ) as output_file:
            dict_writer = csv.DictWriter(output_file, column_headers)
            dict_writer.writeheader()
            dict_writer.writerows(content)

    def write(
        self,
        provider: str,
        title: str,
        document: str,
        content: str | dict[str, str],
    ) -> None:
        folder = self.__folder_from(provider, title)
        os.makedirs(folder, exist_ok=True)

        if isinstance(content, str):
            name = f"{document}.html"

            with open(os.path.join(folder, name), "w", newline="") as output_file:
                output_file.write(content)
        elif isinstance(content, dict):
            name = f"{document}.json"

            with open(os.path.join(folder, name), "w", newline="") as output_file:
                json.dump(content, output_file, indent=4)

    def read(self, provider: str, title: str, document: str) -> dict[str, Any] | None:
        folder = self.__folder_from(provider, title)
        name = f"{document}.json"

        try:
            with open(os.path.join(folder, name), "r", newline="") as input_file:
                print(
                    f"Loading local copy of historical data for {title} at {provider}",
                    end="",
                )
                data = dict(json.loads(input_file.read()))
                print(" ✅")
                return data
        except FileNotFoundError:
            return None

    def __folder_from(self, provider: str, title: str) -> str:
        return os.path.join(
            self.base_directory,
            "courses",
            provider.replace("\\", ""),
            title.replace("/", " & "),
        )
