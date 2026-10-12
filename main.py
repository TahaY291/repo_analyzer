from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.redis import redis_client
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.security_headers import SecurityHeadersMiddleware
from app.auth.router import router as auth_router
from app.core.request_context import RequestContextMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# add this BEFORE the other middleware, so it ends up innermost


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    print("Connected to Redis")
    yield
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="GitHub Repository Intelligence Agent",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment == "production")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}