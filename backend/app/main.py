from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .ai import router as ai_router
from .auth import router as auth_router
from .config import get_settings
from .errors import http_exception_handler, validation_exception_handler
from .health import check_postgres, check_redis
from .stocks import router as stocks_router

app = FastAPI(title="Taiwan Stock AI API", version="0.1.0")
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(stocks_router)


def _parse_cors_origins(raw: str) -> list[str]:
    value = (raw or "").strip()
    if not value:
        return []
    if value == "*":
        return ["*"]

    origins: list[str] = []
    for item in value.split(","):
        origin = item.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


settings = get_settings()
cors_origins = _parse_cors_origins(settings.cors_allow_origins)

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False if cors_origins == ["*"] else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root() -> dict:
    return {"service": "taiwan-stock-ai", "status": "running"}


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    postgres = check_postgres(settings.database_url)
    redis_status = check_redis(settings.redis_url)

    ok = postgres["ok"] and redis_status["ok"]
    return {
        "status": "ok" if ok else "degraded",
        "services": {
            "postgres": postgres,
            "redis": redis_status,
        },
    }
