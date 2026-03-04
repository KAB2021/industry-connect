"""Ingestion router — task-2.1: CSV upload endpoint."""

from fastapi import APIRouter, Depends, Response, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.errors import ErrorResponse
from app.schemas.operational_record import OperationalRecordRead
from app.services.csv_parser import parse_and_validate

router = APIRouter(prefix="/upload", tags=["ingestion"])


@router.post(
    "/csv",
    status_code=201,
    response_model=list[OperationalRecordRead],
    responses={
        413: {"description": "File too large"},
        422: {"model": ErrorResponse, "description": "Validation errors in CSV"},
    },
)
def upload_csv(
    file: UploadFile,
    response: Response,
    db: Session = Depends(get_db),
) -> list[OperationalRecordRead] | Response:
    """Accept a multipart CSV upload, validate it, and persist each row."""

    # ---- Size check -------------------------------------------------------
    content: bytes = file.file.read()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        return Response(status_code=413)

    # ---- Parse & validate -------------------------------------------------
    records, errors = parse_and_validate(content)

    if errors:
        error_response = ErrorResponse(errors=errors)
        return Response(
            content=error_response.model_dump_json(),
            status_code=422,
            media_type="application/json",
        )

    # ---- Persist ----------------------------------------------------------
    orm_records: list[OperationalRecord] = []
    for rec_data in records:
        orm_rec = OperationalRecord(**rec_data)
        db.add(orm_rec)
        orm_records.append(orm_rec)

    db.commit()

    for orm_rec in orm_records:
        db.refresh(orm_rec)

    return orm_records  # type: ignore[return-value]
