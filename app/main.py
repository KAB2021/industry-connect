import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import SessionLocal
from app.routers import analysis, ingestion, records, webhook
from app.services.poller import run_poller


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    poller_task = asyncio.create_task(run_poller(SessionLocal))
    yield
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="IndustryConnect",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert FastAPI validation errors to the spec format."""
    errors = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = str(loc[-1]) if loc else "unknown"
        errors.append({"row": 0, "field": field, "message": err.get("msg", "")})
    return JSONResponse(status_code=422, content={"errors": errors})


app.include_router(ingestion.router)
app.include_router(webhook.router)
app.include_router(records.router)
app.include_router(analysis.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
