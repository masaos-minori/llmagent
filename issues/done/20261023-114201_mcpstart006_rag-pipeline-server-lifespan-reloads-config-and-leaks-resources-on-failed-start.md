# RAG pipeline server lifespan reloads config and leaks resources on failed start

## Priority
Low

## Summary
The rag-pipeline-mcp lifespan starts its service by loading the configuration a second time, so the security posture computed at import and the runtime pipeline can be built from different configuration reads. A failure in the middle of `start()` leaves the HTTP client open, and the lifespan has no `try`/`finally`, so `stop()` is not guaranteed to run. Review severity: Low after verification (the failed-start leak is short-lived because the process exits, and the config re-read is a narrow drift window).

## Background
`rag_pipeline_server.py` loads `_cfg` and builds `_security_posture` at import time. Its `_lifespan` calls `RagPipelineMCPService.start()` (`rag_pipeline_service.py`), which calls `RagPipelineConfig.load()` again, creates an `httpx.AsyncClient`, then builds `RagPipeline` and `DocumentManager`. `stop()` closes only the HTTP client. The lifespan is the only place the service is initialized, and requests are served only after it completes.

## Problem
Confirmed by a probe (evidence label: Confirmed by execution, confidence High). With `RagPipeline` replaced by a function that raises, running the lifespan raised the error, performed one extra `RagPipelineConfig.load()` inside `start()`, and left the `httpx.AsyncClient` open (`is_closed` false). Consequences:

- Configuration drift window: the posture and `_cfg` used for tool availability come from the import-time read, while the pipeline uses a later read; an edit between the two (or a changed environment variable) makes the reported posture describe a configuration the pipeline does not use.
- Resource handling: a failure after the client is created is not cleaned up. The process normally exits afterwards, so the practical impact is small, but the lifecycle contract ("start once, stop once") is not enforced.
- `stop()` does not release `DocumentManager` or the pipeline, and does not reset the stored client, so a second `start()` in the same process (for example in tests or a future reload) would overwrite a still-open client.

Verification (issue-to-plan Step 2, 2026-10-23, adversarial): confirmed with corrections. (1) The probe reproduced both claims (one extra `RagPipelineConfig.load()` inside `start()`, client left open after a failed start), but a failed lifespan makes uvicorn exit the process, so the leak is short-lived; the severity is lowered accordingly. (2) Existing tests call `svc.start()` with no argument and monkeypatch `RagPipelineConfig.load` (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, `TestServiceStart`), and another test builds the service with `__new__` and sets only `_http` before calling `stop()`. A fix must therefore keep `start()` callable without arguments (an optional configuration parameter that defaults to a fresh load) and keep `stop()` tolerant of missing attributes. (3) `DocumentManager()` is constructed in `__init__` without a path and only receives `rag_db_path` inside `start()`; that is intended and unchanged. (4) Only two source files and one test module are involved, so this is a small change.

## Reason for Change
Startup behavior must be deterministic and its failure paths clean. The posture is used by the Agent to decide whether the server is trustworthy, so it must describe the configuration that is actually running.

## Implementation Intent
Build the pipeline from the same configuration object that produced the posture, and make `start()` all-or-nothing with guaranteed cleanup. Keep the lifespan structure but add explicit failure handling.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (`start`, `stop`)
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (`_lifespan`)
- `tests/mcp_servers/rag_pipeline/`

## Required Changes
- Pass the already loaded configuration into `start()` instead of reloading it.
- Close the HTTP client and any partially built resources when `start()` fails.
- Wrap the lifespan `yield` in `try`/`finally` so `stop()` runs once on shutdown, and make `stop()` safe to call more than once.
- Release every resource `start()` acquires in `stop()`.

## Constraints
- Keep lazy import of `rag.pipeline` (it avoids a circular import).
- Do not change the pipeline's runtime behavior or configuration keys.
- `start()` and `stop()` must stay idempotent-safe for tests that call them directly.

## Acceptance Criteria
- A failed `start()` leaves no open `httpx.AsyncClient`.
- `start()` does not call `RagPipelineConfig.load()` again.
- `stop()` after a failed or repeated start does not raise.
- Existing rag-pipeline tests pass.

## Testing Expectations
- Unit test: `RagPipeline` raising during `start()` leaves the client closed and propagates the error.
- Unit test: `start()` uses the injected configuration and performs no additional load.
- Unit test: `stop()` is safe after failure and when called twice.
- Run `ruff`, `mypy`, `bandit`, and `pytest tests/mcp_servers/rag_pipeline`.

## Documentation Impact
Not required beyond a code comment on the lifecycle contract; no documented behavior changes.

## Out of Scope
- The RAG pipeline logic and the embedding or refiner settings.
- Authentication and posture gate changes (`mcpstart002`, `mcpstart003`).

## Dependencies
- Related: `mcpstart004` also changes where configuration is loaded for each server; coordinate if both are in flight.
- No open issue under `issues/` covers these files.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Limit changes to the service lifecycle and its tests. Do not alter pipeline construction arguments. Stop and report if an existing test depends on `start()` loading its own configuration.

## Traceability
- **Workflow phase**: python-code-review (adversarial review of MCP server startup), converted by issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-114201
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
