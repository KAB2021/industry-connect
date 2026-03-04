"""CSV parsing and validation service — task-2.1."""

import csv
import io
from datetime import UTC, datetime

from app.schemas.errors import CSVRowError

REQUIRED_COLUMNS = {"timestamp", "entity_id", "metric_name", "metric_value"}


def parse_and_validate(
    file_content: bytes,
) -> tuple[list[dict], list[CSVRowError]]:
    """Parse *file_content* as CSV and validate every row.

    Returns a tuple of:
      - records: list of dicts ready to be inserted as OperationalRecord rows
      - errors:  list of CSVRowError objects (empty when all rows are valid)

    A non-empty *errors* list means the caller must **not** persist any records.
    """
    # --- Encoding ----------------------------------------------------------
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [], [
            CSVRowError(
                row=0,
                field="file",
                message=f"File encoding error: {exc}",
            )
        ]

    # --- Empty file --------------------------------------------------------
    if not text.strip():
        return [], [
            CSVRowError(row=0, field="file", message="CSV file is empty.")
        ]

    # --- Parse -------------------------------------------------------------
    reader = csv.DictReader(io.StringIO(text))

    # Validate that the header contains all required columns
    if reader.fieldnames is None:
        return [], [
            CSVRowError(row=0, field="file", message="CSV file has no header row.")
        ]

    missing_cols = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing_cols:
        return [], [
            CSVRowError(
                row=0,
                field=",".join(sorted(missing_cols)),
                message=f"Missing required columns: {', '.join(sorted(missing_cols))}",
            )
        ]

    records: list[dict] = []
    errors: list[CSVRowError] = []

    for row_index, row in enumerate(reader, start=1):
        row_errors = _validate_row(row_index, row)
        if row_errors:
            errors.extend(row_errors)
        else:
            records.append(
                {
                    "timestamp": _parse_timestamp(row["timestamp"]),
                    "entity_id": row["entity_id"].strip(),
                    "metric_name": row["metric_name"].strip(),
                    "metric_value": float(row["metric_value"].strip()),
                    "source": "csv",
                    "analysed": False,
                }
            )

    # Header-only: no data rows at all
    if not records and not errors:
        return [], [
            CSVRowError(row=0, field="file", message="CSV file contains no data rows.")
        ]

    return records, errors


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_row(row_index: int, row: dict) -> list[CSVRowError]:
    """Return a list of CSVRowError for any problems found in *row*."""
    errs: list[CSVRowError] = []

    # Check for None values (happens when a row has fewer columns than header)
    for field in REQUIRED_COLUMNS:
        if row.get(field) is None:
            errs.append(
                CSVRowError(
                    row=row_index,
                    field=field,
                    message=f"Field '{field}' is missing (row has fewer columns than header).",
                )
            )

    if errs:
        # Don't try to validate types when columns are outright missing
        return errs

    # --- entity_id ---------------------------------------------------------
    entity_id = row["entity_id"].strip()
    if not entity_id:
        errs.append(
            CSVRowError(
                row=row_index,
                field="entity_id",
                message="entity_id must not be empty.",
            )
        )

    # --- metric_name -------------------------------------------------------
    metric_name = row["metric_name"].strip()
    if not metric_name:
        errs.append(
            CSVRowError(
                row=row_index,
                field="metric_name",
                message="metric_name must not be empty.",
            )
        )

    # --- timestamp ---------------------------------------------------------
    ts_raw = row["timestamp"].strip()
    if not ts_raw:
        errs.append(
            CSVRowError(
                row=row_index,
                field="timestamp",
                message="timestamp must not be empty.",
            )
        )
    else:
        try:
            _parse_timestamp(ts_raw)
        except (ValueError, OverflowError):
            errs.append(
                CSVRowError(
                    row=row_index,
                    field="timestamp",
                    message=f"Invalid timestamp format: '{ts_raw}'. Expected ISO-8601.",
                )
            )

    # --- metric_value ------------------------------------------------------
    mv_raw = row["metric_value"].strip()
    if not mv_raw:
        errs.append(
            CSVRowError(
                row=row_index,
                field="metric_value",
                message="metric_value must not be empty.",
            )
        )
    else:
        try:
            float(mv_raw)
        except ValueError:
            errs.append(
                CSVRowError(
                    row=row_index,
                    field="metric_value",
                    message=f"metric_value must be numeric, got '{mv_raw}'.",
                )
            )

    return errs


def _parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp string into an aware datetime."""
    # Python 3.11+ fromisoformat handles 'Z' suffix; for older versions replace it.
    normalised = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalised)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt
