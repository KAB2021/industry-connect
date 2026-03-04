import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    record_ids: list[Any]
    summary: str | None
    anomalies: Any
    prompt: str | None
    response_raw: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    created_at: datetime


class AnalysisResponse(BaseModel):
    result: AnalysisResultRead
