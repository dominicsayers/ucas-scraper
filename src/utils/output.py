from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union, TypeVar, Generic, Optional
import os
import csv
import json
from abc import ABC, abstractmethod

T = TypeVar("T")


@dataclass
class OutputConfig:
    """Configuration for output operations"""

    base_directory: str = "tmp"

    def __post_init__(self) -> None:
        self.base_directory = os.environ.get("OUTPUT", self.base_directory)


class OutputWriter(ABC, Generic[T]):
    """Abstract base class for different output writers"""

    @abstractmethod
    def write(self, path: Path, content: T) -> None:
        pass


class JsonWriter(OutputWriter[dict[str, Any]]):
    """Handles JSON file writing"""

    def write(self, path: Path, content: dict[str, Any]) -> None:
        with path.open("w", newline="") as file:
            json.dump(content, file, indent=4)


class HtmlWriter(OutputWriter[str]):
    """Handles HTML file writing"""

    def write(self, path: Path, content: str) -> None:
        with path.open("w", newline="") as file:
            file.write(content)


class CsvWriter(OutputWriter[list[dict[str, str]]]):
    """Handles CSV file writing"""

    def write(
        self, path: Path, content: list[dict[str, str]], headers: list[str] = []
    ) -> None:
        with path.open("w", newline="") as file:
            writer = csv.DictWriter(file, headers)
            writer.writeheader()
            writer.writerows(content)


class Output:
    """Manages file output operations with improved error handling and type safety"""

    def __init__(self, top_level: Union[str, int] = "data") -> None:
        self.config = OutputConfig()
        self.top_level = str(top_level)
        self.base_path = Path(self.config.base_directory) / self.top_level
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize writers
        self.json_writer = JsonWriter()
        self.html_writer = HtmlWriter()
        self.csv_writer = CsvWriter()

    def write_csv(
        self, name: str, content: list[dict[str, str]], column_headers: list[str]
    ) -> None:
        """Write data to CSV file with error handling"""
        output_path = self.base_path / f"{name}.csv"
        error_path = self.base_path / f"{name}.err"

        try:
            self.csv_writer.write(output_path, content, column_headers)
        except ValueError as e:
            print(f"Error writing CSV file: {e}")
            with error_path.open("w", newline="") as file:
                file.write(str(content))

    def write(
        self,
        location: list[str],
        document: str,
        content: Union[str, dict[str, str]],
    ) -> None:
        """Write content to either HTML or JSON file"""
        folder_path = self._create_folder_path(location)

        try:
            if isinstance(content, str):
                output_path = folder_path / f"{document}.html"
                self.html_writer.write(output_path, content)
            elif isinstance(content, dict):
                output_path = folder_path / f"{document}.json"
                self.json_writer.write(output_path, content)
        except IOError as e:
            print(f"Error writing file {output_path}: {e}")

    def read(self, location: list[str], document: str) -> Optional[dict[str, Any]]:
        """Read JSON data from file with improved error handling"""
        folder_path = self._create_folder_path(location)
        file_path = folder_path / f"{document}.json"

        try:
            with file_path.open("r", newline="") as file:
                print(
                    f"   🟰Loading local copy of {document}.json "
                    f"for {location[1]} at {location[0]}",
                    end="",
                )
                data: dict[str, Any] = json.load(file)
                print(" ✅")
                return data
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON from {file_path}: {e}")
            return None

    def read_list(self, location: list[str], document: str) -> list[str]:
        """Read a list of items from file with improved error handling"""
        folder_path = self._create_folder_path(location)
        file_path = folder_path / document

        try:
            with file_path.open("r", newline="") as file:
                print(
                    f"Loading items from {document}",
                    end="",
                )
                data: list[str] = file.read().splitlines()
                print(" ✅")
                return data
        except FileNotFoundError:
            return []

    def _create_folder_path(self, location: list[str]) -> Path:
        """Create and return sanitized folder path"""
        sanitized_location = [self._sanitize_path_component(str(x)) for x in location]
        folder_path = self.base_path.joinpath(*sanitized_location)
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    @staticmethod
    def _sanitize_path_component(component: str) -> str:
        """Sanitize path component by replacing invalid characters"""
        return component.replace("\\", "").replace("/", " & ")
