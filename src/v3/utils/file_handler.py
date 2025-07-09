from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union, TypeVar, Generic, Optional
import os
import csv
import json
from abc import ABC, abstractmethod

T = TypeVar("T")


@dataclass
class FileHandlerConfig:
    """Configuration for file handler operations"""

    base_directory: str = "tmp"

    def __post_init__(self) -> None:
        self.base_directory = os.environ.get("OUTPUT", self.base_directory)


class FileHandlerWriter(ABC, Generic[T]):
    """Abstract base class for different file handler writers"""

    @abstractmethod
    def write(self, path: Path, content: T) -> None:
        pass


class JsonWriter(FileHandlerWriter[dict[str, Any]]):
    """Handles JSON file writing"""

    def write(self, path: Path, content: dict[str, Any]) -> None:
        with path.open("w", newline="") as file:
            json.dump(content, file, indent=4)


class HtmlWriter(FileHandlerWriter[str]):
    """Handles HTML file writing"""

    def write(self, path: Path, content: str) -> None:
        with path.open("w", newline="") as file:
            file.write(content)


class TextWriter(FileHandlerWriter[list[str]]):
    """Handles text file writing"""

    def write(self, path: Path, content: list[str]) -> None:
        with path.open("w") as file:
            file.writelines(content)


class CsvWriter(FileHandlerWriter[list[dict[str, str]]]):
    """Handles CSV file writing"""

    def write(
        self, path: Path, content: list[dict[str, str]], headers: list[str] = []
    ) -> None:
        with path.open("w", newline="") as file:
            writer = csv.DictWriter(file, headers)
            writer.writeheader()
            writer.writerows(content)


class FileHandler:
    """Manages file file handler operations with improved error handling and type safety"""

    def __init__(self, top_level: Union[str, int] = "data") -> None:
        self.config = FileHandlerConfig()
        self.top_level = str(top_level)
        self.base_path = Path(self.config.base_directory) / self.top_level
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize writers
        self.json_writer = JsonWriter()
        self.html_writer = HtmlWriter()
        self.text_writer = TextWriter()
        self.csv_writer = CsvWriter()

    def write_csv(
        self, name: str, content: list[dict[str, Any]], column_headers: list[str]
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
        content: Union[str, dict[str, str], list[str]],
    ) -> None:
        """Write content to either HTML, JSON or text file"""
        folder_path = self.__create_folder_path(location)

        output_path = None
        try:
            if isinstance(content, str):
                output_path = folder_path / f"{document}.html"
                self.html_writer.write(output_path, content)
            elif isinstance(content, dict):
                output_path = folder_path / f"{document}.json"
                self.json_writer.write(output_path, content)
            elif isinstance(content, list):
                output_path = folder_path / f"{document}.txt"
                self.text_writer.write(output_path, content)
        except IOError as e:
            print(f"Error writing file {output_path}: {e}")

    def read(
        self, location: list[str], document: str, fallback: bool = True
    ) -> Optional[dict[str, Any]]:
        """Read JSON data from file with improved error handling"""
        folder_path = self.__create_folder_path(location)
        file_path = folder_path / f"{document}.json"

        try:
            with file_path.open("r", newline="") as file:
                print(
                    f"   🟰 Loading local copy of {document}.json "
                    f"from {self.top_level} "
                    f"for {location[1]} at {location[0]}",
                    end="",
                )
                data: dict[str, Any] = json.load(file)
                print(" ✅")
                return data
        except FileNotFoundError:
            if not fallback:
                return None

            # Try to load from v1.1 data
            o = FileHandler("v1.1")
            data = o.read(location, document, fallback=False) or {}
            return data
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON from {file_path}: {e}")
            return None

    def read_list(self, location: list[str], document: str) -> list[str]:
        """Read a list of items from file with improved error handling"""
        folder_path = self.__create_folder_path(location)
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

    def cached_courses(self, location: list[str]) -> list[list[str]]:
        """Return a list of cached courses for a given location.

        Args:
            location: List of location components to build the folder path.

        Returns:
            List of paths to cached course folders.
        """
        folder_path = self.__create_folder_path(location)
        print(f"🔍 Checking for cached courses in {folder_path}")

        course_folders: list[list[str]] = []

        # Using os.walk to simplify nested directory traversal
        for root, dirs, _ in os.walk(folder_path):
            depth = root[len(str(folder_path)) :].count(os.sep)

            # We only want folders at depth 4 (provider/course/qualification/academic_year)
            if depth == 3 and dirs:
                course_folders.extend(
                    os.path.join(root, dir_name).split(os.sep)[-5:]
                    for dir_name in dirs
                    if self.__is_valid_dir(os.path.join(root, dir_name))
                )

        return course_folders

    @staticmethod
    def __is_valid_dir(path: str) -> bool:
        return os.path.isdir(path)

    def __create_folder_path(self, location: list[str]) -> Path:
        """Create and return sanitized folder path"""
        sanitized_location = [self.__sanitize_path_component(str(x)) for x in location]
        folder_path = self.base_path.joinpath(*sanitized_location)
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    @staticmethod
    def __sanitize_path_component(component: str) -> str:
        """Sanitize path component by replacing invalid characters"""
        return component.replace("\\", "").replace("/", " & ")
