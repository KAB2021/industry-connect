"""Router for POST /analyse endpoint."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.analysis_result import AnalysisResult
from app.models.operational_record import OperationalRecord
from app.schemas.analysis_result import AnalysisResultRead
from app.services.analysis import run_analysis

router = APIRouter(tags=["analysis"])


@router.get("/analyse", response_model=list[AnalysisResultRead])
def list_analyses(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[AnalysisResult]:
    """Return all analysis results, most recent first."""
    return (
        db.query(AnalysisResult)
        .order_by(AnalysisResult.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/analyse", response_model=list[AnalysisResultRead])
def analyse(db: Session = Depends(get_db)) -> list[AnalysisResult]:
    """Trigger analysis of all unanalysed operational records."""
    records = (
        db.query(OperationalRecord)
        .filter(OperationalRecord.analysed == False)  # noqa: E712
        .all()
    )

    if not records:
        return []

    # Estimate size: serialise records and check against the upload limit
    data_json = json.dumps(
        [
            {
                "id": str(r.id),
                "source": r.source,
                "timestamp": r.timestamp.isoformat(),
                "entity_id": r.entity_id,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
            }
            for r in records
        ]
    )

    if len(data_json.encode()) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Input data too large for analysis",
        )

    results = run_analysis(db)
    return results
