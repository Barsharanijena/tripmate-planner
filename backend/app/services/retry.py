import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_call(fn: Callable[[], T], *, attempts: int = 2, backoff_seconds: float = 1.5) -> T:
    """Retries a flaky external call with linear backoff, then re-raises the last error.

    Covers transient failures (timeouts, rate limits, brief outages) on the
    handful of live API calls this app makes. Callers are still responsible
    for deciding what to do once retries are exhausted — see the try/except
    around each call site in the graph nodes.
    """

    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - intentionally broad, this is a generic retry wrapper
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(backoff_seconds * (attempt + 1))

    assert last_exc is not None
    raise last_exc
