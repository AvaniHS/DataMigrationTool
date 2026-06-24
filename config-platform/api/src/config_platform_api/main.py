from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config_platform_api.config import get_settings
from config_platform_api.exceptions import ConnectionStoreError, MigrationStoreError
from config_platform_api.logging_setup import configure_logging, get_logger
from config_platform_api.middleware.request_logging import RequestLoggingMiddleware
from config_platform_api.routers import connections, connectors, health, introspection, migrations
from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.services.connection_builder import ConnectionValidationError

from config_platform_api.dependencies import get_staging_store

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    staging_store = get_staging_store()
    removed = staging_store.purge_stale(ttl_days=settings.staging_ttl_days)
    if removed:
        logger.info("staging_startup_purge", removed=removed, ttl_days=settings.staging_ttl_days)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(connectors.router)
app.include_router(connections.router)
app.include_router(introspection.router)
app.include_router(migrations.router)


@app.exception_handler(ConnectionStoreError)
async def connection_store_error_handler(
    _request: Request,
    exc: ConnectionStoreError,
) -> JSONResponse:
    logger.error("connection_store_error", detail=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Connection registry is unavailable."},
    )


@app.exception_handler(MigrationStoreError)
async def migration_store_error_handler(
    _request: Request,
    exc: MigrationStoreError,
) -> JSONResponse:
    logger.error("migration_store_error", detail=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Migration registry is unavailable."},
    )


@app.exception_handler(ConnectionValidationError)
async def connection_validation_error_handler(
    _request: Request,
    exc: ConnectionValidationError,
) -> JSONResponse:
    logger.warning("connection_validation_failed", detail=str(exc))
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ConnectorValidationError)
async def connector_validation_error_handler(
    _request: Request,
    exc: ConnectorValidationError,
) -> JSONResponse:
    logger.warning("connector_validation_failed", detail=str(exc))
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("unhandled_exception", method=request.method, path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
