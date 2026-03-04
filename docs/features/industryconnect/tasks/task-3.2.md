---
id: task-3.2
title: Analysis service with OpenAI, map-reduce chunking, and structured output
complexity: high
method: tdd
blocked_by: [task-1.2]
blocks: [task-3.3]
files: [app/services/analysis.py, app/services/chunking.py, app/services/token_counter.py, tests/test_analysis_service.py]
---

## Description
Implement the core analysis engine. token_counter.py wraps tiktoken using `encoding_for_model()` (not hardcoded encoding). chunking.py implements custom map-reduce: splits record batches into token-counted chunks targeting ~80% of context window with 2-3 rows overlap between chunks. analysis.py orchestrates: query unanalysed records, count tokens, decide single-pass vs map-reduce, call OpenAI with structured output (`response_format={"type": "json_schema", ...}`) for anomaly detection, persist AnalysisResult with all fields, mark records analysed=True. Use TDD with respx mocking OpenAI.

## Actions
1. Write `tests/test_analysis_service.py` — mock OpenAI with respx; test single-pass for small batch; test map-reduce triggers when tokens exceed threshold; test AnalysisResult persisted with all fields (including verbatim prompt string); test records marked analysed=True; test empty unanalysed set is no-op; test structured output json_schema is sent to OpenAI; test chunk overlap behaviour; test recursive reduce if combined summaries exceed context
2. Implement `app/services/token_counter.py` — `count_tokens(text: str, model: str) -> int` using `tiktoken.encoding_for_model(model)`
3. Implement `app/services/chunking.py` — `chunk_records(records, token_threshold, model) -> list[list[OperationalRecord]]` targeting 80% of context window with 2-3 row overlap
4. Implement map-reduce: summarise each chunk individually, combine chunk summaries; if combined summaries exceed context, apply reduce recursively
5. Implement `app/services/analysis.py` — `run_analysis(session_factory)` that queries analysed=False, decides strategy, calls OpenAI, persists AnalysisResult (prompt verbatim, response_raw, prompt_tokens, completion_tokens, summary, anomalies, record_ids), marks records analysed=True
6. Run tests

## Edge Cases
- Zero unanalysed records: no-op, return empty
- Single record under threshold: single-pass, no chunking
- Records exactly at threshold boundary: should not split unnecessarily
- Combined chunk summaries exceed context: recursive reduce

## Acceptance
- [ ] Only records with analysed=False are processed
- [ ] Records marked analysed=True after successful analysis
- [ ] AnalysisResult persisted with: prompt (verbatim rendered string), response_raw, prompt_tokens, completion_tokens, summary, anomalies, record_ids
- [ ] Map-reduce activates when tiktoken token count exceeds TOKEN_THRESHOLD
- [ ] Chunks target ~80% of model context window with 2-3 row overlap
- [ ] Recursive reduce handles case where combined summaries exceed context
- [ ] OpenAI call uses `response_format={"type": "json_schema", ...}` for structured output
- [ ] No processing when no unanalysed records exist
- [ ] Prompt construction is unit-tested (assert prompt field contains expected record data)
- [ ] All OpenAI calls mocked with respx
