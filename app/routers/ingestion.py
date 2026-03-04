"""Ingestion router — CSV upload endpoint."""

import json

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.operational_record import OperationalRecord
from app.schemas.errors import CSVRowError, ErrorResponse
from app.schemas.operational_record import CSVUploadResponse, OperationalRecordRead
from app.services.csv_parser import parse_and_validate

router = APIRouter(prefix="/upload", tags=["ingestion"])


@router.post(
    "/csv",
    status_code=201,
    response_model=CSVUploadResponse,
    responses={
        413: {"description": "File too large"},
        422: {"model": ErrorResponse, "description": "Validation errors in CSV"},
    },
)
def upload_csv(
    file: UploadFile,
    db: Session = Depends(get_db),
    column_mapping: str | None = Form(default=None),
) -> CSVUploadResponse | JSONResponse:
    """Accept a multipart CSV upload, validate it, and persist each row."""

    # ---- Size check -------------------------------------------------------
    content: bytes = file.file.read()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

    # ---- Parse column_mapping ---------------------------------------------
    parsed_mapping: dict[str, str] | None = None
    if column_mapping is not None:
        try:
            parsed_mapping = json.loads(column_mapping)
        except json.JSONDecodeError as exc:
            error_response = ErrorResponse(
                errors=[
                    CSVRowError(
                        row=0,
                        field="column_mapping",
                        message=f"Invalid JSON: {exc}",
                    )
                ]
            )
            return JSONResponse(content=error_response.model_dump(), status_code=422)

        if not isinstance(parsed_mapping, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in parsed_mapping.items()
        ):
            error_response = ErrorResponse(
                errors=[
                    CSVRowError(
                        row=0,
                        field="column_mapping",
                        message="column_mapping must be a JSON object with string keys and string values",
                    )
                ]
            )
            return JSONResponse(content=error_response.model_dump(), status_code=422)

    # ---- Parse & validate -------------------------------------------------
    records, errors, mappings_applied = parse_and_validate(content, parsed_mapping)

    if errors:
        error_response = ErrorResponse(errors=errors)
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=422,
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

    return CSVUploadResponse(
        records=[OperationalRecordRead.model_validate(r) for r in orm_records],
        mappings_applied=mappings_applied,
    )
