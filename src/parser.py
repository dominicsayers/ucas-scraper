from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag


class Parser:
    def __init__(self, response: bytes | None):
        self.soup = BeautifulSoup(str(response), "html.parser")

    @property
    def empty(self) -> bool:
        return not bool(self.soup.css)

    def select(self, selector: str) -> ResultSet[Tag] | list[None]:
        return [] if not self.soup.css else self.soup.css.select(selector)

    def prettify(self) -> str:
        return self.soup.prettify()


class ParserContent:
    def __init__(self, content: Tag | None):
        self.content = content

    def get_content_from(self, selector: str, type: str = "string") -> str:
        if not self.content:
            return ""

        try:
            match type:
                case "string":
                    result = str(self.content.select(selector)[0].string)
                case "link":
                    result = str(self.content.select(selector)[0].attrs["href"])
                case _:
                    raise Exception(f"Unknown type: {type}")

            return result
        except IndexError:
            return ""

    def prettify(self) -> str:
        return self.content.prettify() if self.content else ""
