## Goal
Let `start()` use a supplied configuration, close the HTTP client when startup fails, and make `stop()` safe to call repeatedly (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
- Change `start()` (line 95) and `stop()` (line 113) of `RagPipelineMCPService` only.
- No change to the pipeline, document manager or dispatch code.

## Assumptions
- `TestServiceStart` in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` calls `svc.start()` with no argument and patches `RagPipelineConfig.load`, so the parameter must be optional and default to a fresh load.
- `test_stop_closes_http_client` builds the service with `__new__`, sets only `_http` and `_pipeline`, and calls `stop()`; `stop()` must not read other attributes.
- The module is 10472 bytes, so the change stays under the 16384-byte module-size gate.

## Design decisions
- `start(self, cfg: RagPipelineConfig | None = None)` uses `cfg if cfg is not None else RagPipelineConfig.load()`.
- Cleanup uses `try`/`except BaseException` that closes the client, clears the reference and re-raises, so cancellation is never swallowed.

## Alternatives considered
- Pass the config to the constructor: rejected, the service is created at import time and tests construct it without a config.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`

### Procedure
1. Change the signature to `async def start(self, cfg: RagPipelineConfig | None = None) -> None` and replace `cfg = RagPipelineConfig.load()` with the optional-argument logic.
2. Wrap the statements after `self._http = httpx.AsyncClient(...)` (building `RagPipeline` and `DocumentManager`) in `try`/`except BaseException`: on failure `await self._http.aclose()`, set `self._http = None`, `self._pipeline = None`, then `raise`.
3. Rewrite `stop()` to read `http = getattr(self, "_http", None)`, set `self._http = None` and `self._pipeline = None` first, then `await http.aclose()` when `http` is not `None`, so a second call is a no-op and a `__new__`-built instance works.

### Method
- Keep the lazy `from rag.pipeline import RagPipeline` at the top of `start()` (it avoids a circular import).
- Keep the `logger.info("RagPipelineMCPService started")` and stopped messages.

### Details
- Evidence: probe with `RagPipeline` raising showed one extra `RagPipelineConfig.load()` and an open client; `rag_pipeline_service.py` `start` at line 95 and `stop` at line 113.
- Reference only: `rag_pipeline_models.py` (`RagPipelineConfig`), `document_manager.py`.

## Compatibility considerations
- `start()` stays callable with no argument; behavior with no argument is unchanged except for the failure cleanup.

## Security considerations
- N/A: no trust-boundary change; cleanup avoids leaving a connection pool open after a failed start.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py` (tracked in its own document) and the existing `test_rag_pipeline_mcp_service.py`.
- `uv run pytest tests/mcp_servers/rag_pipeline`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/rag_pipeline`, `uv run python tools/check_module_size.py`.

## Completion criteria
- A failed `start()` leaves no open client and re-raises; `start(cfg)` does not call `RagPipelineConfig.load()`; `stop()` is safe twice and on a `__new__` instance; existing tests pass.

## Out of Scope
- Closing `RagPipeline` or `DocumentManager` resources (plan UNK-01)
- Pipeline logic

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the `start()` and `stop()` changes per Implementation > Procedure/Method/Details | Completed | 20261023-131652 | 20261023-131652 | implemented; rag_pipeline tests 152 passed; full suite 9805 passed, 14 skipped |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py`, tracked in its own document) | Completed | 20261023-131652 | 20261023-131652 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-131652 | 20261023-131652 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (optional injected config), `REQ-002` (failure cleanup), `REQ-003` (idempotent `stop()`)
- **Source issue**: issues/20261023-114201_mcpstart006_rag-pipeline-server-lifespan-reloads-config-and-leaks-resources-on-failed-start.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-120118_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124226
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py