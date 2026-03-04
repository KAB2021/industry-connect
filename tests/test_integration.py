"""End-to-end integration test suite — task-4.1.

Tests the full ingestion → retrieval → analysis lifecycle across all three
ingestion paths: CSV upload, webhook POST, and background poller.
"""

import asyncio
import json
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.operational_record import OperationalRecord
from app.services.poller import poll_once

# ---------------------------------------------------------------------------
# Paths to fixture files
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_CSV_PATH = FIXTURES_DIR / "valid.csv"
INVALID_CSV_PATH = FIXTURES_DIR / "invalid.csv"

# ---------------------------------------------------------------------------
# Mock constants
# ---------------------------------------------------------------------------

MOCK_POLL_URL = "http://integration-poll-source.local/data"

MOCK_POLL_DATA = [
    {
        "timestamp": "2024-03-01T09:00:00Z",
        "entity_id": "poller-device-1",
        "metric_name": "voltage",
        "metric_value": 220.0,
    },
    {
        "timestamp": "2024-03-01T09:05:00Z",
        "entity_id": "poller-device-2",
        "metric_name": "current",
        "metric_value": 5.5,
    },
]

MOCK_OPENAI_RESPONSE = {
    "id": "chatcmpl-integration-test",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "summary": "Integration test: all metrics within normal range.",
                        "anomalies": [],
                    }
                ),
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 120,
        "completion_tokens": 60,
        "total_tokens": 180,
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _upload_csv(client: TestClient, path: Path) -> httpx.Response:
    """POST the CSV file at *path* to /upload/csv."""
    content = path.read_bytes()
    return client.post(
        "/upload/csv",
        files={"file": (path.name, content, "text/csv")},
    )


def _post_webhook(client: TestClient) -> httpx.Response:
    """POST a single valid webhook payload."""
    return client.post(
        "/webhook",
        json={
            "timestamp": "2024-03-01T10:00:00Z",
            "entity_id": "webhook-sensor-1",
            "metric_name": "cpu_usage",
            "metric_value": 78.3,
        },
    )


def _count_records_in_engine(engine: Engine, source: str | None = None) -> int:
    """Count OperationalRecord rows directly from the engine (bypasses test session)."""
    with engine.connect() as conn:
        stmt = select(func.count()).select_from(OperationalRecord)
        if source is not None:
            stmt = stmt.where(OperationalRecord.source == source)
        result = conn.execute(stmt)
        return result.scalar_one()


# ---------------------------------------------------------------------------
# Integration fixture: engine-based client (no transactional rollback)
#
# For the full lifecycle test we need records from all three sources to be
# visible to GET /records and POST /analyse.  The transactional db_session
# fixture rolls back after each test, so the poller's records (committed via
# a separate session) would be invisible to GET /records if the client is
# bound to the rolled-back connection.
#
# Solution: bind the test client directly to the test_engine so that all
# sessions share the same real database state.  The _clean_tables autouse
# fixture in conftest.py handles cleanup after each test.
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine_client(test_engine: Engine) -> Generator[TestClient, None, None]:
    """TestClient whose db session is created from test_engine directly.

    Unlike the standard ``client`` fixture this does NOT use a transactional
    connection, so records committed by the poller's own session are visible
    to the HTTP layer.
    """
    from app.db.session import get_db
    from app.main import app

    TestSession: sessionmaker[Session] = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    def override_get_db() -> Generator[Session, None, None]:
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ===========================================================================
# SECTION 1 — CSV ingestion path
# ===========================================================================


def test_csv_valid_upload_creates_records(client: TestClient) -> None:
    """Valid CSV upload must return 201 with records matching fixture rows."""
    response = _upload_csv(client, VALID_CSV_PATH)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, list)
    # valid.csv has 3 data rows
    assert len(body) == 3


def test_csv_records_have_correct_source_and_analysed(client: TestClient) -> None:
    """CSV-sourced records must have source='csv' and analysed=False."""
    response = _upload_csv(client, VALID_CSV_PATH)
    assert response.status_code == 201
    for record in response.json():
        assert record["source"] == "csv"
        assert record["analysed"] is False


def test_csv_records_conform_to_schema(client: TestClient) -> None:
    """Every CSV record in the response must contain all OperationalRecordRead fields."""
    response = _upload_csv(client, VALID_CSV_PATH)
    assert response.status_code == 201
    required_fields = {
        "id",
        "source",
        "timestamp",
        "entity_id",
        "metric_name",
        "metric_value",
        "analysed",
        "ingested_at",
    }
    for record in response.json():
        assert required_fields.issubset(record.keys())


def test_csv_invalid_returns_422_with_error_shape(client: TestClient) -> None:
    """Invalid CSV upload must return 422 with ErrorResponse containing CSVRowError list."""
    response = _upload_csv(client, INVALID_CSV_PATH)
    assert response.status_code == 422
    body = response.json()
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0
    for err in body["errors"]:
        assert "row" in err
        assert "field" in err
        assert "message" in err


