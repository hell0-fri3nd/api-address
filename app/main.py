# main.py


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.address import address_router as ADDRESS_ROUTERS


def create_app(config) -> FastAPI:
    app = FastAPI(
        title=config.project_name,
        version=config.api_prefix,
        # lifespan=lifespan,
        description="""
API Documentation for the address book application.

### Features

- Create, update and Delete A address
- Retrieve addresses within a given distance and location coordinates.
""",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
        max_age=3600
    )
    
    for router in (
        ADDRESS_ROUTERS,
    ):
        app.include_router(router, prefix=config.api_prefix)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "ok"
        }

    return app


app = create_app(config)