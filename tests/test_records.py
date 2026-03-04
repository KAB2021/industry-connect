"""Tests for GET /records endpoint (task-3.1)."""

import uuid
from datetime import UTC, datetime

from app.models.operational_record import OperationalRecord


def make_record(source: str, entity_id: str, metric_name: str, metric_value: float) -> OperationalRecord:
    """Helper to create an OperationalRecord instance."""
    return OperationalRecord(
        id=uuid.uuid4(),
        source=source,
        timestamp=datetime.now(UTC),
        entity_id=entity_id,
        metric_name=metric_name,
        metric_value=metric_value,
        analysed=False,
        ingested_at=datetime.now(UTC),
    )


def test_get_records_returns_all_records(client, db_session):
    """Test GET /records returns all records regardless of source."""
    records = [
        make_record("csv", "entity-1", "temperature", 23.5),
        make_record("webhook", "entity-2", "cpu_usage", 85.0),
        make_record("poll", "entity-3", "memory_usage", 60.0),
    ]
    for record in records:
        db_session.add(record)
    db_session.flush()

    response = client.get("/records")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    sources = {item["source"] for item in data}
    assert sources == {"csv", "webhook", "poll"}


def test_get_records_matches_schema(client, db_session):
    """Test that the response matches the OperationalRecordRead schema."""
    record = make_record("csv", "entity-schema-test", "disk_usage", 45.0)
    db_session.add(record)
    db_session.flush()

    response = client.get("/records")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Find our record in the response
    matching = [r for r in data if r["entity_id"] == "entity-schema-test"]
    assert len(matching) == 1
    item = matching[0]

    # Verify all OperationalRecordRead schema fields are present
    assert "id" in item
    assert "source" in item
    assert "timestamp" in item
    assert "entity_id" in item
    assert "metric_name" in item
    assert "metric_value" in item
    assert "analysed" in item
    assert "ingested_at" in item

    # Verify field values
    assert item["source"] == "csv"
    assert item["entity_id"] == "entity-schema-test"
    assert item["metric_name"] == "disk_usage"
    assert item["metric_value"] == 45.0
    assert item["analysed"] is False

    # Verify id is a valid UUID string
    uuid.UUID(item["id"])


def test_get_records_empty_db_returns_empty_list(client, db_session):
    """Test that an empty DB returns an empty list (not an error)."""
    response = client.get("/records")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_records_multiple_sources_all_returned(client, db_session):
    """Test that records from csv, webhook, and poll sources are all returned."""
    sources = ["csv", "webhook", "poll"]
    for i, source in enumerate(sources):
        record = make_record(source, f"entity-{i}", f"metric-{i}", float(i * 10))
        db_session.add(record)
    db_session.flush()

    response = client.get("/records")
    assert response.status_code == 200
    data = response.json()

    returned_sources = {item["source"] for item in data}
    for source in sources:
        assert source in returned_sources
