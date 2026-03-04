"""Tests for Pydantic schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisResponse,
    AnalysisResultRead,
    CSVRowError,
    ErrorResponse,
    OperationalRecordRead,
    WebhookPayload,
)


class TestOperationalRecordRead:
    def test_serialize_from_orm_attributes(self) -> None:
        """OperationalRecordRead can be constructed from ORM-like attribute dict."""
        record_id = uuid.uuid4()
        now = datetime.now(tz=UTC)

        record = OperationalRecordRead(
            id=record_id,
            source="sensor-a",
            timestamp=now,
            entity_id="entity-1",
            metric_name="temperature",
            metric_value=98.6,
            analysed=False,
            ingested_at=now,
        )

        assert record.id == record_id
        assert record.source == "sensor-a"
        assert record.entity_id == "entity-1"
        assert record.metric_name == "temperature"
        assert record.metric_value == 98.6
        assert record.analysed is False

    def test_model_validate_from_attributes(self) -> None:
        """OperationalRecordRead.model_validate works with from_attributes=True."""

        class FakeORM:
            id = uuid.uuid4()
            source = "sensor-b"
            timestamp = datetime.now(tz=UTC)
            entity_id = "entity-2"
            metric_name = "humidity"
            metric_value = 55.0
            analysed = True
            ingested_at = datetime.now(tz=UTC)

        record = OperationalRecordRead.model_validate(FakeORM())
        assert record.source == "sensor-b"
        assert record.analysed is True


class TestWebhookPayload:
    def test_valid_payload(self) -> None:
        payload = WebhookPayload(
            timestamp=datetime.now(tz=UTC),
            entity_id="entity-1",
            metric_name="pressure",
            metric_value=101.3,
        )
        assert payload.metric_value == 101.3

    def test_rejects_missing_timestamp(self) -> None:
        with pytest.raises(ValidationError):
            WebhookPayload(  # type: ignore[call-arg]
                entity_id="entity-1",
                metric_name="pressure",
                metric_value=101.3,
            )

    def test_rejects_missing_entity_id(self) -> None:
        with pytest.raises(ValidationError):
            WebhookPayload(  # type: ignore[call-arg]
                timestamp=datetime.now(tz=UTC),
                metric_name="pressure",
                metric_value=101.3,
            )

    def test_rejects_missing_metric_name(self) -> None:
        with pytest.raises(ValidationError):
            WebhookPayload(  # type: ignore[call-arg]
                timestamp=datetime.now(tz=UTC),
                entity_id="entity-1",
                metric_value=101.3,
            )

    def test_rejects_missing_metric_value(self) -> None:
        with pytest.raises(ValidationError):
            WebhookPayload(  # type: ignore[call-arg]
                timestamp=datetime.now(tz=UTC),
                entity_id="entity-1",
                metric_name="pressure",
            )


class TestErrorResponse:
    def test_produces_expected_structure(self) -> None:
        err = ErrorResponse(
            errors=[
                CSVRowError(row=1, field="metric_value", message="Not a number"),
                CSVRowError(row=3, field="timestamp", message="Invalid date"),
            ]
        )
        data = err.model_dump()
        assert data == {
            "errors": [
                {"row": 1, "field": "metric_value", "message": "Not a number"},
                {"row": 3, "field": "timestamp", "message": "Invalid date"},
            ]
        }

    def test_empty_errors_list(self) -> None:
        err = ErrorResponse(errors=[])
        assert err.errors == []


class TestAllSchemasImportable:
    def test_all_schemas_importable(self) -> None:
        """Verify all schemas are importable from app.schemas."""
        import app.schemas as schemas

        assert hasattr(schemas, "OperationalRecordRead")
        assert hasattr(schemas, "WebhookPayload")
        assert hasattr(schemas, "AnalysisResultRead")
        assert hasattr(schemas, "AnalysisResponse")
        assert hasattr(schemas, "CSVRowError")
        assert hasattr(schemas, "ErrorResponse")

    def test_analysis_result_read_from_attributes(self) -> None:
        """AnalysisResultRead.model_validate works with ORM-like objects."""

        class FakeAnalysisORM:
            id = uuid.uuid4()
            record_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
            summary = "No anomalies detected"
            anomalies = []
            prompt = "Analyse the following records"
            response_raw = '{"result": "ok"}'
            prompt_tokens = 120
            completion_tokens = 80
            created_at = datetime.now(tz=UTC)

        result = AnalysisResultRead.model_validate(FakeAnalysisORM())
        assert result.summary == "No anomalies detected"
        assert len(result.record_ids) == 2

    def test_analysis_response_wrapper(self) -> None:
        result_read = AnalysisResultRead(
            id=uuid.uuid4(),
            record_ids=[str(uuid.uuid4())],
            summary="Test summary",
            anomalies=[],
            prompt="Test prompt",
            response_raw='{"summary": "Test"}',
            prompt_tokens=None,
            completion_tokens=None,
            created_at=datetime.now(tz=UTC),
        )
        response = AnalysisResponse(result=result_read)
        assert response.result.summary == "Test summary"
