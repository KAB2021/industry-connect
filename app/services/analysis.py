"""Core analysis engine: single-pass and map-reduce over OperationalRecords."""

import json
import uuid
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.operational_record import OperationalRecord
from app.services.chunking import chunk_records
from app.services.token_counter import count_tokens

_MAX_REDUCE_ITERATIONS = 5

# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

_JSON_SCHEMA: dict[str, Any] = {
    "name": "analysis_output",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "A concise summary of the analysed records.",
            },
            "anomalies": {
                "type": "array",
                "description": "List of detected anomalies.",
                "items": {
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string"},
                        "metric_name": {"type": "string"},
                        "metric_value": {"type": "number"},
                        "explanation": {"type": "string"},
                    },
                    "required": [
                        "record_id",
                        "metric_name",
                        "metric_value",
                        "explanation",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "anomalies"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = (
    "You are an operational data analyst. "
    "Analyse the provided records and return a JSON object with a summary and "
    "any detected anomalies. Follow the provided JSON schema exactly."
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _serialize_records(records: list[OperationalRecord]) -> str:
    """Serialise a list of ORM records to a JSON string."""
    return json.dumps(
        [
            {
                "id": str(r.id),
                "source": r.source,
                "timestamp": r.timestamp.isoformat(),
                "entity_id": r.entity_id,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
            }
            for r in records
        ]
    )


def _build_prompt(data_json: str) -> str:
    """Return the user message content for a given JSON-serialised data blob."""
    return (
        "Analyse the following operational records and identify any anomalies.\n\n"
        f"Records:\n{data_json}"
    )


def _call_openai(client: OpenAI, prompt: str) -> dict[str, Any]:
    """Make a single chat completion call and return a dict with parsed fields."""
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_schema", "json_schema": _JSON_SCHEMA},  # type: ignore[call-overload]
    )
    raw_content: str = response.choices[0].message.content or ""
    parsed = json.loads(raw_content)
    return {
        "response_raw": raw_content,
        "summary": parsed.get("summary"),
        "anomalies": parsed.get("anomalies"),
        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
        "completion_tokens": response.usage.completion_tokens if response.usage else None,
    }


def _persist_result(
    session: Session,
    record_ids: list[str],
    prompt: str,
    call_result: dict[str, Any],
) -> AnalysisResult:
    """Persist a single AnalysisResult and return it."""
    ar = AnalysisResult(
        id=uuid.uuid4(),
        record_ids=record_ids,
        prompt=prompt,
        response_raw=call_result["response_raw"],
        summary=call_result["summary"],
        anomalies=call_result["anomalies"],
        prompt_tokens=call_result["prompt_tokens"],
        completion_tokens=call_result["completion_tokens"],
    )
    session.add(ar)
    session.flush()
    return ar


def _mark_analysed(session: Session, records: list[OperationalRecord]) -> None:
    """Set analysed=True on every record in *records*."""
    for rec in records:
        rec.analysed = True
    session.flush()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_analysis(session: Session) -> list[AnalysisResult]:
    """Analyse all unanalysed OperationalRecords.

    Parameters
    ----------
    session:
        A SQLAlchemy :class:`~sqlalchemy.orm.Session`. The caller is
        responsible for session lifecycle (commit/rollback/close).

    Returns
    -------
    list[AnalysisResult]:
        The persisted :class:`AnalysisResult` objects, or an empty list if
        there are no unanalysed records.
    """
    session.expire_on_commit = False

    records: list[OperationalRecord] = (
        session.query(OperationalRecord)
        .filter(OperationalRecord.analysed == False)  # noqa: E712
        .all()
    )

    if not records:
        return []

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    data_json = _serialize_records(records)
    total_tokens = count_tokens(data_json, settings.OPENAI_MODEL)

    results: list[AnalysisResult] = []

    if total_tokens <= settings.TOKEN_THRESHOLD:
        # ----------------------------------------------------------------
        # Single-pass: all records fit within the token budget
        # ----------------------------------------------------------------
        prompt = _build_prompt(data_json)
        call_result = _call_openai(client, prompt)
        record_ids = [str(r.id) for r in records]
        ar = _persist_result(session, record_ids, prompt, call_result)
        results.append(ar)
        _mark_analysed(session, records)
    else:
        # ----------------------------------------------------------------
        # Map phase: serialise each record as a plain dict for chunking
        # ----------------------------------------------------------------
        serialized_list = json.loads(data_json)
        chunks = chunk_records(
            serialized_list,
            token_threshold=settings.TOKEN_THRESHOLD,
            model=settings.OPENAI_MODEL,
        )

        chunk_summaries: list[str] = []
        all_anomalies: list[Any] = []
        chunk_results: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_json = json.dumps(chunk)
            prompt = _build_prompt(chunk_json)
            call_result = _call_openai(client, prompt)
            chunk_results.append(
                {
                    "chunk": chunk,
                    "prompt": prompt,
                    "call_result": call_result,
                }
            )
            if call_result["summary"]:
                chunk_summaries.append(call_result["summary"])
            if call_result["anomalies"]:
                all_anomalies.extend(call_result["anomalies"])

        # ----------------------------------------------------------------
        # Reduce phase: combine chunk summaries (recursively if needed)
        # ----------------------------------------------------------------
        combined_text = "\n\n".join(chunk_summaries)
        reduce_tokens = count_tokens(combined_text, settings.OPENAI_MODEL)

        for _ in range(_MAX_REDUCE_ITERATIONS):
            if reduce_tokens <= settings.TOKEN_THRESHOLD:
                break
            reduce_prompt = _build_prompt(combined_text)
            reduce_result = _call_openai(client, reduce_prompt)
            combined_text = reduce_result["summary"] or combined_text
            reduce_tokens = count_tokens(combined_text, settings.OPENAI_MODEL)
        else:
            if reduce_tokens > settings.TOKEN_THRESHOLD:
                raise RuntimeError(
                    f"Reduce phase did not converge after {_MAX_REDUCE_ITERATIONS} iterations"
                )

        # Final reduce call to get a unified summary
        reduce_prompt = (
            "The following are summaries from chunks of operational records. "
            "Combine them into one final summary and merge any anomalies.\n\n"
            f"{combined_text}"
        )
        final_result = _call_openai(client, reduce_prompt)
        if final_result["anomalies"]:
            all_anomalies.extend(final_result["anomalies"])

        # Persist one AnalysisResult per chunk (map) and one for the reduce
        record_id_str = [str(r.id) for r in records]

        for cr in chunk_results:
            chunk_record_ids = [str(item["id"]) for item in cr["chunk"]]
            ar = _persist_result(
                session,
                chunk_record_ids,
                cr["prompt"],
                cr["call_result"],
            )
            results.append(ar)

        # Persist the final reduce result referencing all records
        final_ar = _persist_result(
            session,
            record_id_str,
            reduce_prompt,
            {
                **final_result,
                "anomalies": all_anomalies or final_result["anomalies"],
            },
        )
        results.append(final_ar)
        _mark_analysed(session, records)

    session.commit()
    return results
