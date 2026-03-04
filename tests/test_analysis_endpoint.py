"""Tests for POST /analyse endpoint — task-3.3."""

import json
import uuid
from datetime import UTC, datetime

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.operational_record import OperationalRecord

# ---------------------------------------------------------------------------
# Mock OpenAI responses (same pattern as test_analysis_service.py)
# ---------------------------------------------------------------------------

MOCK_OPENAI_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {"summary": "All metrics normal.", "anomalies": []}
                ),
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_record(
    session: Session,
    metric_value: float = 42.0,
    analysed: bool = False,
    source: str = "test",
    metric_name: str = "temperature",
) -> OperationalRecord:
    """Create and persist an OperationalRecord."""
    rec = OperationalRecord(
        id=uuid.uuid4(),
        source=source,
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        entity_id="sensor-1",
        metric_name=metric_name,
        metric_value=metric_value,
        analysed=analysed,
    )
    session.add(rec)
    session.flush()
    return rec


# ---------------------------------------------------------------------------
# Tests: happy path
# ---------------------------------------------------------------------------


@respx.mock
def test_post_analyse_returns_analysis_results(
    client: TestClient,
    db_session: Session,
) -> None:
    """POST /analyse should return a list with analysis result data."""
    make_record(db_session, metric_value=72.5)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    response = client.post("/analyse")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    result = data[0]
    assert result["summary"] == "All metrics normal."
    assert result["anomalies"] == []
    assert result["prompt_tokens"] == 100
    assert result["completion_tokens"] == 50
    assert "id" in result
    assert "created_at" in result


@respx.mock
def test_post_analyse_records_marked_analysed(
    client: TestClient,
    db_session: Session,
) -> None:
    """After POST /analyse, the seeded records should have analysed=True."""
    rec1 = make_record(db_session, metric_value=10.0)
    rec2 = make_record(db_session, metric_value=20.0)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    response = client.post("/analyse")
    assert response.status_code == 200

    # Expire the cached objects and reload from DB
    db_session.expire_all()
    updated1 = db_session.get(OperationalRecord, rec1.id)
    updated2 = db_session.get(OperationalRecord, rec2.id)
    assert updated1 is not None
    assert updated2 is not None
    assert updated1.analysed is True
    assert updated2.analysed is True


@respx.mock
def test_post_analyse_result_persisted_in_db(
    client: TestClient,
    db_session: Session,
) -> None:
    """An AnalysisResult row should be persisted in the database."""
    make_record(db_session, metric_value=55.0)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    response = client.post("/analyse")
    assert response.status_code == 200

    db_session.expire_all()
    results_in_db = db_session.query(AnalysisResult).all()
    assert len(results_in_db) >= 1
    ar = results_in_db[0]
    assert ar.summary == "All metrics normal."


@respx.mock
def test_post_analyse_result_contains_record_ids(
    client: TestClient,
    db_session: Session,
) -> None:
    """The analysis result's record_ids should reference the seeded records."""
    rec = make_record(db_session, metric_value=99.9)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    response = client.post("/analyse")
    assert response.status_code == 200

    data = response.json()
    all_record_ids: list[str] = []
    for item in data:
        all_record_ids.extend(item["record_ids"])

    assert str(rec.id) in all_record_ids


# ---------------------------------------------------------------------------
# Tests: idempotency
# ---------------------------------------------------------------------------


@respx.mock
def test_post_analyse_idempotent_second_call_returns_empty(
    client: TestClient,
    db_session: Session,
) -> None:
    """A second POST /analyse should return an empty list (no unanalysed records)."""
    make_record(db_session, metric_value=5.0)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    # First call — processes the record
    response1 = client.post("/analyse")
    assert response1.status_code == 200
    assert len(response1.json()) >= 1

    # Second call — all records are now analysed
    response2 = client.post("/analyse")
    assert response2.status_code == 200
    assert response2.json() == []


# ---------------------------------------------------------------------------
# Tests: no unanalysed records
# ---------------------------------------------------------------------------


def test_post_analyse_no_unanalysed_records_returns_empty(
    client: TestClient,
    db_session: Session,
) -> None:
    """POST /analyse should return [] when there are no unanalysed records."""
    # All records already analysed
    make_record(db_session, analysed=True)
    db_session.flush()

    response = client.post("/analyse")

    assert response.status_code == 200
    assert response.json() == []


def test_post_analyse_empty_db_returns_empty(
    client: TestClient,
    db_session: Session,
) -> None:
    """POST /analyse should return [] when there are no records at all."""
    response = client.post("/analyse")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Tests: 413 when input data exceeds MAX_UPLOAD_BYTES
# ---------------------------------------------------------------------------


def test_post_analyse_413_when_data_exceeds_max_bytes(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /analyse should return 413 when total input data exceeds MAX_UPLOAD_BYTES."""
    # Lower the threshold so we don't actually need 10 MB of records in the test
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 100)

    # Create several records so that their serialised JSON exceeds 100 bytes
    for i in range(10):
        make_record(db_session, metric_value=float(i), source=f"sensor-{i}")
    db_session.flush()

    response = client.post("/analyse")

    assert response.status_code == 413
    body = response.json()
    assert "detail" in body


def test_post_analyse_413_with_actual_large_data(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /analyse returns 413 when records are genuinely larger than MAX_UPLOAD_BYTES."""
    # Use a 1 KB threshold to keep the test fast
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 1024)

    # Each record serialises to roughly 150–200 bytes; 20 records ~ 3–4 KB
    for i in range(20):
        make_record(
            db_session,
            metric_value=float(i),
            source="large-source-" + "x" * 50,
            metric_name="metric-" + "y" * 50,
        )
    db_session.flush()

    response = client.post("/analyse")

    assert response.status_code == 413
