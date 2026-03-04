"""Tests for CSV upload endpoint — task-2.1."""


from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.operational_record import OperationalRecord

VALID_CSV = (
    "timestamp,entity_id,metric_name,metric_value\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
    "2024-01-15T11:00:00Z,sensor-2,humidity,45.0\n"
)

HEADER_ONLY_CSV = "timestamp,entity_id,metric_name,metric_value\n"

EMPTY_CSV = ""

INVALID_ROWS_CSV = (
    "timestamp,entity_id,metric_name,metric_value\n"
    "not-a-date,sensor-1,temperature,72.5\n"
    "2024-01-15T10:30:00Z,sensor-2,humidity,not-a-number\n"
)

MISSING_FIELD_CSV = (
    "timestamp,entity_id,metric_name,metric_value\n"
    "2024-01-15T10:30:00Z,,temperature,72.5\n"
)


def _upload(client: TestClient, content: bytes, filename: str = "test.csv") -> object:
    """Helper to POST a CSV file to /upload/csv."""
    return client.post(
        "/upload/csv",
        files={"file": (filename, content, "text/csv")},
    )


# ---------------------------------------------------------------------------
# Valid CSV
# ---------------------------------------------------------------------------


def test_valid_csv_creates_records(client: TestClient, db_session: Session) -> None:
    """Valid CSV should return 201 and create one record per data row."""
    response = _upload(client, VALID_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2


def test_valid_csv_records_have_correct_source_and_analysed(
    client: TestClient, db_session: Session
) -> None:
    """Each created record must have source='csv' and analysed=False."""
    response = _upload(client, VALID_CSV.encode("utf-8"))
    assert response.status_code == 201
    for record in response.json():
        assert record["source"] == "csv"
        assert record["analysed"] is False


def test_valid_csv_records_appear_in_db(
    client: TestClient, db_session: Session
) -> None:
    """Records created via the endpoint should be queryable from the DB."""
    response = _upload(client, VALID_CSV.encode("utf-8"))
    assert response.status_code == 201
    db_session.expire_all()
    records = db_session.query(OperationalRecord).all()
    assert len(records) == 2
    for rec in records:
        assert rec.source == "csv"
        assert rec.analysed is False


# ---------------------------------------------------------------------------
# Oversized file
# ---------------------------------------------------------------------------


def test_oversized_csv_returns_413(client: TestClient) -> None:
    """A file larger than MAX_UPLOAD_BYTES must return 413."""
    # Build content slightly over 10 MB
    big_content = b"x" * (10 * 1024 * 1024 + 1)
    response = _upload(client, big_content)
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_invalid_rows_returns_422(client: TestClient) -> None:
    """CSV with unparseable rows must return 422 with ErrorResponse shape."""
    response = _upload(client, INVALID_ROWS_CSV.encode("utf-8"))
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0
    for err in body["errors"]:
        assert "row" in err
        assert "field" in err
        assert "message" in err


def test_empty_csv_returns_422(client: TestClient) -> None:
    """Completely empty CSV (no content at all) must return 422."""
    response = _upload(client, EMPTY_CSV.encode("utf-8"))
    assert response.status_code == 422


def test_header_only_csv_returns_422(client: TestClient) -> None:
    """CSV with only a header row (no data rows) must return 422."""
    response = _upload(client, HEADER_ONLY_CSV.encode("utf-8"))
    assert response.status_code == 422


def test_missing_required_field_returns_422(client: TestClient) -> None:
    """CSV row with a missing required field value must return 422."""
    response = _upload(client, MISSING_FIELD_CSV.encode("utf-8"))
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body


# ---------------------------------------------------------------------------
# Non-UTF-8 encoding
# ---------------------------------------------------------------------------


def test_non_utf8_csv_returns_422_not_500(client: TestClient) -> None:
    """Non-UTF-8 bytes must return 422 (not 500) with an encoding error."""
    # Latin-1 encoded bytes that are invalid UTF-8
    bad_bytes = b"timestamp,entity_id,metric_name,metric_value\n2024-01-15,s\xff\xfe,temp,1.0\n"
    response = _upload(client, bad_bytes)
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert len(body["errors"]) > 0
