import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.include_router(ingestion.router)
app.include_router(webhook.router)
app.include_router(records.router)
app.include_router(analysis.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
