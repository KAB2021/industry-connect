"""Tests for analysis service — task-3.2."""

import json
import uuid
from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.operational_record import OperationalRecord

# ---------------------------------------------------------------------------
# Helpers
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

MOCK_OPENAI_RESPONSE_WITH_ANOMALY = {
    "id": "chatcmpl-test2",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "summary": "Anomaly detected.",
                        "anomalies": [
                            {
                                "record_id": "some-uuid",
                                "metric_name": "temperature",
                                "metric_value": 999.0,
                                "explanation": "Value is extremely high.",
                            }
                        ],
                    }
                ),
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 200,
        "completion_tokens": 80,
        "total_tokens": 280,
    },
}


def make_record(
    session: Session,
    metric_value: float = 42.0,
    analysed: bool = False,
) -> OperationalRecord:
    """Create and persist an OperationalRecord."""
    rec = OperationalRecord(
        id=uuid.uuid4(),
        source="test",
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        entity_id="sensor-1",
        metric_name="temperature",
        metric_value=metric_value,
        analysed=analysed,
    )
    session.add(rec)
    session.flush()
    return rec


def make_session_factory(db_session: Session) -> sessionmaker:
    """Return a sessionmaker that always yields the given session."""
    # We need a factory that creates a new session but we want to use
    # the test transaction. We wrap by providing a factory that returns
    # the same session object.
    factory = sessionmaker()
    factory.configure(bind=db_session.bind)
    return factory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session_factory(db_session: Session) -> sessionmaker:
    """Session factory that creates sessions on the test connection."""
    return make_session_factory(db_session)


# ---------------------------------------------------------------------------
# Token counter tests
# ---------------------------------------------------------------------------


def test_count_tokens_returns_positive_integer() -> None:
    """count_tokens should return a positive integer for non-empty text."""
    from app.services.token_counter import count_tokens

    result = count_tokens("Hello, world!", "gpt-4o-mini")
    assert isinstance(result, int)
    assert result > 0


def test_count_tokens_empty_string() -> None:
    """count_tokens should return 0 for an empty string."""
    from app.services.token_counter import count_tokens

    assert count_tokens("", "gpt-4o-mini") == 0


def test_count_tokens_longer_text_has_more_tokens() -> None:
    """Longer text should produce more tokens than shorter text."""
    from app.services.token_counter import count_tokens

    short = count_tokens("Hi", "gpt-4o-mini")
    long = count_tokens("Hi " * 100, "gpt-4o-mini")
    assert long > short


# ---------------------------------------------------------------------------
# Chunking tests
# ---------------------------------------------------------------------------


def test_chunk_records_small_batch_single_chunk() -> None:
    """A small batch under threshold should produce exactly one chunk."""
    from app.services.chunking import chunk_records

    records = [{"id": str(uuid.uuid4()), "value": i} for i in range(3)]
    chunks = chunk_records(records, token_threshold=4000, model="gpt-4o-mini")
    assert len(chunks) == 1
    assert chunks[0] == records


def test_chunk_records_large_batch_multiple_chunks() -> None:
    """Records exceeding the token threshold should be split into multiple chunks."""
    from app.services.chunking import chunk_records

    # Create records with large text to force chunking
    records = [
        {"id": str(uuid.uuid4()), "data": "word " * 300}
        for _ in range(20)
    ]
    chunks = chunk_records(records, token_threshold=1000, model="gpt-4o-mini")
    assert len(chunks) > 1


def test_chunk_records_overlap() -> None:
    """Consecutive chunks should share 2-3 records (overlap)."""
    from app.services.chunking import chunk_records

    records = [
        {"id": str(uuid.uuid4()), "data": "word " * 100}
        for _ in range(30)
    ]
    chunks = chunk_records(records, token_threshold=500, model="gpt-4o-mini")
    # Need at least 2 chunks to check overlap
    if len(chunks) >= 2:
        # Last records of chunk[0] should appear at start of chunk[1]
        last_of_first = chunks[0][-3:]
        first_of_second = chunks[1][:3]
        # At least 2 overlap records
        overlapping = [r for r in last_of_first if r in first_of_second]
        assert len(overlapping) >= 2


def test_chunk_records_all_records_covered() -> None:
    """Every record should appear in at least one chunk."""
    from app.services.chunking import chunk_records

    record_ids = [str(uuid.uuid4()) for _ in range(20)]
    records = [{"id": rid, "data": "word " * 100} for rid in record_ids]
    chunks = chunk_records(records, token_threshold=500, model="gpt-4o-mini")

    seen_ids = set()
    for chunk in chunks:
        for rec in chunk:
            seen_ids.add(rec["id"])

    assert seen_ids == set(record_ids)


# ---------------------------------------------------------------------------
# Analysis service — empty batch
# ---------------------------------------------------------------------------


def test_run_analysis_empty_returns_empty_list(db_session: Session) -> None:
    """run_analysis should return [] when there are no unanalysed records."""
    from app.services.analysis import run_analysis

    factory = make_session_factory(db_session)
    result = run_analysis(factory)
    assert result == []


def test_run_analysis_all_analysed_is_noop(db_session: Session) -> None:
    """run_analysis should return [] when all records are already analysed."""
    from app.services.analysis import run_analysis

    make_record(db_session, analysed=True)
    make_record(db_session, analysed=True)
    db_session.flush()

    factory = make_session_factory(db_session)
    result = run_analysis(factory)
    assert result == []


# ---------------------------------------------------------------------------
# Analysis service — single pass (small batch)
# ---------------------------------------------------------------------------


