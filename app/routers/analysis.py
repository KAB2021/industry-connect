"""Router for POST /analyse endpoint."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.analysis_result import AnalysisResultRead
from app.services.analysis import run_analysis

router = APIRouter(tags=["analysis"])


@router.post("/analyse", response_model=list[AnalysisResultRead])
def analyse(db: Session = Depends(get_db)) -> list:
    """Trigger analysis of all unanalysed operational records.

    Returns
    -------
    list[AnalysisResultRead]:
        The persisted analysis results, or an empty list if there are no
        unanalysed records.

    Raises
    ------
    HTTPException(413):
        If the serialised size of the unanalysed records exceeds
        ``settings.MAX_UPLOAD_BYTES``.
    """
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

    # Create a session factory bound to the same connection as the injected
    # session.  This ensures that in tests the analysis service operates on
    # the same test-database connection (and thus sees the seeded data).
    factory: sessionmaker = sessionmaker(bind=db.get_bind())

    results = run_analysis(factory)
    return results
