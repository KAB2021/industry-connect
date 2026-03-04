---
id: task-4.1
title: End-to-end integration test suite
complexity: high
method: write-test
blocked_by: [task-2.1, task-2.2, task-2.3, task-3.1, task-3.3]
blocks: [task-5.1]
files: [tests/test_integration.py, tests/fixtures/valid.csv, tests/fixtures/invalid.csv]
---

## Description
Comprehensive integration test covering all ingestion paths feeding into analysis and retrieval. Tests the full lifecycle: ingest via CSV, webhook, and poller → verify all appear in GET /records → run analysis → verify analysed flag flipped and AnalysisResult persisted → verify second analysis skips already-processed records. All mocking via respx.

## Actions
1. Create `tests/fixtures/valid.csv` with representative test data
2. Create `tests/fixtures/invalid.csv` with rows that trigger validation errors
3. Write `tests/test_integration.py` — full lifecycle test: upload CSV → POST webhook → trigger poller → GET /records (all three sources) → POST /analyse → verify AnalysisResult and analysed=True → POST /analyse again (no reprocessing)
4. Add assertion: all AnalysisResult fields are present and non-null (prompt, response_raw, prompt_tokens, completion_tokens, summary, anomalies, record_ids)
5. Add assertion: analysed flag lifecycle (false after ingestion, true after analysis)
6. Run full test suite

## Acceptance
- [ ] CSV, webhook, and poller ingestion paths all create records retrievable via GET /records
- [ ] All records conform to OperationalRecord schema regardless of source
- [ ] Analysis processes only unanalysed records and marks them analysed=True
- [ ] AnalysisResult persisted with all fields present and non-null
- [ ] Second analysis call does not reprocess already-analysed records
- [ ] CSV invalid path returns 422 with correct error shape
- [ ] Webhook invalid path returns 422 with row=0
- [ ] Full test suite passes with zero failures
