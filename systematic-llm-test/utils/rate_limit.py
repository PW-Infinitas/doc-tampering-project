import time
import functools
from typing import Callable, TypeVar
from config import RETRY_MAX_ATTEMPTS, RETRY_BACKOFF_SECONDS

F = TypeVar("F", bound=Callable)


def with_retry(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_error: Exception | None = None
        for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < RETRY_MAX_ATTEMPTS:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    print(f"  Attempt {attempt} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        raise RuntimeError(f"All {RETRY_MAX_ATTEMPTS} attempts failed") from last_error
    return wrapper  # type: ignore[return-value]
