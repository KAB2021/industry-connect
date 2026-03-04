# Mock Server Schema

## Overview

The background poller fetches data from `POLL_SOURCE_URL` on a configurable interval (`POLL_INTERVAL_SECONDS`). This document defines the expected HTTP response schema that the external data source must provide.

## Endpoint

`GET {POLL_SOURCE_URL}`

## Response

### HTTP Status

`200 OK`

### Content-Type

`application/json`

### Body

The response body must be a JSON array of record objects. An empty array `[]` is valid and results in no records being persisted.

```json
[
  {
    "timestamp": "2024-01-15T10:00:00Z",
    "entity_id": "sensor-1",
    "metric_name": "temperature",
    "metric_value": 72.5
  },
  {
    "timestamp": "2024-01-15T10:01:00Z",
    "entity_id": "sensor-2",
    "metric_name": "pressure",
    "metric_value": 101.3
  }
]
```

## Field Definitions

| Field          | Type             | Required | Description                                                      |
|----------------|------------------|----------|------------------------------------------------------------------|
| `timestamp`    | string (ISO 8601)| Yes      | UTC timestamp of the measurement. Must include timezone offset.  |
| `entity_id`    | string           | Yes      | Identifier for the entity (device, sensor, etc.) being measured. |
| `metric_name`  | string           | Yes      | Name of the metric being recorded (e.g., "temperature").         |
| `metric_value` | number           | Yes      | Numeric value of the metric. Will be coerced to float.           |

## Persisted Fields

When a record is successfully polled, it is stored in the `operational_records` table with the following additional fields set by the poller:

| Field        | Value          | Description                                      |
|--------------|----------------|--------------------------------------------------|
| `source`     | `"poll"`       | Identifies that the record came from the poller. |
| `analysed`   | `false`        | Indicates the record has not yet been analysed.  |
| `ingested_at`| server default | UTC timestamp of when the record was persisted.  |

## Error Handling

| Scenario        | Poller Behaviour                                                    |
|-----------------|---------------------------------------------------------------------|
| HTTP 5xx        | Logs the error and retries after `POLL_INTERVAL_SECONDS`.           |
| HTTP 4xx        | Logs the error and retries after `POLL_INTERVAL_SECONDS`.           |
| Timeout         | Logs the error and retries after `POLL_INTERVAL_SECONDS`.           |
| Malformed JSON  | Logs the error and retries after `POLL_INTERVAL_SECONDS`.           |
| Missing fields  | Rolls back the transaction, logs the error, retries next cycle.     |
| Empty list `[]` | No records created; poller sleeps and retries after the interval.   |

## Example: cURL

```bash
curl -s http://localhost:8080/data | python3 -m json.tool
```

Expected output:

```json
[
  {
    "timestamp": "2024-01-15T10:00:00Z",
    "entity_id": "machine-001",
    "metric_name": "vibration",
    "metric_value": 0.42
  }
]
```
