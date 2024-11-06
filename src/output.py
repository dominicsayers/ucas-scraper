import os
import csv
import json


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
        content: str | dict[str, str],
    ) -> None:
        folder = os.path.join(
            self.base_directory,
            "courses",
            provider.replace("\\", ""),
            "summary",
        )

        name = f"{title.replace("/", " & ")}.html"

        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, name), "w", newline="") as output_file:
            if isinstance(content, str):
                output_file.write(content)
            elif isinstance(content, dict):
                json.dump(content, output_file, indent=4)
