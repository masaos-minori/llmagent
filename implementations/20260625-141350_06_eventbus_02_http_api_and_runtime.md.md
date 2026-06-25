# Implementation: Add offload model notes to HTTP API and runtime doc

Source plan: `plans/20260625-140631_plan.md` (req #21, HTTP API doc portion)

## Goal

Add brief offload model notes to the DLQ background loop section and `/subscribe` section in `docs/06_eventbus_02_http_api_and_runtime.md` so the doc accurately reflects that DB and file I/O operations are offloaded via `asyncio.to_thread()`.

## Scope

- Append one sentence to the `## DLQ background loop` section noting `asyncio.to_thread` offload
- Append one sentence to the `### GET /subscribe` section noting that DB poll queries are offloaded
- No changes to endpoint contracts, request/response schemas, or failure behavior table

## Assumptions

1. req #14 (asyncio.to_thread wrapping) and req #18 (file I/O offload) are implemented
2. The changes are additive — existing sentences are not modified

## Implementation

### Target file

`docs/06_eventbus_02_http_api_and_runtime.md`

### Procedure

1. Locate `## DLQ background loop` section (currently at line 87)
2. Append offload note after the existing paragraph
3. Locate `### GET /subscribe` section
4. Append offload note after the existing paragraph about polling

### Method

Additive edit only — append sentences. Do not modify existing sentences.

### Details

**DLQ background loop section — append after existing paragraph:**
```markdown
DB operations (`promote_to_dlq`) and DLQ file writes (`_atomic_write`) are executed via `asyncio.to_thread()` and do not block the event loop.
```

**GET /subscribe section — append after the paragraph ending "...`consumer_id` is set and `since_seq == 0`":**
```markdown
Each poll query and offset file write is executed via `asyncio.to_thread()` to avoid blocking the event loop during streaming delivery.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Offload note in DLQ section | `grep "asyncio.to_thread" docs/06_eventbus_02_http_api_and_runtime.md` | ≥ 2 matches |
| No existing content removed | `diff` with original | Only new lines added |
| Markdown lint | `markdownlint docs/06_eventbus_02_http_api_and_runtime.md` | 0 errors (if installed) |