def test_csv_invalid_returns_422_with_nonzero_row(client: TestClient) -> None:
    """Validation errors from CSV data rows should have row > 0 (row 0 is file-level)."""
    response = _upload_csv(client, INVALID_CSV_PATH)
    assert response.status_code == 422
    body = response.json()
    # invalid.csv has data-row errors so at least one error with row >= 1
    row_numbers = [e["row"] for e in body["errors"]]
    assert any(r >= 1 for r in row_numbers)


# ===========================================================================
# SECTION 2 — Webhook ingestion path
# ===========================================================================


def test_webhook_creates_record(client: TestClient) -> None:
    """Webhook POST must return 201 with source='webhook' and analysed=False."""
    response = _post_webhook(client)
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "webhook"
    assert data["analysed"] is False


def test_webhook_invalid_missing_fields_returns_422_row0(client: TestClient) -> None:
    """Webhook POST with missing fields must return 422 (row=0 in error context)."""
    response = client.post(
        "/webhook",
        json={"timestamp": "2024-03-01T10:00:00Z"},
    )
    assert response.status_code == 422


def test_webhook_record_appears_in_get_records(client: TestClient) -> None:
    """Record created via webhook must be retrievable via GET /records."""
    post_response = _post_webhook(client)
    assert post_response.status_code == 201
    record_id = post_response.json()["id"]

    get_response = client.get("/records")
    assert get_response.status_code == 200
    ids = [r["id"] for r in get_response.json()]
    assert record_id in ids


# ===========================================================================
# SECTION 3 — Poller ingestion path
# ===========================================================================


@respx.mock
def test_poller_creates_records_visible_via_get_records(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Records created by the poller must appear in GET /records."""
    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))

    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))
    assert count == len(MOCK_POLL_DATA)

    response = engine_client.get("/records")
    assert response.status_code == 200
    records = response.json()
    poll_sources = [r for r in records if r["source"] == "poll"]
    assert len(poll_sources) == len(MOCK_POLL_DATA)


@respx.mock
def test_poller_records_have_correct_fields(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Polled records must have source='poll', analysed=False, and correct field values."""
    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))

    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    with Session(test_engine) as session:
        records = session.query(OperationalRecord).filter_by(source="poll").all()
    assert len(records) == 2
    for rec in records:
        assert rec.source == "poll"
        assert rec.analysed is False


# ===========================================================================
# SECTION 4 — Full lifecycle: all sources → GET /records → analyse → verify
# ===========================================================================


