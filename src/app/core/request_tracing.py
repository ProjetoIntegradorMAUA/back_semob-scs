import logging
import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-ID"
PROCESS_TIME_HEADER = "X-Process-Time-Ms"

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_logger = logging.getLogger("semob.requests")


def _request_id(value: str | None) -> str:
    if value and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


async def trace_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        _logger.exception(
            "request_failed",
            extra={
                "request_id": request_id,
                "http_method": request.method,
                "http_path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = round((perf_counter() - started_at) * 1000, 3)
    response.headers[REQUEST_ID_HEADER] = request_id
    response.headers[PROCESS_TIME_HEADER] = str(duration_ms)
    _logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "http_method": request.method,
            "http_path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
