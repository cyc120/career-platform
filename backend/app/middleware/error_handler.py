from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback


def register_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": "Validation error", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"},
        )
