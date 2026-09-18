from v3.utils.course_id_parser import CourseIdParser


def test_parse_returns_id_unchanged_when_not_a_url() -> None:
    assert CourseIdParser.parse("508f8040-1309-e5cb-ff57-c4ff9c902ed3") == (
        "508f8040-1309-e5cb-ff57-c4ff9c902ed3"
    )


def test_parse_extracts_id_from_url() -> None:
    url = "https://digital.ucas.com/coursedisplay/courses/508f8040-1309-e5cb-ff57-c4ff9c902ed3"
    assert CourseIdParser.parse(url) == "508f8040-1309-e5cb-ff57-c4ff9c902ed3"


def test_parse_extracts_id_from_url_with_query_string() -> None:
    url = (
        "https://digital.ucas.com/coursedisplay/courses/"
        "508f8040-1309-e5cb-ff57-c4ff9c902ed3?academicYearId=2025"
    )
    assert CourseIdParser.parse(url) == "508f8040-1309-e5cb-ff57-c4ff9c902ed3"


def test_parse_is_case_insensitive_for_scheme() -> None:
    url = "HTTPS://digital.ucas.com/coursedisplay/courses/abc123"
    assert CourseIdParser.parse(url) == "abc123"
