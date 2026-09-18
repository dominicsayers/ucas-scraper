import re
from dataclasses import dataclass


@dataclass
class ResponseHandler:
    """Handles HTTP response processing"""

    status_code: int
    content: bytes | None = None
    text: str | None = None

    def process(self) -> bytes | int:
        """Process response based on status code"""
        match self.status_code:
            case 200:
                print(" ✅")
                return self.content or b""
            case 404:
                print(" - doesn't exist")
                return self.status_code
            case _:
                if self.text:
                    content = re.sub("\\s+", " ", self.text)[:79]
                    print(f" ❌ {self.status_code}: {content}")
                return self.status_code
