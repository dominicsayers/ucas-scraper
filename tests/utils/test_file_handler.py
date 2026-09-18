import json
from pathlib import Path

import pytest

from v3.utils.file_handler import (
    CsvWriter,
    FileHandler,
    FileHandlerConfig,
    HtmlWriter,
    JsonWriter,
    TextWriter,
)


@pytest.fixture(autouse=True)
def _use_tmp_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTPUT", str(tmp_path))


def test_config_reads_output_directory_from_environment(
    tmp_path: Path,
) -> None:
    config = FileHandlerConfig()

    assert config.base_directory == str(tmp_path)


def test_json_writer_writes_json_file(tmp_path: Path) -> None:
    path = tmp_path / "out.json"

    JsonWriter().write(path, {"a": 1})

    assert json.loads(path.read_text()) == {"a": 1}


def test_html_writer_writes_text_file(tmp_path: Path) -> None:
    path = tmp_path / "out.html"

    HtmlWriter().write(path, "<p>hi</p>")

    assert path.read_text() == "<p>hi</p>"


def test_text_writer_writes_lines(tmp_path: Path) -> None:
    path = tmp_path / "out.txt"

    TextWriter().write(path, ["a\n", "b\n"])

    assert path.read_text() == "a\nb\n"


def test_csv_writer_writes_rows_with_given_headers(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"

    CsvWriter().write(path, [{"a": "1", "b": "2"}], ["a", "b"])

    assert path.read_text().splitlines() == ["a,b", "1,2"]


def test_csv_writer_defaults_headers_to_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"

    CsvWriter().write(path, [])

    assert path.read_bytes() == b"\r\n"


def test_write_csv_writes_file(tmp_path: Path) -> None:
    handler = FileHandler("data")

    handler.write_csv("courses", [{"a": "1"}], ["a"])

    output = Path(handler.base_path, "courses.csv")
    assert output.read_text().splitlines() == ["a", "1"]


def test_write_csv_writes_error_file_on_value_error(tmp_path: Path) -> None:
    handler = FileHandler("data")

    # Mismatched headers cause csv.DictWriter to raise ValueError.
    handler.write_csv("courses", [{"unexpected": "1"}], ["a"])

    error_path = Path(handler.base_path, "courses.err")
    assert "unexpected" in error_path.read_text()


def test_write_writes_html_for_string_content() -> None:
    handler = FileHandler("data")

    handler.write(["providers"], "index", "<p>hi</p>")

    output = Path(handler.base_path, "providers", "index.html")
    assert output.read_text() == "<p>hi</p>"


def test_write_writes_json_for_dict_content() -> None:
    handler = FileHandler("data")

    handler.write(["providers"], "course", {"a": 1})

    output = Path(handler.base_path, "providers", "course.json")
    assert json.loads(output.read_text()) == {"a": 1}


def test_write_writes_text_for_list_content() -> None:
    handler = FileHandler("data")

    handler.write([], "ids", ["a\n", "b\n"])

    output = Path(handler.base_path, "ids.txt")
    assert output.read_text() == "a\nb\n"


def test_write_ignores_unsupported_content_types() -> None:
    handler = FileHandler("data")

    handler.write([], "course", 12345)  # type: ignore[arg-type]

    assert list(handler.base_path.iterdir()) == []


def test_write_handles_io_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    handler = FileHandler("data")

    def raise_io_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(handler.json_writer, "write", raise_io_error)

    handler.write([], "course", {"a": 1})

    assert "disk full" in capsys.readouterr().out


def test_read_returns_data_when_file_exists() -> None:
    handler = FileHandler("data")
    handler.write(["providers"], "course", {"a": 1})

    data = handler.read(["providers"], "course")

    assert data == {"a": 1}


def test_read_returns_none_when_missing_and_fallback_disabled() -> None:
    handler = FileHandler("data")

    data = handler.read(["providers"], "missing", fallback=False)

    assert data is None


def test_read_falls_back_to_v1_1_data_when_missing() -> None:
    handler = FileHandler("data")
    v1_1_handler = FileHandler("v1.1")
    v1_1_handler.write(["providers"], "course", {"legacy": True})

    data = handler.read(["providers"], "course")

    assert data == {"legacy": True}


def test_read_returns_empty_dict_when_missing_everywhere() -> None:
    handler = FileHandler("data")

    data = handler.read(["providers"], "missing")

    assert data == {}


def test_read_returns_none_on_invalid_json(tmp_path: Path) -> None:
    handler = FileHandler("data")
    file_path = handler.base_path / "broken.json"
    file_path.write_text("{not valid json")

    data = handler.read([], "broken")

    assert data is None


def test_read_list_returns_lines_when_file_exists() -> None:
    handler = FileHandler("data")
    file_path = handler.base_path / "ids.txt"
    file_path.write_text("a\nb\n")

    assert handler.read_list([], "ids.txt") == ["a", "b"]


def test_read_list_returns_empty_list_when_missing() -> None:
    handler = FileHandler("data")

    assert handler.read_list([], "missing.txt") == []


def test_cached_courses_finds_nested_qualification_folders() -> None:
    handler = FileHandler("data")
    course_dir = (
        handler.base_path
        / "providers"
        / "Example University"
        / "Engineering"
        / "BEng (Hons)"
        / "2025"
    )
    course_dir.mkdir(parents=True)

    courses = handler.cached_courses(["providers"])

    assert courses == [
        ["providers", "Example University", "Engineering", "BEng (Hons)", "2025"]
    ]


def test_cached_courses_returns_empty_list_when_none_cached() -> None:
    handler = FileHandler("data")

    assert handler.cached_courses(["providers"]) == []


def test_create_folder_path_sanitizes_slashes() -> None:
    handler = FileHandler("data")

    handler.write(["Example/University"], "note", "<p>hi</p>")

    output = Path(handler.base_path, "Example & University", "note.html")
    assert output.exists()


def test_top_level_defaults_to_string_representation() -> None:
    handler = FileHandler(2025)

    assert handler.top_level == "2025"
