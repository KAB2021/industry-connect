"""CSV parsing and validation service — task-2.1."""

import csv
import io
from datetime import UTC, datetime

from app.schemas.errors import CSVRowError

REQUIRED_COLUMNS = {"timestamp", "entity_id", "metric_name", "metric_value"}

COLUMN_ALIASES: dict[str, str] = {
    "site_id": "entity_id",
    "station_id": "entity_id",
    "asset_id": "entity_id",
    "metric": "metric_name",
    "measurement": "metric_name",
    "kpi": "metric_name",
    "value": "metric_value",
    "reading": "metric_value",
    "val": "metric_value",
}


def resolve_columns(
    raw_fields: list[str],
    column_mapping: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str], list[CSVRowError]]:
    """Resolve raw CSV fieldnames to canonical column names.

    Parameters
    ----------
    raw_fields:
        The fieldnames as they appear in the CSV header (original casing).
    column_mapping:
        Optional explicit mapping from canonical name → source column name.
        e.g. ``{"entity_id": "site_id"}`` means the ``entity_id`` canonical
        column is sourced from the ``site_id`` column in the CSV.

    Returns
    -------
    rename_map:
        Maps source column name (original casing) → canonical name.
        e.g. ``{"site_id": "entity_id"}``.
    mappings_applied:
        Always has exactly 4 keys (one per required column), mapping
        canonical name → source column name.
        e.g. ``{"entity_id": "site_id", "timestamp": "timestamp", ...}``.
    errors:
        List of :class:`CSVRowError` describing any problems found.
        ``row=0`` is used for header-level errors.
    """
    errors: list[CSVRowError] = []

    # Build a lowercase → original-casing lookup for O(1) membership tests.
    lower_to_raw: dict[str, str] = {f.lower(): f for f in raw_fields}
    lower_fields: set[str] = set(lower_to_raw)

    # rename_map: source col (original casing) → canonical name
    rename_map: dict[str, str] = {}
    # mappings_applied: canonical name → source col (original casing)
    mappings_applied: dict[str, str] = {}

    # Track which canonical columns have been resolved so far.
    resolved_canonicals: set[str] = set()

    # -----------------------------------------------------------------------
    # Step A — apply explicit column_mapping entries first.
    # column_mapping keys are canonical names, values are source col names.
    # -----------------------------------------------------------------------
    if column_mapping:
        for canonical, source_col in column_mapping.items():
            source_lower = source_col.lower()
            if source_lower not in lower_fields:
                errors.append(
                    CSVRowError(
                        row=0,
                        field=source_col,
                        message=(
                            f"Explicit mapping references column '{source_col}'"
                            " which is not present in CSV header."
                        ),
                    )
                )
                continue
            # Use the original casing of the source column from the header.
            raw_source = lower_to_raw[source_lower]
            rename_map[raw_source] = canonical
            mappings_applied[canonical] = raw_source
            resolved_canonicals.add(canonical)

    # -----------------------------------------------------------------------
    # Step B — for each still-unresolved required column try:
    #   1. canonical match (case-insensitive)
    #   2. alias match via COLUMN_ALIASES
    # We collect all candidate source columns per canonical so we can detect
    # collisions in Step C.
    # -----------------------------------------------------------------------
    # candidates: canonical → list of raw source column names that resolve to it
    candidates: dict[str, list[str]] = {c: [] for c in REQUIRED_COLUMNS}

    # Pre-populate candidates from Step A resolutions.
    for canonical, raw_source in mappings_applied.items():
        if canonical in REQUIRED_COLUMNS:
            candidates[canonical].append(raw_source)

    for raw_field, lower_field in ((r, r.lower()) for r in raw_fields):
        # Skip fields already consumed by an explicit mapping.
        # (A field could appear in rename_map already.)
        if raw_field in rename_map:
            continue

        # Canonical match
        if lower_field in REQUIRED_COLUMNS:
            candidates[lower_field].append(raw_field)
            continue

        # Alias match
        if lower_field in COLUMN_ALIASES:
            mapped_canonical = COLUMN_ALIASES[lower_field]
            candidates[mapped_canonical].append(raw_field)

    # -----------------------------------------------------------------------
    # Step C — detect collisions (multiple source cols → same canonical).
    # -----------------------------------------------------------------------
    for canonical, srcs in candidates.items():
        if len(srcs) > 1:
            errors.append(
                CSVRowError(
                    row=0,
                    field=canonical,
                    message=f"Ambiguous: multiple columns resolve to '{canonical}'",
                )
            )

    # -----------------------------------------------------------------------
    # Step D — detect unresolvable required columns, and finalise rename_map /
    # mappings_applied for the non-collision, non-explicit entries.
    # -----------------------------------------------------------------------
    for canonical in REQUIRED_COLUMNS:
        srcs = candidates[canonical]
        if canonical in resolved_canonicals:
            # Already handled by explicit mapping (Step A).
            continue
        if len(srcs) == 0:
            errors.append(
                CSVRowError(
                    row=0,
                    field=canonical,
                    message=f"Could not resolve required column '{canonical}'",
                )
            )
        elif len(srcs) == 1:
            raw_source = srcs[0]
            rename_map[raw_source] = canonical
            mappings_applied[canonical] = raw_source

    return rename_map, mappings_applied, errors


def parse_and_validate(
    file_content: bytes,
    column_mapping: dict[str, str] | None = None,
) -> tuple[list[dict], list[CSVRowError], dict[str, str]]:
    """Parse *file_content* as CSV and validate every row.

    Returns a tuple of:
      - records:          list of dicts ready to be inserted as OperationalRecord rows
      - errors:           list of CSVRowError objects (empty when all rows are valid)
      - mappings_applied: dict mapping canonical column name → source column name

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
        ], {}

    # --- Empty file --------------------------------------------------------
    if not text.strip():
        return [], [
            CSVRowError(row=0, field="file", message="CSV file is empty.")
        ], {}

    # --- Parse -------------------------------------------------------------
    reader = csv.DictReader(io.StringIO(text))

    # Validate that the header contains all required columns
    if reader.fieldnames is None:
        return [], [
            CSVRowError(row=0, field="file", message="CSV file has no header row.")
        ], {}

    # --- Resolve columns ---------------------------------------------------
    rename_map, mappings_applied, col_errors = resolve_columns(
        list(reader.fieldnames), column_mapping
    )
    if col_errors:
        return [], col_errors, {}

    records: list[dict] = []
    errors: list[CSVRowError] = []

    for row_index, row in enumerate(reader, start=1):
        renamed = {rename_map.get(k, k): v for k, v in row.items()}
        row_errors = _validate_row(row_index, renamed)
        if row_errors:
            errors.extend(row_errors)
        else:
            records.append(
                {
                    "timestamp": _parse_timestamp(renamed["timestamp"]),
                    "entity_id": renamed["entity_id"].strip(),
                    "metric_name": renamed["metric_name"].strip(),
                    "metric_value": float(renamed["metric_value"].strip()),
                    "source": "csv",
                    "analysed": False,
                }
            )

    # Header-only: no data rows at all
    if not records and not errors:
        return [], [
            CSVRowError(row=0, field="file", message="CSV file contains no data rows.")
        ], {}

    return records, errors, mappings_applied


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
