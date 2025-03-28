from dataclasses import dataclass
from typing import Any, Optional, Union, Dict
from enum import Enum
import httpx
import logging
import re
import time
from pathlib import Path


class HttpVerb(Enum):
    """Supported HTTP verbs"""

    GET = "get"
    POST = "post"


class HttpError(Exception):
    """Custom exception for HTTP errors"""

    pass


@dataclass
class FetcherConfig:
    """Configuration for Fetcher"""

    max_retries: int = 3
    timeout: float = 10.0
    error_log_path: str = "tmp/errors.txt"
    http2_enabled: bool = True
    log_level: int = logging.WARN
    log_format: str = "%(levelname)s [%(asctime)s] %(name)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class ResponseHandler:
    """Handles HTTP response processing"""

    status_code: int
    content: Optional[bytes] = None
    text: Optional[str] = None

    def process(self) -> Union[bytes, int]:
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


class HttpClient:
    """Wrapper for HTTP client operations"""

    def __init__(self, config: FetcherConfig):
        self.config = config
        self.client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """Create new HTTP client"""
        return httpx.Client(
            http2=self.config.http2_enabled, timeout=self.config.timeout
        )

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute GET request"""
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Execute POST request"""
        return self.client.post(url, **kwargs)


class Fetcher:
    """Main class for handling HTTP requests with retries and error handling"""

    def __init__(self, config: Optional[FetcherConfig] = None):
        """
        Initialize Fetcher

        Args:
            config: Optional configuration override
        """
        self.config = config or FetcherConfig()
        self.client = HttpClient(self.config)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging"""
        logging.basicConfig(
            format=self.config.log_format,
            datefmt=self.config.log_date_format,
            level=self.config.log_level,
        )
        self.logger = logging.getLogger(__name__)

    def close(self) -> None:
        """Clean up resources"""
        self.client.close()

    def fetch(self, uri: str) -> Union[bytes, int, None]:
        """
        Fetch content from URI using GET

        Args:
            uri: URI to fetch

        Returns:
            Response content or status code

        Raises:
            HttpError: If request fails after retries
        """
        return self.request(HttpVerb.GET, uri, follow_redirects=True)

    def post(
        self, uri: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Union[bytes, int, None]:
        """
        Send POST request

        Args:
            uri: URI to post to
            payload: Request payload
            headers: Request headers

        Returns:
            Response content or status code

        Raises:
            HttpError: If request fails after retries
        """
        return self.request(
            HttpVerb.POST,
            uri,
            json=payload,
            headers=headers,
            follow_redirects=True,
        )

    def request(
        self, verb: HttpVerb, uri: str, **kwargs: Any
    ) -> Union[bytes, int, None]:
        """
        Execute HTTP request with retries

        Args:
            verb: HTTP verb to use
            uri: URI to request
            **kwargs: Additional request parameters

        Returns:
            Response content or status code

        Raises:
            HttpError: If request fails after retries
            ValueError: If verb is unknown
        """
        for attempt in range(self.config.max_retries):
            try:
                response = self._execute_request(verb, uri, **kwargs)
                return ResponseHandler(
                    response.status_code, response.content, response.text
                ).process()

            except (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ) as e:
                self._handle_retry(uri, attempt, e)
                continue

        self._handle_failure(uri)
        return None

    def _execute_request(
        self, verb: HttpVerb, uri: str, **kwargs: Any
    ) -> httpx.Response:
        """Execute single HTTP request"""
        match verb:
            case HttpVerb.GET:
                return self.client.get(uri, **kwargs)
            case HttpVerb.POST:
                return self.client.post(uri, **kwargs)
            case _:
                raise ValueError(f"Unknown HTTP verb: {verb}")

    def _handle_retry(self, uri: str, attempt: int, error: Exception) -> None:
        """Handle request retry"""
        self.logger.warning(
            f"Attempt {attempt + 1}/{self.config.max_retries} failed for {uri}: {error}"
        )
        print(f"  Retrying uri {uri}")
        time.sleep(1)
        self.client = HttpClient(self.config)

    def _handle_failure(self, uri: str) -> None:
        """Handle complete request failure"""
        self._log_error(uri)
        error_msg = f"Failed to fetch {uri} after {self.config.max_retries} attempts"
        self.logger.error(error_msg)
        raise HttpError(error_msg)

    def _log_error(self, uri: str) -> None:
        """Log error to file"""
        error_dir = Path(self.config.error_log_path).parent
        error_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config.error_log_path, "a") as f:
            f.write(f"{uri}\n")


def create_fetcher(
    max_retries: Optional[int] = None, timeout: Optional[float] = None
) -> Fetcher:
    """
    Factory function to create Fetcher instance

    Args:
        max_retries: Optional retry count override
        timeout: Optional timeout override

    Returns:
        Configured Fetcher instance
    """
    config = FetcherConfig()
    if max_retries is not None:
        config.max_retries = max_retries
    if timeout is not None:
        config.timeout = timeout
    return Fetcher(config)


def main() -> None:
    """Example usage of Fetcher"""
    try:
        fetcher = create_fetcher(max_retries=3, timeout=5.0)

        # GET request
        _content = fetcher.fetch("https://api.example.com/data")

        # POST request
        _response = fetcher.post(
            "https://api.example.com/submit",
            payload={"key": "value"},
            headers={"Content-Type": "application/json"},
        )

        fetcher.close()

    except HttpError as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    main()
