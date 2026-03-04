from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.operational_record import OperationalRecordRead

router = APIRouter(tags=["records"])


@router.get("/records", response_model=list[OperationalRecordRead])
def get_records(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[OperationalRecord]:
    return db.query(OperationalRecord).offset(offset).limit(limit).all()
