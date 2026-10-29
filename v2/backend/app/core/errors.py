import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


class AppError(Exception):
    """Expected business error returned to the client as {"code": ...}."""

    def __init__(self, status_code: int, code: str) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = []
        for error in exc.errors():
            location = error["loc"]
            field = ".".join(str(part) for part in location[1:]) or str(location[0])
            fields.append({"field": field, "type": error["type"]})
        return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error in %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})
