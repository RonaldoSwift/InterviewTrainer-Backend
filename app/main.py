import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers.exams import router as exams_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
)
app.include_router(exams_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    error_codes = {
        404: "not_found",
        409: "conflict",
        422: "invalid_input",
    }
    message = (
        exc.detail
        if isinstance(exc.detail, str)
        else "La solicitud no pudo completarse."
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": error_codes.get(exc.status_code, "http_error"),
            "message": message,
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "invalid_input",
            "message": "La solicitud contiene datos inválidos.",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled application error")
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "Ocurrió un error interno.",
        },
    )
