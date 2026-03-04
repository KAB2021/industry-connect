"""Tests for POST /webhook endpoint (task-2.2)."""



VALID_PAYLOAD = {
    "timestamp": "2024-01-15T10:30:00Z",
    "entity_id": "entity-123",
    "metric_name": "cpu_usage",
    "metric_value": 85.5,
}


def test_valid_webhook_creates_record(client):
    """Test that a valid webhook payload creates an OperationalRecord with source='webhook' and analysed=False."""
    response = client.post("/webhook", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "webhook"
    assert data["analysed"] is False
    assert data["entity_id"] == "entity-123"
    assert data["metric_name"] == "cpu_usage"
    assert data["metric_value"] == 85.5
    assert "id" in data
    assert "ingested_at" in data


def test_valid_webhook_returns_operationalrecord_schema(client):
    """Test that the response matches the OperationalRecordRead schema."""
    response = client.post("/webhook", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    # Verify all expected fields are present
    assert "id" in data
    assert "source" in data
    assert "timestamp" in data
    assert "entity_id" in data
    assert "metric_name" in data
    assert "metric_value" in data
    assert "analysed" in data
    assert "ingested_at" in data


def test_invalid_webhook_missing_fields_returns_422(client):
    """Test that a request missing required fields returns 422."""
    incomplete_payload = {
        "timestamp": "2024-01-15T10:30:00Z",
        # Missing entity_id, metric_name, metric_value
    }
    response = client.post("/webhook", json=incomplete_payload)
    assert response.status_code == 422


def test_invalid_webhook_empty_body_returns_422(client):
    """Test that an empty body returns 422."""
    response = client.post("/webhook", json={})
    assert response.status_code == 422


def test_invalid_webhook_missing_timestamp_returns_422(client):
    """Test that missing timestamp returns 422."""
    payload = {
        "entity_id": "entity-123",
        "metric_name": "cpu_usage",
        "metric_value": 85.5,
        # Missing timestamp
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 422


def test_webhook_exceeding_10mb_returns_413(client):
    """Test that a request exceeding 10MB content-length returns 413."""
    # Use custom content-length header that exceeds MAX_UPLOAD_BYTES (10485760)
    oversized_content_length = str(10485761)  # 10MB + 1 byte
    response = client.post(
        "/webhook",
        json=VALID_PAYLOAD,
        headers={"content-length": oversized_content_length},
    )
    assert response.status_code == 413


def test_webhook_at_limit_content_length_succeeds(client):
    """Test that a request at exactly MAX_UPLOAD_BYTES is allowed."""
    at_limit_content_length = str(10485760)  # exactly 10MB
    response = client.post(
        "/webhook",
        json=VALID_PAYLOAD,
        headers={"content-length": at_limit_content_length},
    )
    assert response.status_code == 201


def test_record_retrievable_after_creation(client, db_session):
    """Test that the record is persisted in the database after creation."""
    from app.models.operational_record import OperationalRecord

    response = client.post("/webhook", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    record_id = data["id"]

    # Query the database directly to verify the record was persisted
    import uuid
    record = db_session.get(OperationalRecord, uuid.UUID(record_id))
    assert record is not None
    assert record.source == "webhook"
    assert record.analysed is False
    assert record.entity_id == "entity-123"
    assert record.metric_name == "cpu_usage"
    assert record.metric_value == 85.5


def test_webhook_source_is_webhook(client):
    """Test that the source field is always set to 'webhook'."""
    response = client.post("/webhook", json=VALID_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["source"] == "webhook"


def test_webhook_analysed_defaults_to_false(client):
    """Test that analysed is always False for webhook-ingested records."""
    response = client.post("/webhook", json=VALID_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["analysed"] is False
