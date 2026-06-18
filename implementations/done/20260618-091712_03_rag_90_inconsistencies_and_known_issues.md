# Implementation: docs/03_rag_90_inconsistencies_and_known_issues.md

## Goal

Resolve OQ-1 ("External RAG service — authentication and error handling undefined") by documenting the decisions made in the implementation: auth via `X-RAG-Token` header, retry policy (2 retries, exponential backoff), explicit 10s timeout, and fallback conditions.

## Scope

- `docs/03_rag_90_inconsistencies_and_known_issues.md` — update OQ-1 entry from "open question" to "resolved"
- No code changes

## Assumptions

1. OQ-1 is at line ~59 in the doc (confirmed by grep).
2. The resolved decision: `X-RAG-Token` header (optional, default empty = no auth), 2 retries on 5xx/transport errors, 10s timeout, fallback on None, accept empty result.
3. Format should follow the existing doc's style for resolved issues (change status, add resolution).

## Implementation

### Target file

`docs/03_rag_90_inconsistencies_and_known_issues.md`

### Procedure

1. Locate OQ-1 section.
2. Change status from open to **Resolved** (or add a **Resolution:** line).
3. Add bullet points documenting the decisions:
   - Auth: `X-RAG-Token` header from `rag_auth_token` config field; empty = no auth (default)
   - Timeout: `timeout=10.0` seconds (connect + read) on each HTTP attempt
   - Retry: 2 retries for 5xx and transport errors; no retry on 4xx; exponential backoff (1s, 2s)
   - Fallback: `None` return → in-process; empty string `""` → valid result, no fallback
4. Update `- **Recommended action:**` line to reflect completed work.

### Method

Direct text edit. No structural changes to the doc format.

### Details

**Current OQ-1 text** (approximate):
```
### OQ-1: External RAG service — authentication and error handling undefined
...
- **Recommended action:** Define authentication headers and retry policy before enabling in production.
```

**Updated OQ-1:**
```
### OQ-1: External RAG service — authentication and error handling (RESOLVED)
...
- **Status:** Resolved — implemented in `rag/pipeline_service.py` and `shared/types.py`.
- **Resolution:**
  - Auth: optional `X-RAG-Token` header from `rag_auth_token` config field; empty string = no auth (default, backward-compatible)
  - Timeout: 10.0 seconds (connect + read) per HTTP attempt
  - Retry: up to 2 retries on 5xx or transport errors; no retry on 4xx client errors; exponential backoff (1s after first failure, 2s after second)
  - Fallback: `None` from `call_rag_service()` triggers in-process pipeline; empty string `""` is accepted as a valid (empty-result) response, no fallback
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Doc format | Visual review | OQ-1 status clear, no broken markdown |
| No regressions | `uv run pytest tests/ -x -q` | all pass (no code change) |
