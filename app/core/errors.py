import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"


class NotFoundError(Exception):
    pass


class RateLimitExceededError(Exception):
    def __init__(self, limit: str, retry_after_seconds: int) -> None:
        super().__init__(limit)
        self.limit = limit
        self.retry_after_seconds = retry_after_seconds


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str


class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationProblemDetail(ProblemDetail):
    errors: list[ValidationErrorItem]


def problem_response(
    request: Request,
    status: int,
    detail: str,
    errors: list[dict] | None = None,
) -> JSONResponse:
    problem = ProblemDetail(
        title=HTTPStatus(status).phrase,
        status=status,
        detail=detail,
        instance=request.url.path,
    )
    content = problem.model_dump()

    if errors is not None:
        content["errors"] = errors

    return JSONResponse(content, status_code=status, media_type=PROBLEM_MEDIA_TYPE)


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return problem_response(request, 422, "Request validation failed", errors)


async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
    return problem_response(request, 404, str(exc))


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    response = problem_response(request, exc.status_code, str(exc.detail))
    response.headers.update(exc.headers or {})
    return response


async def handle_rate_limit_exceeded(
    request: Request, exc: RateLimitExceededError
) -> JSONResponse:
    response = problem_response(request, 429, f"Rate limit exceeded: {exc.limit}")
    response.headers["Retry-After"] = str(exc.retry_after_seconds)
    return response


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return problem_response(request, 500, "Internal server error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(NotFoundError, handle_not_found_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RateLimitExceededError, handle_rate_limit_exceeded)
    app.add_exception_handler(Exception, handle_unexpected_error)