@respx.mock
def test_run_analysis_single_pass_persists_result(db_session: Session) -> None:
    """Single-pass analysis should persist one AnalysisResult."""
    from app.services.analysis import run_analysis

    rec = make_record(db_session, metric_value=72.5)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    assert len(results) == 1
    ar = results[0]
    assert isinstance(ar, AnalysisResult)
    assert ar.summary == "All metrics normal."
    assert ar.anomalies == []
    assert str(rec.id) in ar.record_ids
    assert ar.prompt_tokens == 100
    assert ar.completion_tokens == 50
    assert ar.response_raw is not None
    assert "All metrics normal." in ar.response_raw


@respx.mock
def test_run_analysis_marks_records_analysed(db_session: Session) -> None:
    """After analysis, all processed records should have analysed=True."""
    from app.services.analysis import run_analysis

    rec1 = make_record(db_session, metric_value=10.0)
    rec2 = make_record(db_session, metric_value=20.0)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    run_analysis(factory)

    # Reload from session
    db_session.expire_all()
    updated1 = db_session.get(OperationalRecord, rec1.id)
    updated2 = db_session.get(OperationalRecord, rec2.id)
    assert updated1.analysed is True
    assert updated2.analysed is True


@respx.mock
def test_run_analysis_prompt_contains_record_data(db_session: Session) -> None:
    """The prompt field of AnalysisResult must contain serialised record data."""
    from app.services.analysis import run_analysis

    make_record(db_session, metric_value=55.5)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    ar = results[0]
    assert ar.prompt is not None
    # The prompt should mention the metric value or entity_id
    assert "55.5" in ar.prompt or "sensor-1" in ar.prompt


@respx.mock
def test_run_analysis_response_raw_is_verbatim(db_session: Session) -> None:
    """response_raw should store the verbatim OpenAI response content."""
    from app.services.analysis import run_analysis

    make_record(db_session)
    db_session.flush()

    expected_content = json.dumps(
        {"summary": "All metrics normal.", "anomalies": []}
    )
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    assert results[0].response_raw == expected_content


@respx.mock
def test_run_analysis_token_counts_match_mock(db_session: Session) -> None:
    """prompt_tokens and completion_tokens should match the mock response."""
    from app.services.analysis import run_analysis

    make_record(db_session)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    ar = results[0]
    assert ar.prompt_tokens == 100
    assert ar.completion_tokens == 50


@respx.mock
def test_run_analysis_record_ids_in_result(db_session: Session) -> None:
    """AnalysisResult.record_ids should list all processed record UUIDs."""
    from app.services.analysis import run_analysis

    rec1 = make_record(db_session, metric_value=1.0)
    rec2 = make_record(db_session, metric_value=2.0)
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    all_record_ids: list[str] = []
    for ar in results:
        all_record_ids.extend(ar.record_ids)

    assert str(rec1.id) in all_record_ids
    assert str(rec2.id) in all_record_ids


# ---------------------------------------------------------------------------
# Analysis service — structured output schema
# ---------------------------------------------------------------------------


@respx.mock
def test_run_analysis_sends_json_schema_format(db_session: Session) -> None:
    """OpenAI call must use response_format with json_schema type."""
    from app.services.analysis import run_analysis

    make_record(db_session)
    db_session.flush()

    captured_requests: list[httpx.Request] = []

    def capture_and_respond(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json=MOCK_OPENAI_RESPONSE)

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        side_effect=capture_and_respond
    )

    factory = make_session_factory(db_session)
    run_analysis(factory)

    assert len(captured_requests) >= 1
    body = json.loads(captured_requests[0].content)
    assert "response_format" in body
    assert body["response_format"]["type"] == "json_schema"
    assert "json_schema" in body["response_format"]
    schema = body["response_format"]["json_schema"]
    # Schema must describe summary and anomalies
    schema_str = json.dumps(schema)
    assert "summary" in schema_str
    assert "anomalies" in schema_str


# ---------------------------------------------------------------------------
# Analysis service — map-reduce (large batch)
# ---------------------------------------------------------------------------


@respx.mock
def test_run_analysis_map_reduce_triggers_multiple_calls(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When tokens exceed threshold, multiple OpenAI calls should be made."""
    from app.services.analysis import run_analysis

    # Insert enough records to exceed a tiny threshold
    for i in range(5):
        make_record(db_session, metric_value=float(i))
    db_session.flush()

    call_count = 0

    def counting_responder(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=MOCK_OPENAI_RESPONSE)

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        side_effect=counting_responder
    )

    monkeypatch.setattr(settings, "TOKEN_THRESHOLD", 50)
    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    # Multiple calls = map phase + reduce phase
    assert call_count >= 2
    assert len(results) >= 1


@respx.mock
def test_run_analysis_map_reduce_all_records_marked_analysed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even with map-reduce, every processed record must be marked analysed."""
    from app.services.analysis import run_analysis

    recs = [make_record(db_session, metric_value=float(i)) for i in range(5)]
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    monkeypatch.setattr(settings, "TOKEN_THRESHOLD", 50)
    factory = make_session_factory(db_session)
    run_analysis(factory)

    db_session.expire_all()
    for rec in recs:
        updated = db_session.get(OperationalRecord, rec.id)
        assert updated.analysed is True


@respx.mock
def test_run_analysis_map_reduce_result_has_all_record_ids(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map-reduce results should collectively reference all processed records."""
    from app.services.analysis import run_analysis

    recs = [make_record(db_session, metric_value=float(i)) for i in range(5)]
    db_session.flush()

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=MOCK_OPENAI_RESPONSE)
    )

    monkeypatch.setattr(settings, "TOKEN_THRESHOLD", 50)
    factory = make_session_factory(db_session)
    results = run_analysis(factory)

    all_record_ids: list[str] = []
    for ar in results:
        all_record_ids.extend(ar.record_ids)

    for rec in recs:
        assert str(rec.id) in all_record_ids
