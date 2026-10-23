## Goal
Prove failed-start cleanup, no config reload with an injected config, safe repeated and post-failure `stop()`, and `stop()` on shutdown (`REQ-005`).

## Scope
- New test module only; existing service tests stay unchanged.

## Assumptions
- `RagPipeline` is imported lazily inside `start()` from `rag.pipeline`, so patching `rag.pipeline.RagPipeline` controls the failure.
- The probe that reproduced the leak patched `rag.pipeline.RagPipeline` with a function raising a test exception and read `svc._http.is_closed`.

## Design decisions
- Build `RagPipelineConfig` through the same constructor arguments the existing `TestServiceStart` uses; use `unittest.mock.patch` on `RagPipelineConfig.load` with a counting stub.

## Alternatives considered
- Drive the whole FastAPI app: rejected, the service and `_lifespan` can be tested directly.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py` (new)

### Procedure
1. Failed-start test: patch `rag.pipeline.RagPipeline` to raise; assert the exception propagates and the client captured during `start()` is closed (`is_closed`) and `svc._http is None`.
2. Injected-config test: call `start(cfg)` with `RagPipelineConfig.load` patched to fail the test if called; assert the pipeline and client are set.
3. `stop()` tests: twice in a row; after a failed start; on a `__new__` instance with only `_http` set to an `AsyncMock`.
4. Lifespan test: use `rag_pipeline_server._lifespan` with a patched `_service` double; raise inside the `async with` and assert `stop()` was awaited once and `start()` received `_cfg`.

### Method
- Use `pytest.mark.asyncio` as the sibling service tests do.

### Details
- Reference only: `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` `TestServiceStart`, `tests/mcp_servers/lifespan_fixtures.py`.

## Compatibility considerations
- Test-only.

## Security considerations
- No secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py`, `uv run pytest tests/mcp_servers/rag_pipeline`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All cases pass on the implemented change; the failed-start and injected-config cases fail on the pre-change code.

## Out of Scope
- Changes to existing test modules

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (lifecycle tests), covering `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: issues/20261023-114201_mcpstart006_rag-pipeline-server-lifespan-reloads-config-and-leaks-resources-on-failed-start.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-120118_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124226
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py
