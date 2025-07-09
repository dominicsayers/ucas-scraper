from dataclasses import dataclass
from typing import Optional, Union, TypeVar
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from enum import Enum


T = TypeVar("T")


class ContentType(Enum):
    """Supported content types for parsing"""

    STRING = "string"
    LINK = "link"


@dataclass
class ParserConfig:
    """Configuration for parser"""

    parser_type: str = "html.parser"
    default_value: str = ""


class ParsingError(Exception):
    """Custom exception for parsing errors"""

    pass


class ContentSelector:
    """Generic content selector for parsing HTML elements"""

    def __init__(self, element: Optional[Tag]):
        self.element = element

    def select_content(self, selector: str) -> Optional[ResultSet[Tag]]:
        """
        Select content using CSS selector

        Args:
            selector: CSS selector string

        Returns:
            List of matched elements or None
        """
        try:
            if not self.element:
                return None
            return self.element.select(selector)
        except Exception as e:
            raise ParsingError(f"Error selecting content: {e}")


class HTMLParser:
    """Main parser class for handling HTML content"""

    def __init__(
        self,
        response: Optional[Union[bytes, str]],
        config: Optional[ParserConfig] = None,
    ):
        """
        Initialize parser with response content

        Args:
            response: HTML content as bytes or string
            config: Parser configuration
        """
        self.config = config or ParserConfig()
        self.soup = self.__create_soup(response)

    def __create_soup(self, response: Optional[Union[bytes, str]]) -> BeautifulSoup:
        """
        Create BeautifulSoup instance from response

        Args:
            response: HTML content

        Returns:
            BeautifulSoup instance
        """
        try:
            return BeautifulSoup(str(response), self.config.parser_type)
        except Exception as e:
            raise ParsingError(f"Error creating soup: {e}")

    @property
    def empty(self) -> bool:
        """Check if parser contains any CSS content"""
        return not bool(self.soup.css)

    def select(self, selector: str) -> ResultSet[Tag] | list[Tag]:
        """
        Select elements using CSS selector

        Args:
            selector: CSS selector string

        Returns:
            ResultSet of matching Tags
        """
        try:
            return [] if not self.soup.css else self.soup.css.select(selector)
        except Exception as e:
            raise ParsingError(f"Error selecting elements: {e}")

    def prettify(self) -> str:
        """
        Return prettified HTML string

        Returns:
            Formatted HTML string
        """
        try:
            return self.soup.prettify()
        except Exception as e:
            raise ParsingError(f"Error prettifying content: {e}")


class ParserContent:
    """Handler for parsing specific HTML content"""

    def __init__(self, content: Optional[Tag]):
        """
        Initialize content parser

        Args:
            content: BeautifulSoup Tag to parse
        """
        self.content = content
        self.selector = ContentSelector(content)
        self.config = ParserConfig()

    def get_content_from(
        self, selector: str, content_type: Union[str, ContentType] = ContentType.STRING
    ) -> str:
        """
        Extract content from element using selector

        Args:
            selector: CSS selector string
            content_type: Type of content to extract (string or link)

        Returns:
            Extracted content as string

        Raises:
            ParsingError: If content extraction fails
        """
        if not self.content:
            return self.config.default_value

        try:
            selected = self.selector.select_content(selector)
            if not selected or not selected[0]:
                return self.config.default_value

            return self.__extract_content(selected[0], content_type)
        except IndexError:
            return self.config.default_value
        except Exception as e:
            raise ParsingError(f"Error getting content: {e}")

    def __extract_content(
        self, element: Tag, content_type: Union[str, ContentType]
    ) -> str:
        """
        Extract specific type of content from element

        Args:
            element: BeautifulSoup Tag
            content_type: Type of content to extract

        Returns:
            Extracted content as string

        Raises:
            TypeError: If content type is unknown
        """
        content_type = (
            content_type
            if isinstance(content_type, ContentType)
            else ContentType(content_type)
        )

        try:
            match content_type:
                case ContentType.STRING:
                    return str(element.string or "")
                case ContentType.LINK:
                    return str(element.attrs.get("href", ""))
                case _:
                    raise TypeError(f"Unknown content type: {content_type}")
        except Exception as e:
            raise ParsingError(f"Error extracting content: {e}")

    def prettify(self) -> str:
        """
        Return prettified content

        Returns:
            Formatted HTML string
        """
        try:
            return (
                self.content.prettify() if self.content else self.config.default_value
            )
        except Exception as e:
            raise ParsingError(f"Error prettifying content: {e}")


def create_parser(html_content: Union[bytes, str]) -> HTMLParser:
    """
    Factory function to create parser instance

    Args:
        html_content: HTML content to parse

    Returns:
        Parser instance
    """
    return HTMLParser(html_content)


def main() -> None:
    """Example usage of Parser classes"""
    html = """
    <html>
        <body>
            <div class="content">
                <h1>Title</h1>
                <a href="https://example.com">Link</a>
            </div>
        </body>
    </html>
    """

    try:
        # Create parser
        parser = create_parser(html)

        # Select content
        content = parser.select("div.content")
        if isinstance(content, ResultSet):
            # Parse specific content
            parser_content = ParserContent(content[0])

            # Extract different types of content
            title = parser_content.get_content_from("h1")
            link = parser_content.get_content_from("a", ContentType.LINK)

            print(f"Title: {title}")
            print(f"Link: {link}")
    except ParsingError as e:
        print(f"Error parsing content: {e}")


if __name__ == "__main__":
    main()
