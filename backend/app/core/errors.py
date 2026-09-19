"""Centralized error handling. Every error response uses the same stable
shape ({"error": {"code", "message", "details"}}) and no handler ever
forwards a raw exception message or stack trace to the client for
unexpected failures (security.md #5: "No raw Python stack trace may be
returned to callers").
"""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("salary_api")


class PredictionInputError(ValueError):
    """A query parameter passed FastAPI's type validation but fails a
    domain rule sourced from model metadata (unsupported category, out of
    range numeric value, etc.)."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PredictionInputError)
    async def handle_prediction_input_error(request: Request, exc: PredictionInputError):
        return JSONResponse(status_code=422, content=error_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_body(
                "VALIDATION_ERROR",
                "One or more query parameters are invalid.",
                {"errors": jsonable_encoder(exc.errors())},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content=error_body("HTTP_ERROR", str(exc.detail)))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error while processing request")
        return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "An unexpected error occurred."))
