from __future__ import annotations

import random

BASE_DELAY = 0.5
MAX_DELAY = 8.0
# ``idempotency_request_in_progress`` means the first attempt is still running: ask again this often,
# and stop asking once this long has passed since the first attempt of the call started.
IN_PROGRESS_POLL = 2.0
IN_PROGRESS_WAIT = 90.0


def is_retryable_status(status_code: int, code: str | None) -> bool:
    """Statuses the API documents as safe to retry with the same ``Idempotency-Key``."""
    if status_code in (429, 500, 502, 503):
        return True
    return is_in_progress(status_code, code)


def is_in_progress(status_code: int, code: str | None) -> bool:
    """The first request with this ``Idempotency-Key`` is still being processed."""
    return status_code == 409 and code == "idempotency_request_in_progress"


def retry_delay(attempt: int, *, retry_after: float | None = None, rand: random.Random | None = None) -> float:
    """Seconds before the next attempt: ``Retry-After`` when sent, else 0.5 s × 2^attempt with full jitter, capped at 8 s."""
    if retry_after is not None:
        return float(min(retry_after, 60.0))
    ceiling = min(MAX_DELAY, BASE_DELAY * (2**attempt))
    r = rand.random() if rand is not None else random.random()
    return float(ceiling * (0.5 + r * 0.5))


def in_progress_delay(elapsed: float, *, retry_after: float | None = None) -> float | None:
    """Seconds before asking again after ``idempotency_request_in_progress``: ``Retry-After`` when sent, else 2 s,
    capped at the time left. ``None`` once ``IN_PROGRESS_WAIT`` has passed (``elapsed`` is the time since the
    first attempt of the call started)."""
    remaining = IN_PROGRESS_WAIT - elapsed
    if remaining <= 0:
        return None
    wait = retry_after if retry_after is not None and retry_after > 0 else IN_PROGRESS_POLL
    return float(min(wait, remaining))
