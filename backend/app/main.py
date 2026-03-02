from fastapi import FastAPI

from .auth import router as auth_router
from .config import get_settings
from .health import check_postgres, check_redis
from .stocks import router as stocks_router

app = FastAPI(title="Taiwan Stock AI API", version="0.1.0")
app.include_router(auth_router)
app.include_router(stocks_router)


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
