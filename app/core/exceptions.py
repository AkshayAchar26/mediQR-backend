from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, status_code=404)

class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(code="CONFLICT", message=message, status_code=409)

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)

class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)

async def app_error_handler(request: Request, exc: AppError):
    logger.error("application_error", error_code=exc.code, message=exc.message, url=str(request.url))
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": {"code": exc.code, "message": exc.message}}
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", url=str(request.url), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}}
    )
