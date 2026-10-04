# error standar, bentuknya dipakai semua router
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: list | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def unauthenticated() -> AppError:
    return AppError(401, "UNAUTHENTICATED", "Sesi berakhir, silakan masuk kembali.")


def forbidden(message: str = "Kamu tidak punya izin untuk aksi ini.") -> AppError:
    return AppError(403, "FORBIDDEN", message)


def not_found(message: str = "Data tidak ditemukan.") -> AppError:
    return AppError(404, "NOT_FOUND", message)


def conflict(message: str = "Datanya sudah ada.") -> AppError:
    return AppError(409, "CONFLICT", message)


def error_body(request: Request, code: str, message: str, details: list | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": getattr(request.state, "request_id", ""),
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=error_body(request, exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in err["loc"][1:]), "issue": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=error_body(request, "VALIDATION_ERROR", "Isi permintaan tidak sesuai ketentuan.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(status_code=exc.status_code, content=error_body(request, code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_body(request, "INTERNAL_ERROR", "Terjadi gangguan, tim sudah menerima laporan."),
        )
