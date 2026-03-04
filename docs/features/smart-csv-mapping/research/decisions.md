---
feature: smart-csv-mapping
type: decisions
created: 2026-03-04T00:00:00Z
---

# Technical Decisions: Smart CSV Column Mapping

## Decision 1: Response shape change strategy

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: Wrapper model (`CSVUploadResponse`) | Clean separation of `mappings_applied` from records; `OperationalRecordRead` stays unchanged for webhook/records endpoints | Breaking change — existing callers expect a raw JSON array; `test_integration.py` has 4+ assertions that break |
| B: Versioned endpoint (`/v2/upload/csv`) | No breakage; old endpoint stays as-is | Maintenance burden of two endpoints for a portfolio project; unnecessary complexity |
| C: Add `mappings_applied` as a response header | No body shape change; backward compatible | Non-standard; headers are strings, not structured JSON; harder to use in frontend |

### Recommendation
Option A because: this is a portfolio project with a known, internal-only frontend. There are no external consumers. The breakage is contained to `test_integration.py` (4 assertions) and possibly the React frontend's CSV upload handler. Updating these is straightforward and avoids the maintenance cost of versioned endpoints.

## Decision 2: `mappings_applied` content for identity case

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: Always include all 4 canonical fields | Consistent; callers always get the same keys; easy to inspect "what was used" | Slight verbosity on standard uploads |
| B: Only include fields that were actually remapped | Cleaner for standard uploads; empty dict means "nothing changed" | Callers must handle missing keys; harder to debug "was timestamp resolved?" |

### Recommendation
Option A because: the feature spec explicitly shows the identity mapping in Success Criterion 1 (`{"entity_id": "entity_id", ...}`). A consistent 4-key dict simplifies client code — no need to check for key existence. The direction is canonical name (key) → source column name (value), matching the spec.

## Decision 3: Alias table location

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: Module-level dict in `csv_parser.py` | Co-located with `REQUIRED_COLUMNS` (same pattern); no new files; zero indirection | Grows the file slightly |
| B: Separate `app/services/column_aliases.py` | Clean separation; independently importable | Over-engineered for a ~10-entry fixed dict; adds a file and import for no real benefit |
| C: Env var in `config.py` | Configurable per environment | The alias table is a compile-time constant, not a deployment concern; every other config value is runtime-injectable |

### Recommendation
Option A because: `REQUIRED_COLUMNS` at `csv_parser.py:9` establishes the exact precedent. The alias table is a domain constant consumed by one function in one file. A separate module adds indirection with no benefit.
