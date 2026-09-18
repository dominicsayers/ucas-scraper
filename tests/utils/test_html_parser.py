from unittest.mock import MagicMock

import pytest

from v3.utils.html_parser import (
    ContentSelector,
    ContentType,
    HTMLParser,
    ParserContent,
    ParsingError,
    create_parser,
    main,
)

SAMPLE_HTML = """
<html>
    <body>
        <div class="content">
            <h1>Title</h1>
            <a href="https://example.com">Link</a>
        </div>
    </body>
</html>
"""


def test_create_parser_returns_html_parser() -> None:
    parser = create_parser(SAMPLE_HTML)

    assert isinstance(parser, HTMLParser)


def test_select_finds_matching_elements() -> None:
    parser = HTMLParser(SAMPLE_HTML)

    elements = parser.select("div.content")

    assert len(elements) == 1


def test_select_returns_empty_list_when_soup_has_no_css() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    parser.soup = MagicMock(css=None)

    assert parser.select("div.content") == []


def test_select_wraps_errors_in_parsing_error() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    parser.soup = MagicMock()
    parser.soup.css.select.side_effect = ValueError("boom")

    with pytest.raises(ParsingError, match="Error selecting elements"):
        parser.select("div.content")


def test_empty_is_false_for_normal_soup() -> None:
    parser = HTMLParser(SAMPLE_HTML)

    assert parser.empty is False


def test_empty_is_true_when_soup_has_no_css() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    parser.soup = MagicMock(css=None)

    assert parser.empty is True


def test_prettify_returns_formatted_html() -> None:
    parser = HTMLParser("<a>hi</a>")

    assert "<a>" in parser.prettify()


def test_prettify_wraps_errors_in_parsing_error() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    parser.soup = MagicMock()
    parser.soup.prettify.side_effect = ValueError("boom")

    with pytest.raises(ParsingError, match="Error prettifying content"):
        parser.prettify()


def test_create_soup_wraps_errors_in_parsing_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_value_error(*_args: object, **_kwargs: object) -> None:
        raise ValueError("boom")

    monkeypatch.setattr("v3.utils.html_parser.BeautifulSoup", raise_value_error)

    with pytest.raises(ParsingError, match="Error creating soup"):
        HTMLParser(SAMPLE_HTML)


def test_content_selector_returns_none_without_element() -> None:
    selector = ContentSelector(None)

    assert selector.select_content("h1") is None


def test_content_selector_selects_matching_elements() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    selector = ContentSelector(div)

    result = selector.select_content("h1")

    assert result is not None
    assert result[0].string == "Title"


def test_content_selector_wraps_errors_in_parsing_error() -> None:
    element = MagicMock()
    element.select.side_effect = ValueError("boom")
    selector = ContentSelector(element)

    with pytest.raises(ParsingError, match="Error selecting content"):
        selector.select_content("h1")


def test_get_content_from_returns_default_when_no_content() -> None:
    parser_content = ParserContent(None)

    assert parser_content.get_content_from("h1") == ""


def test_get_content_from_returns_string_content() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    assert parser_content.get_content_from("h1") == "Title"


def test_get_content_from_returns_link_href() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    assert (
        parser_content.get_content_from("a", ContentType.LINK) == "https://example.com"
    )


def test_get_content_from_accepts_string_content_type() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    assert parser_content.get_content_from("a", "link") == "https://example.com"


def test_get_content_from_returns_default_when_selector_matches_nothing() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    assert parser_content.get_content_from("p") == ""


def test_get_content_from_returns_default_when_selector_returns_empty() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)
    parser_content.selector = MagicMock()
    parser_content.selector.select_content.return_value = []

    assert parser_content.get_content_from("h1") == ""


def test_get_content_from_returns_default_on_index_error() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)
    selected = MagicMock()
    selected.__bool__.return_value = True
    selected.__getitem__.side_effect = IndexError("boom")
    parser_content.selector = MagicMock()
    parser_content.selector.select_content.return_value = selected

    assert parser_content.get_content_from("h1") == ""


def test_get_content_from_wraps_unexpected_errors() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)
    parser_content.selector = MagicMock()
    parser_content.selector.select_content.side_effect = ValueError("boom")

    with pytest.raises(ParsingError, match="Error getting content"):
        parser_content.get_content_from("h1")


def test_get_content_from_wraps_invalid_content_type_string() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    with pytest.raises(ParsingError, match="Error getting content"):
        parser_content.get_content_from("h1", "not-a-real-type")


def test_get_content_from_wraps_extraction_errors() -> None:
    element = MagicMock()
    element.attrs.get.side_effect = ValueError("boom")
    parser_content = ParserContent(MagicMock())
    parser_content.selector = MagicMock()
    parser_content.selector.select_content.return_value = [element]

    with pytest.raises(ParsingError, match="Error extracting content"):
        parser_content.get_content_from("a", ContentType.LINK)


def test_prettify_content_returns_formatted_html() -> None:
    parser = HTMLParser(SAMPLE_HTML)
    div = parser.select("div.content")[0]
    parser_content = ParserContent(div)

    assert "<h1>" in parser_content.prettify()


def test_prettify_content_returns_default_when_no_content() -> None:
    parser_content = ParserContent(None)

    assert parser_content.prettify() == ""


def test_prettify_content_wraps_errors_in_parsing_error() -> None:
    content = MagicMock()
    content.prettify.side_effect = ValueError("boom")
    parser_content = ParserContent(content)

    with pytest.raises(ParsingError, match="Error prettifying content"):
        parser_content.prettify()


def test_main_runs_without_error(capsys: pytest.CaptureFixture[str]) -> None:
    main()

    captured = capsys.readouterr()
    assert "Title: Title" in captured.out
    assert "Link: https://example.com" in captured.out


def test_main_skips_extraction_when_selection_is_not_a_result_set(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(HTMLParser, "select", lambda self, selector: [])

    main()

    assert capsys.readouterr().out == ""


def test_main_handles_parsing_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def raise_parsing_error(_html_content: str) -> HTMLParser:
        raise ParsingError("boom")

    monkeypatch.setattr("v3.utils.html_parser.create_parser", raise_parsing_error)

    main()

    assert "Error parsing content: boom" in capsys.readouterr().out
