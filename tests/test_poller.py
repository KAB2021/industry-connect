"""Tests for the background poller service."""
import asyncio

import httpx
import pytest
import respx
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.operational_record import OperationalRecord
from app.services.poller import poll_once

MOCK_URL = "http://mock-poll-source.local/data"


@pytest.fixture(autouse=True)
def override_poll_url(monkeypatch):
    """Override POLL_SOURCE_URL for all tests in this module."""
    monkeypatch.setattr(settings, "POLL_SOURCE_URL", MOCK_URL)


@respx.mock
def test_poll_once_creates_records(test_engine, db_session):
    """poll_once should create OperationalRecord rows with source='poll' and analysed=False."""
    session_factory = sessionmaker(bind=test_engine)

    mock_data = [
        {
            "timestamp": "2024-01-15T10:00:00Z",
            "entity_id": "sensor-1",
            "metric_name": "temperature",
            "metric_value": 72.5,
        },
        {
            "timestamp": "2024-01-15T10:01:00Z",
            "entity_id": "sensor-2",
            "metric_name": "pressure",
            "metric_value": 101.3,
        },
    ]
    respx.get(MOCK_URL).mock(return_value=httpx.Response(200, json=mock_data))

    count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    assert count == 2

    records = db_session.query(OperationalRecord).filter_by(source="poll").all()
    assert len(records) == 2

    for record in records:
        assert record.source == "poll"
        assert record.analysed is False

    entity_ids = {r.entity_id for r in records}
    assert entity_ids == {"sensor-1", "sensor-2"}

    metric_names = {r.metric_name for r in records}
    assert metric_names == {"temperature", "pressure"}


@respx.mock
def test_poll_once_single_record_field_values(test_engine, db_session):
    """poll_once should persist all fields correctly."""
    session_factory = sessionmaker(bind=test_engine)

    mock_data = [
        {
            "timestamp": "2024-06-01T08:30:00Z",
            "entity_id": "device-42",
            "metric_name": "voltage",
            "metric_value": 220.0,
        }
    ]
    respx.get(MOCK_URL).mock(return_value=httpx.Response(200, json=mock_data))

    count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    assert count == 1

    record = db_session.query(OperationalRecord).filter_by(source="poll").first()
    assert record is not None
    assert record.entity_id == "device-42"
    assert record.metric_name == "voltage"
    assert record.metric_value == pytest.approx(220.0)
    assert record.analysed is False
    assert record.source == "poll"
    assert record.id is not None


@respx.mock
def test_poll_once_handles_http_error(test_engine):
    """poll_once should raise on HTTP 5xx but not cause unhandled crashes."""
    session_factory = sessionmaker(bind=test_engine)

    respx.get(MOCK_URL).mock(return_value=httpx.Response(500, text="Internal Server Error"))

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(poll_once(session_factory, httpx.AsyncClient()))


@respx.mock
def test_poll_once_handles_http_404(test_engine):
    """poll_once should raise on HTTP 404."""
    session_factory = sessionmaker(bind=test_engine)

    respx.get(MOCK_URL).mock(return_value=httpx.Response(404, text="Not Found"))

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(poll_once(session_factory, httpx.AsyncClient()))


@respx.mock
def test_poll_once_handles_malformed_json(test_engine):
    """poll_once should raise on malformed JSON responses."""
    session_factory = sessionmaker(bind=test_engine)

    respx.get(MOCK_URL).mock(
        return_value=httpx.Response(
            200,
            content=b"not valid json {{{",
            headers={"Content-Type": "application/json"},
        )
    )

    with pytest.raises((ValueError, KeyError)):
        asyncio.run(poll_once(session_factory, httpx.AsyncClient()))


@respx.mock
def test_poll_once_handles_missing_fields(test_engine):
    """poll_once should raise when required fields are missing from response items."""
    session_factory = sessionmaker(bind=test_engine)

    # Missing metric_value field
    mock_data = [
        {
            "timestamp": "2024-01-15T10:00:00Z",
            "entity_id": "sensor-1",
            "metric_name": "temperature",
            # metric_value is missing
        }
    ]
    respx.get(MOCK_URL).mock(return_value=httpx.Response(200, json=mock_data))

    with pytest.raises((KeyError, Exception)):
        asyncio.run(poll_once(session_factory, httpx.AsyncClient()))


@respx.mock
def test_poll_once_empty_response(test_engine, db_session):
    """poll_once should return 0 and create no records when server returns empty list."""
    session_factory = sessionmaker(bind=test_engine)

    respx.get(MOCK_URL).mock(return_value=httpx.Response(200, json=[]))

    count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    assert count == 0

    records = db_session.query(OperationalRecord).filter_by(source="poll").all()
    assert len(records) == 0


@respx.mock
def test_run_poller_skips_when_no_url(test_engine, monkeypatch):
    """run_poller should exit immediately when POLL_SOURCE_URL is not set."""
    from app.services.poller import run_poller

    class MockSettings:
        POLL_SOURCE_URL = ""
        POLL_INTERVAL_SECONDS = 1

    session_factory = sessionmaker(bind=test_engine)

    # Should return without error when URL is empty
    asyncio.run(run_poller(session_factory, poll_settings=MockSettings()))
    # If we reach here without hanging, the test passes


@respx.mock
def test_poll_once_returns_correct_count(test_engine, db_session):
    """poll_once should return the exact count of records created."""
    session_factory = sessionmaker(bind=test_engine)

    mock_data = [
        {
            "timestamp": f"2024-01-15T{10 + i:02d}:00:00Z",
            "entity_id": f"sensor-{i}",
            "metric_name": "metric",
            "metric_value": float(i),
        }
        for i in range(5)
    ]
    respx.get(MOCK_URL).mock(return_value=httpx.Response(200, json=mock_data))

    count = asyncio.run(poll_once(session_factory, httpx.AsyncClient()))

    assert count == 5
