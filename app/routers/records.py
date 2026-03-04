from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.operational_record import OperationalRecordRead

router = APIRouter(tags=["records"])


@router.get("/records", response_model=list[OperationalRecordRead])
def get_records(db: Session = Depends(get_db)) -> list[OperationalRecord]:
    return db.query(OperationalRecord).all()
