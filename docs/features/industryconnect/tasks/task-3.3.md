---
id: task-3.3
title: POST /analyse endpoint
complexity: medium
method: tdd
blocked_by: [task-3.2]
blocks: [task-4.1]
files: [app/routers/analysis.py, app/main.py, tests/test_analysis_endpoint.py]
---

## Description
Implement POST /analyse endpoint that triggers the analysis service. Check total input size against MAX_UPLOAD_BYTES (10MB), return 413 if exceeded before any LLM call. Call run_analysis, return AnalysisResult(s). Handle case where no unanalysed records exist. Register router. Use TDD with respx mocking OpenAI.

## Actions
1. Write `tests/test_analysis_endpoint.py` — seed unanalysed records; mock OpenAI with respx; call POST /analyse; verify response contains AnalysisResult data; verify records now analysed=True; test idempotency (second call returns empty); verify AnalysisResult row in DB; test 413 when input data exceeds 10MB
2. Implement `app/routers/analysis.py` — POST /analyse route: check total unanalysed data size against MAX_UPLOAD_BYTES, return 413 if exceeded; otherwise call run_analysis
3. Register analysis router in `app/main.py`
4. Run tests

## Acceptance
- [ ] POST /analyse processes only analysed=False records
- [ ] Inputs exceeding 10MB rejected with HTTP 413 before any LLM call
- [ ] After call, processed records have analysed=True
- [ ] Response includes AnalysisResult with summary, anomalies, prompt_tokens, completion_tokens, record_ids
- [ ] Second call with no new unanalysed records returns gracefully (empty results)
- [ ] AnalysisResult row persisted in database with all required fields
