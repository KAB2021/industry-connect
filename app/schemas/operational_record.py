import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperationalRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    timestamp: datetime
    entity_id: str
    metric_name: str
    metric_value: float
    analysed: bool
    ingested_at: datetime


class WebhookPayload(BaseModel):
    timestamp: datetime
    entity_id: str
    metric_name: str
    metric_value: float


class CSVUploadResponse(BaseModel):
    records: list[OperationalRecordRead]
    mappings_applied: dict[str, str]
