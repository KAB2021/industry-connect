"""Tests for CSV upload endpoint — task-2.1."""

import json

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
    assert isinstance(body["records"], list)
    assert len(body["records"]) == 2


def test_valid_csv_records_have_correct_source_and_analysed(
    client: TestClient, db_session: Session
) -> None:
    """Each created record must have source='csv' and analysed=False."""
    response = _upload(client, VALID_CSV.encode("utf-8"))
    assert response.status_code == 201
    for record in response.json()["records"]:
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


# ---------------------------------------------------------------------------
# Column mapping helper — task-4.1
# ---------------------------------------------------------------------------


def _upload_with_mapping(
    client: TestClient,
    content: bytes,
    mapping: dict,
    filename: str = "test.csv",
) -> object:
    """Helper to POST a CSV file with an explicit column_mapping to /upload/csv."""
    return client.post(
        "/upload/csv",
        files={"file": (filename, content, "text/csv")},
        data={"column_mapping": json.dumps(mapping)},
    )


# ---------------------------------------------------------------------------
# SC1 — Canonical columns produce an identity mappings_applied
# ---------------------------------------------------------------------------

_CANONICAL_CSV = (
    "timestamp,entity_id,metric_name,metric_value\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc1_canonical_columns_identity_mapping(
    client: TestClient, db_session: Session
) -> None:
    """SC1: Canonical headers → 201 and mappings_applied maps each column to itself."""
    response = _upload(client, _CANONICAL_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    mappings = body["mappings_applied"]
    assert mappings["timestamp"] == "timestamp"
    assert mappings["entity_id"] == "entity_id"
    assert mappings["metric_name"] == "metric_name"
    assert mappings["metric_value"] == "metric_value"


# ---------------------------------------------------------------------------
# SC2 — Alias columns are resolved and reported in mappings_applied
# ---------------------------------------------------------------------------

_ALIAS_CSV = (
    "timestamp,site_id,metric,value\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc2_alias_columns_resolved(client: TestClient, db_session: Session) -> None:
    """SC2: Alias headers → 201 and mappings_applied reflects the alias resolution."""
    response = _upload(client, _ALIAS_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    mappings = body["mappings_applied"]
    assert mappings["timestamp"] == "timestamp"
    assert mappings["entity_id"] == "site_id"
    assert mappings["metric_name"] == "metric"
    assert mappings["metric_value"] == "value"


# ---------------------------------------------------------------------------
# SC3 — Explicit column_mapping combined with alias resolution
# ---------------------------------------------------------------------------

_EXPLICIT_AND_ALIAS_CSV = (
    "timestamp,my_entity,metric,value\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc3_explicit_mapping_plus_alias_composition(
    client: TestClient, db_session: Session
) -> None:
    """SC3: Explicit mapping for one column + alias resolution for others → 201."""
    response = _upload_with_mapping(
        client,
        _EXPLICIT_AND_ALIAS_CSV.encode("utf-8"),
        {"entity_id": "my_entity"},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["records"]) == 1
    mappings = body["mappings_applied"]
    assert mappings["entity_id"] == "my_entity"
    assert mappings["metric_name"] == "metric"
    assert mappings["metric_value"] == "value"


# ---------------------------------------------------------------------------
# SC4 — Extra columns are silently discarded
# ---------------------------------------------------------------------------

_EXTRA_COL_CSV = (
    "timestamp,entity_id,metric_name,metric_value,extra_col\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5,ignored\n"
)


def test_sc4_extra_columns_silently_discarded(
    client: TestClient, db_session: Session
) -> None:
    """SC4: CSV with an extra column returns 201; mappings_applied has exactly 4 keys."""
    response = _upload(client, _EXTRA_COL_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    assert len(body["records"]) == 1
    assert len(body["mappings_applied"]) == 4


# ---------------------------------------------------------------------------
# SC5 — Unresolvable column returns 422
# ---------------------------------------------------------------------------

_UNRESOLVABLE_CSV = (
    "timestamp,entity_id,metric_name,unknown_col\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc5_unresolvable_column_returns_422(client: TestClient) -> None:
    """SC5: CSV missing a required column equivalent → 422."""
    response = _upload(client, _UNRESOLVABLE_CSV.encode("utf-8"))
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert len(body["errors"]) > 0


# ---------------------------------------------------------------------------
# SC6 — Explicit mapping referencing an absent source column returns 422
# ---------------------------------------------------------------------------

_STANDARD_CSV = (
    "timestamp,entity_id,metric_name,metric_value\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc6_explicit_mapping_absent_column_returns_422(client: TestClient) -> None:
    """SC6: Explicit column_mapping pointing to a non-existent column → 422."""
    response = _upload_with_mapping(
        client,
        _STANDARD_CSV.encode("utf-8"),
        {"entity_id": "ghost"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert len(body["errors"]) > 0


# ---------------------------------------------------------------------------
# SC7 — Ambiguous columns (two sources resolve to same canonical) returns 422
# ---------------------------------------------------------------------------

_AMBIGUOUS_CSV = (
    "timestamp,entity_id,site_id,metric_name,metric_value\n"
    "2024-01-15T10:30:00Z,sensor-1,sensor-1,temperature,72.5\n"
)


def test_sc7_ambiguous_columns_returns_422(client: TestClient) -> None:
    """SC7: Two columns both resolving to entity_id → 422."""
    response = _upload(client, _AMBIGUOUS_CSV.encode("utf-8"))
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert len(body["errors"]) > 0


# ---------------------------------------------------------------------------
# SC8 — Case-insensitive header matching
# ---------------------------------------------------------------------------

_UPPERCASE_CSV = (
    "TIMESTAMP,ENTITY_ID,METRIC_NAME,METRIC_VALUE\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc8_case_insensitive_canonical_headers(
    client: TestClient, db_session: Session
) -> None:
    """SC8: Uppercase canonical header names are matched case-insensitively → 201."""
    response = _upload(client, _UPPERCASE_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    assert len(body["records"]) == 1


_MIXED_CASE_ALIAS_CSV = (
    "TIMESTAMP,Site_ID,METRIC_NAME,METRIC_VALUE\n"
    "2024-01-15T10:30:00Z,sensor-1,temperature,72.5\n"
)


def test_sc8_case_insensitive_alias_headers(
    client: TestClient, db_session: Session
) -> None:
    """SC8: Mixed-case alias headers are matched case-insensitively → 201."""
    response = _upload(client, _MIXED_CASE_ALIAS_CSV.encode("utf-8"))
    assert response.status_code == 201
    body = response.json()
    assert len(body["records"]) == 1


# ---------------------------------------------------------------------------
# SC9 — Alias table completeness (unit test on COLUMN_ALIASES dict)
# ---------------------------------------------------------------------------


def test_sc9_alias_table_completeness() -> None:
    """SC9: COLUMN_ALIASES has exactly 9 entries and no key overlaps REQUIRED_COLUMNS."""
    from app.services.csv_parser import COLUMN_ALIASES, REQUIRED_COLUMNS

    assert len(COLUMN_ALIASES) == 9, (
        f"Expected 9 aliases, got {len(COLUMN_ALIASES)}: {list(COLUMN_ALIASES)}"
    )
    for alias_key in COLUMN_ALIASES:
        assert alias_key not in REQUIRED_COLUMNS, (
            f"Alias key '{alias_key}' must not appear in REQUIRED_COLUMNS"
        )


# ---------------------------------------------------------------------------
# SC10 — Row-level error on aliased CSV uses canonical field name in message
# ---------------------------------------------------------------------------

_ALIAS_EMPTY_ENTITY_CSV = (
    "timestamp,site_id,metric,value\n"
    "2024-01-15T10:30:00Z,,temperature,72.5\n"
)


def test_sc10_row_error_reports_canonical_field_name(client: TestClient) -> None:
    """SC10: A row-level validation error on an aliased column reports the canonical name."""
    response = _upload(client, _ALIAS_EMPTY_ENTITY_CSV.encode("utf-8"))
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    row_errors = body["errors"]
    assert len(row_errors) > 0
    # The error must reference the canonical field name, not the alias.
    assert any(err["field"] == "entity_id" for err in row_errors), (
        f"Expected field 'entity_id' in errors but got: {[e['field'] for e in row_errors]}"
    )
