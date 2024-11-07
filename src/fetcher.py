import httpx
import logging
import re
import time
from typing import Any


class Fetcher:
    MAX_RETRIES = 3

    def __init__(self) -> None:
        self.client = self.__get_client()

        logging.basicConfig(
            format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.WARN,
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self, uri: str) -> bytes | int:
        return self.request("get", uri, follow_redirects=True)

    def post(
        self, uri: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> bytes | int:
        return self.request(
            "post",
            uri,
            json=payload,
            headers=headers,
            follow_redirects=True,
        )

    def request(self, verb: str, uri: str, **kwargs: Any) -> bytes | int:
        for _ in range(self.MAX_RETRIES):
            try:
                match verb:
                    case "get":
                        response = self.client.get(uri, **kwargs)
                    case "post":
                        response = self.client.post(uri, **kwargs)
                    case _:
                        raise ValueError(f"Unknown verb {verb}")

                result: bytes | int = response.status_code

                match response.status_code:
                    case 200:
                        result = response.content
                        print(" ✅")
                    case 404:
                        print(" - doesn't exist")
                    case _:
                        content = re.sub("\\s+", " ", response.text)[:79]
                        print(f" ❌ {response.status_code}: {content}")

                return result
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError):
                print(f"  Retrying uri {uri}")
                time.sleep(1)
                self.client = self.__get_client()
                continue
            else:
                break
        else:
            with open("tmp/errors.txt", "a") as f:
                f.write(f"{uri}\n")

            print(f"Error fetching uri {uri}")
            raise httpx.HTTPError("Unhandled HTTP error")

    def __get_client(self) -> httpx.Client:
        return httpx.Client(http2=True, timeout=10.0)
