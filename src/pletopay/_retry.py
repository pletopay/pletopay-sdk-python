from __future__ import annotations

import random

BASE_DELAY = 0.5
MAX_DELAY = 8.0
IN_PROGRESS_FLOOR = 1.0


def is_retryable_status(status_code: int, code: str | None) -> bool:
    """Statuses the API documents as safe to retry with the same ``Idempotency-Key``."""
    if status_code in (429, 500, 502, 503):
        return True
    return status_code == 409 and code == "idempotency_request_in_progress"


def retry_delay(
    attempt: int,
    *,
    retry_after: float | None = None,
    status_code: int | None = None,
    code: str | None = None,
    rand: random.Random | None = None,
) -> float:
    """Seconds before the next attempt: ``Retry-After`` when sent, else 0.5 s × 2^attempt with full jitter, capped at 8 s."""
    if retry_after is not None:
        return float(min(retry_after, 60.0))
    ceiling = min(MAX_DELAY, BASE_DELAY * (2**attempt))
    r = rand.random() if rand is not None else random.random()
    delay = ceiling * (0.5 + r * 0.5)
    floor = IN_PROGRESS_FLOOR if status_code == 409 and code == "idempotency_request_in_progress" else 0.0
    return float(max(delay, floor))