@respx.mock
def test_full_lifecycle_all_sources_appear_in_get_records(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CSV, webhook, and poller records must all appear in GET /records."""
    # --- CSV ingestion
    csv_response = _upload_csv(engine_client, VALID_CSV_PATH)
    assert csv_response.status_code == 201
    assert len(csv_response.json()) == 3  # valid.csv has 3 rows

    # --- Webhook ingestion
    wh_response = _post_webhook(engine_client)
    assert wh_response.status_code == 201

    # --- Poller ingestion
    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    poll_count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))
    assert poll_count == 2

    # --- GET /records: all six records visible
    get_response = engine_client.get("/records")
    assert get_response.status_code == 200
    records = get_response.json()
    assert len(records) == 6  # 3 csv + 1 webhook + 2 poll

    sources = {r["source"] for r in records}
    assert sources == {"csv", "webhook", "poll"}


@respx.mock
def test_full_lifecycle_records_conform_to_schema(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All records from all sources must conform to OperationalRecordRead schema."""
    # Ingest from all three sources
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    get_response = engine_client.get("/records")
    assert get_response.status_code == 200

    required_fields = {
        "id",
        "source",
        "timestamp",
        "entity_id",
        "metric_name",
        "metric_value",
        "analysed",
        "ingested_at",
    }
    for record in get_response.json():
        assert required_fields.issubset(record.keys()), (
            f"Record missing fields: {required_fields - record.keys()}"
        )


@respx.mock
def test_full_lifecycle_analysed_flag_false_after_ingestion(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All ingested records must have analysed=False before analysis is triggered."""
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    get_response = engine_client.get("/records")
    assert get_response.status_code == 200
    for record in get_response.json():
        assert record["analysed"] is False, (
            f"Record {record['id']} already has analysed=True before analysis"
        )


@respx.mock
def test_full_lifecycle_analysis_processes_all_records(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /analyse must return at least one AnalysisResult covering all ingested records."""
    # Ingest
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    # Mock OpenAI
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    # Analyse
    analyse_response = engine_client.post("/analyse")
    assert analyse_response.status_code == 200
    results = analyse_response.json()
    assert isinstance(results, list)
    assert len(results) >= 1


@respx.mock
def test_full_lifecycle_analysed_flag_true_after_analysis(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All records must have analysed=True after POST /analyse completes."""
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    analyse_response = engine_client.post("/analyse")
    assert analyse_response.status_code == 200

    # Verify directly in the database
    with Session(test_engine) as session:
        unanalysed = (
            session.query(OperationalRecord)
            .filter(OperationalRecord.analysed == False)  # noqa: E712
            .all()
        )
    assert unanalysed == [], (
        f"Expected 0 unanalysed records, found {len(unanalysed)}"
    )


@respx.mock
def test_full_lifecycle_analysis_result_all_fields_present(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every AnalysisResult must have all required fields present and non-null."""
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    analyse_response = engine_client.post("/analyse")
    assert analyse_response.status_code == 200
    results = analyse_response.json()

    required_result_fields = {
        "id",
        "record_ids",
        "prompt",
        "response_raw",
        "prompt_tokens",
        "completion_tokens",
        "summary",
        "anomalies",
        "created_at",
    }
    for result in results:
        assert required_result_fields.issubset(result.keys()), (
            f"AnalysisResult missing fields: {required_result_fields - result.keys()}"
        )
        # All fields must be non-null
        assert result["id"] is not None
        assert result["record_ids"] is not None
        assert len(result["record_ids"]) > 0
        assert result["prompt"] is not None
        assert result["response_raw"] is not None
        assert result["prompt_tokens"] is not None
        assert result["completion_tokens"] is not None
        assert result["summary"] is not None
        assert result["anomalies"] is not None
        assert result["created_at"] is not None


@respx.mock
def test_full_lifecycle_analysis_result_persisted_in_db(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AnalysisResult rows must be persisted in the database after POST /analyse."""
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    analyse_response = engine_client.post("/analyse")
    assert analyse_response.status_code == 200
    api_result_count = len(analyse_response.json())

    with Session(test_engine) as session:
        db_results = session.query(AnalysisResult).all()
    assert len(db_results) == api_result_count
    assert len(db_results) >= 1


@respx.mock
def test_full_lifecycle_second_analysis_skips_already_processed(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Second POST /analyse must return empty list — no reprocessing of analysed records."""
    _upload_csv(engine_client, VALID_CSV_PATH)
    _post_webhook(engine_client)

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    # First analysis
    first_response = engine_client.post("/analyse")
    assert first_response.status_code == 200
    assert len(first_response.json()) >= 1

    # Second analysis — all records are now analysed
    second_response = engine_client.post("/analyse")
    assert second_response.status_code == 200
    assert second_response.json() == [], (
        "Second /analyse call should return [] but got non-empty results"
    )


@respx.mock
def test_full_lifecycle_analysis_result_record_ids_cover_all_ingested(
    test_engine: Engine,
    engine_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All ingested record IDs must appear in the union of AnalysisResult.record_ids."""
    # Ingest all three sources
    csv_response = _upload_csv(engine_client, VALID_CSV_PATH)
    assert csv_response.status_code == 201
    wh_response = _post_webhook(engine_client)
    assert wh_response.status_code == 201

    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_POLL_URL)
    respx.get(MOCK_POLL_URL).mock(return_value=httpx.Response(200, json=MOCK_POLL_DATA))
    session_factory: sessionmaker[Session] = sessionmaker(bind=test_engine)
    asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    # Collect all ingested record IDs from GET /records
    get_response = engine_client.get("/records")
    assert get_response.status_code == 200
    all_ingested_ids = {r["id"] for r in get_response.json()}
    assert len(all_ingested_ids) == 6

    # Run analysis
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )
    analyse_response = engine_client.post("/analyse")
    assert analyse_response.status_code == 200

    # Collect all record_ids from analysis results
    union_record_ids: set[str] = set()
    for result in analyse_response.json():
        union_record_ids.update(result["record_ids"])

    assert all_ingested_ids == union_record_ids, (
        f"Missing record IDs in analysis results: {all_ingested_ids - union_record_ids}"
    )


# ===========================================================================
# SECTION 5 — Idempotency: analysis token/summary values match mock
# ===========================================================================


@respx.mock
def test_analysis_result_token_counts_match_mock(
    client: TestClient,
    db_session: Session,
) -> None:
    """prompt_tokens and completion_tokens in AnalysisResult must match the mock."""
    # Seed one record via the standard transactional client
    rec = OperationalRecord(
        id=uuid.uuid4(),
        source="csv",
        timestamp=datetime(2024, 3, 1, 8, 0, tzinfo=UTC),
        entity_id="sensor-A",
        metric_name="temperature",
        metric_value=22.5,
        analysed=False,
    )
    db_session.add(rec)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    response = client.post("/analyse")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["prompt_tokens"] == 120
    assert results[0]["completion_tokens"] == 60
    assert results[0]["summary"] == "Integration test: all metrics within normal range."
