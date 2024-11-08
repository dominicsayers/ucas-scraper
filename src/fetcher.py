import httpx
import re
import time


class Fetcher:
    MAX_RETRIES = 3

    def __init__(self) -> None:
        self.client = self.__get_client()

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

    def __get_client(self) -> httpx.Client:
        return httpx.Client(http2=True, timeout=10.0)
