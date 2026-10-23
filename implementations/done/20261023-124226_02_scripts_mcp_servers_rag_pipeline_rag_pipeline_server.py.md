## Goal
Pass the module's already loaded configuration to `start()` and guarantee `stop()` runs on shutdown (`REQ-001`, `REQ-004`).

## Scope
- Edit `_lifespan` (lines 139-146) only.

## Assumptions
- `_cfg` is the module-level `RagPipelineConfig` that the security posture was built from (verified at the top of the module).
- The module is 13782 bytes, so the three-line change stays under the module-size gate.

## Design decisions
- Use `try: yield finally: await svc.stop()` so `stop()` runs even when the application raises while serving.

## Alternatives considered
- N/A: three-line change.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure
1. Change `await svc.start()` to `await svc.start(_cfg)`.
2. Replace the bare `yield` followed by `await svc.stop()` with `try: yield` and `finally: await svc.stop()`.

### Method
- Keep the `@asynccontextmanager` decorator and the `AsyncGenerator[None]` return annotation.

### Details
- Evidence: `rag_pipeline_server.py:139-146` (no `finally`; `start()` reloads config).
- Reference only: `tests/mcp_servers/lifespan_fixtures.py` for the existing lifespan test pattern.

## Compatibility considerations
- No external behavior change; shutdown now also runs after an exception during serving.

## Security considerations
- N/A: lifecycle change only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py` (tracked in its own document).
- `uv run pytest tests/mcp_servers/rag_pipeline`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers/rag_pipeline`, `uv run python tools/check_module_size.py`.

## Completion criteria
- The lifespan passes `_cfg`, and `stop()` runs once when the context exits normally or with an exception.

## Out of Scope
- Posture or authentication changes
- The service implementation (separate row)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the lifespan change per Implementation > Procedure | Completed | 20261023-131654 | 20261023-131654 | implemented; rag_pipeline tests 152 passed; full suite 9805 passed, 14 skipped |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py`, tracked in its own document) | Completed | 20261023-131654 | 20261023-131654 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-131654 | 20261023-131654 |  |

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
- **Requirement ID**: `REQ-001` (pass the module config), `REQ-004` (`try`/`finally` in the lifespan)
- **Source issue**: issues/20261023-114201_mcpstart006_rag-pipeline-server-lifespan-reloads-config-and-leaks-resources-on-failed-start.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-120118_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124226
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py