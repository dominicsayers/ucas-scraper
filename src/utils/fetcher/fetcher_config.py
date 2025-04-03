from dataclasses import dataclass, field
from typing import Dict
import logging


@dataclass
class RateLimit:
    requests: int
    seconds: int
    counter: int = 0


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

    rate_limits: Dict[str, RateLimit] = field(
        default_factory=lambda: {"universal": RateLimit(requests=10, seconds=60)}
    )
