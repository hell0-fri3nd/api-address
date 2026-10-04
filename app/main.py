import logging

from fastapi import FastAPI

from app.addresses import router as addresses_router
from app.core import register_exception_handlers, settings

API_PREFIX = "/api/v1"

logging.basicConfig(level=settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Address Book API",
        version="0.1.0",
        description=(
            "Create, update and soft delete addresses, and find the addresses "
            "within a given distance of a location."
        ),
    )

    register_exception_handlers(app)
    app.include_router(addresses_router, prefix=API_PREFIX)

    return app


app = create_app()
