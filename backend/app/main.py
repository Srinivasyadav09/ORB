import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.cart import router as cart_router
from app.api.routes.orders import router as orders_router
from app.api.routes.addresses import router as addresses_router
from app.api.routes.admin_products import router as admin_products_router
from app.api.routes.categories import router as categories_router
from app.api.routes.admin import router as admin_router
from app.api.routes.customers import router as customers_router
from app.api.routes.farmers import router as farmers_router
from app.api.routes.farmer_products import router as farmer_products_router
from app.api.routes.products import router as products_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging(settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Application starting: %s (%s)", settings.APP_NAME, settings.APP_VERSION
    )
    yield
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ORB — Online Raithu Bazaar API",
    openapi_tags=[
        {
            "name": "Cart",
            "description": "Authenticated customer carts with current server-calculated prices and stock.",
        },
        {
            "name": "Addresses",
            "description": "Authenticated customer delivery addresses and default selection.",
        },
        {
            "name": "Customers",
            "description": "Authenticated customer profile operations.",
        },
        {"name": "Farmers", "description": "Farmer profiles and verification status."},
        {
            "name": "Admin / Farmer Verification",
            "description": "Admin-only farmer review and verification transitions.",
        },
        {
            "name": "Products",
            "description": "Public marketplace and farmer-owned product inventory.",
        },
        {"name": "Categories", "description": "Public active marketplace categories."},
        {
            "name": "Admin / Products",
            "description": "Admin-only product moderation listings.",
        },
    ],
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "Unhandled request exception method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "HTTP method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    # Pydantic errors include submitted values by default; never echo passwords,
    # tokens, email addresses, or other request input back to the caller.
    details = [
        {"type": error["type"], "loc": error["loc"], "msg": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get(
    "/health",
    response_model=dict[str, str],
    tags=["Health"],
    summary="Application health",
)
async def root_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(addresses_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(farmers_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(farmer_products_router, prefix="/api")
app.include_router(admin_products_router, prefix="/api")
