## Goal
Stop four tests from reaching the real `write_ops.upsert` by patching `agent.memory.ingestion.write_upsert`, so their correctness no longer depends on the global redirect (`REQ-005`).

## Scope
- The four tests that were observed to write one `memories` row each: `test_no_entry_when_embed_fails`, `test_increment_on_embed_failure_in_persist_entry_with_dedup`, `test_increment_on_embed_failure_in_persist_entry`, and `test_summary_log_contains_count`.
- `test_on_session_stop_delegates` is not changed: it drives a `MemoryServices` facade whose ingestion is a mock and never reaches the writer (verified while generating this procedure).

## Assumptions
- `write_upsert` is bound in `agent.memory.ingestion` (`from agent.memory.write_ops import upsert as write_upsert`), which is where the patched neighbors patch it.
- `patch` is already imported in this module.

## Design decisions
- Wrap only the awaited `on_session_stop` or `write_semantic` call in `with patch("agent.memory.ingestion.write_upsert"):`; keep each test's assertions as they are.
- Where a test asserts that the writer was or was not called, keep that assertion, using the patched object.

## Alternatives considered
Relying on the global redirect alone was rejected: a test should not need a production-shaped path to be safe.

## Implementation
### Target file
`tests/agent/memory/test_memory_layer.py`

### Procedure
1. Patch `write_upsert` around the `on_session_stop` call in `test_no_entry_when_embed_fails`.
2. Do the same around `on_session_stop` in `test_increment_on_embed_failure_in_persist_entry_with_dedup` and `test_summary_log_contains_count`.
3. Patch around `write_semantic` in `test_increment_on_embed_failure_in_persist_entry`.
4. Run the file.

### Method
- Use the neighboring tests' form: `with patch("agent.memory.ingestion.write_upsert") as mock_write:` and keep the awaited call inside the block.
- Do not change test names or the shared helper `_make_ingestion_svc`.

### Details
- These tests only check counters and logs; with the patch they must still pass unchanged.
- Use only the new, production-safe test files until the conftest isolation exists; do not run the full suite (it writes to `/opt/llm`).

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only; removes a write path to a database.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_layer.py -q` (after the conftest isolation exists)
- `uv run ruff format tests/agent/memory/test_memory_layer.py && uv run ruff check tests/agent/memory/test_memory_layer.py`
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The four tests pass and no longer call the real `write_ops.upsert`.

## Out of scope
- `test_on_session_stop_delegates` and other tests
- Any production data cleanup

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wrap the four calls with the patch | Pending | — | — | |
| 2 | Run the file and the validation sequence (`rules/toolchain.md`) for it | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (patch the four unpatched tests)
- **Source issue**: issues/20261019-131051_testiso001_tests-write-to-production-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-131444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-132033
- **Related target files**: tests/agent/memory/test_memory_layer.py
