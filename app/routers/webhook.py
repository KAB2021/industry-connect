"""Webhook ingestion router for POST /webhook endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.operational_record import OperationalRecordRead, WebhookPayload

router = APIRouter(tags=["ingestion"])


@router.post("/webhook", status_code=201, response_model=OperationalRecordRead)
def create_webhook_record(
    payload: WebhookPayload,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationalRecord:
    """Accept a JSON webhook payload and persist it as an OperationalRecord."""
    # Check Content-Length header against max upload size
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Request too large")

    record = OperationalRecord(
        source="webhook",
        timestamp=payload.timestamp,
        entity_id=payload.entity_id,
        metric_name=payload.metric_name,
        metric_value=payload.metric_value,
        analysed=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
