from typing import Any, Optional, Union, Dict
from pathlib import Path
import time
import httpx
import logging
import json
from .http_verb import HttpVerb
from .http_error import HttpError
from .fetcher_config import FetcherConfig
from .response_handler import ResponseHandler
from .http_client import HttpClient


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
        self.__setup_logging()

    def __setup_logging(self) -> None:
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

    def fetch_json(self, uri: str) -> dict[str, Any]:
        """
        Fetch JSON from URI using GET

        Args:
            uri: URI to fetch

        Returns:
            JSON response

        Raises:
            HttpError: If request fails after retries
        """
        response = self.fetch(uri)

        if isinstance(response, int):
            raise HttpError(uri, response)

        if not response:
            return {}

        try:
            return dict(json.loads(response))
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON response: {e}")
            return {}

    def fetch_json_with_rate_limit(
        self, uri: str, rate_limit_type: str = "universal"
    ) -> dict[str, Any]:
        """
        Fetch content from URI with rate limiting
        """
        self.__apply_rate_limit(rate_limit_type)
        return self.fetch_json(uri)

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

    def fetch_with_rate_limit(
        self, uri: str, rate_limit_type: str = "universal"
    ) -> Union[bytes, int, None]:
        """
        Fetch content from URI with rate limiting
        """
        self.__apply_rate_limit(rate_limit_type)
        return self.fetch(uri)

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

    def post_with_rate_limit(
        self,
        uri: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        rate_limit_type: str = "universal",
    ) -> Union[bytes, int, None]:
        """
        Fetch content from URI with rate limiting
        """
        self.__apply_rate_limit(rate_limit_type)
        return self.post(uri, payload, headers)

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
                response = self.__execute_request(verb, uri, **kwargs)
                return ResponseHandler(
                    response.status_code, response.content, response.text
                ).process()

            except (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ) as e:
                self.__handle_retry(uri, attempt, e)
                continue

        self.__handle_failure(uri)
        return None

    def __apply_rate_limit(self, limit_type: str) -> None:
        """Apply rate limiting"""
        if limit_type not in self.config.rate_limits:
            raise KeyError(f"Rate limit type {limit_type} not found")

        rate_limit = self.config.rate_limits[limit_type]
        rate_limit.counter += 1

        if rate_limit.counter > rate_limit.requests:
            rate_limit.counter = 0
            time.sleep(rate_limit.seconds)

    def __execute_request(
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

    def __handle_retry(self, uri: str, attempt: int, error: Exception) -> None:
        """Handle request retry"""
        self.logger.warning(
            f"Attempt {attempt + 1}/{self.config.max_retries} failed for {uri}: {error}"
        )
        print(f"  Retrying uri {uri}")
        time.sleep(1)
        self.client = HttpClient(self.config)

    def __handle_failure(self, uri: str) -> None:
        """Handle complete request failure"""
        self.__log_error(uri)
        error_msg = f"Failed to fetch {uri} after {self.config.max_retries} attempts"
        self.logger.error(error_msg)
        raise HttpError(error_msg)

    def __log_error(self, uri: str) -> None:
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
