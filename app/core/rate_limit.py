import math
import time

from fastapi import Request
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from .config import settings
from .errors import RateLimitExceededError

RATE_LIMIT = parse(settings.rate_limit)

_storage = MemoryStorage()
_rate_limiter = FixedWindowRateLimiter(_storage)


def enforce_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.method}:{request.scope['route'].path}"

    if not _rate_limiter.hit(RATE_LIMIT, key):
        reset_time = _rate_limiter.get_window_stats(RATE_LIMIT, key).reset_time
        retry_after_seconds = max(1, math.ceil(reset_time - time.time()))
        raise RateLimitExceededError(str(RATE_LIMIT), retry_after_seconds)


def reset_rate_limits() -> None:
    _storage.reset()
