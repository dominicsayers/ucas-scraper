import httpx
import json
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

    def fetch(self, uri: str) -> bytes | None:
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.get(uri, follow_redirects=True)
                result = None

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

    def post(self, uri: str, payload: dict[str, Any], headers: dict[str, str]) -> bytes:
        # The HTTPx documentation insists that `data` is passed as a `Mapping[str, Any]`
        # but I can't make it work unless it's manually converted to a string, hence we
        # need to ignore the typing on this line.
        response = self.client.post(
            uri,
            data=json.dumps(payload),  # type: ignore
            headers=headers,
            follow_redirects=True,
        )

        print(response)
        return response.content

    def __get_client(self) -> httpx.Client:
        return httpx.Client(http2=True, timeout=10.0)
