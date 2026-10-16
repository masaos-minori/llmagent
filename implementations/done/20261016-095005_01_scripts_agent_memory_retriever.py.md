## Goal
- `REQ-001`: make `HybridRetriever.top_semantic()` return a pinned semantic memory even when its importance is below `min_importance`, so session-start injection matches `docs/23_agent/agent_11_01_memory-overview-and-modes.md`.

## Scope
- Change the one `WHERE` predicate of `top_semantic()` only. Tests are the other row's document (`tests/agent/memory/test_memory_retriever.py`).

## Assumptions
- Pinned entries are meant to bypass the importance threshold (Plan Assumptions); an unpinned entry below the threshold stays excluded.
- `top_semantic()` has one production caller, `MemoryInjectionService.on_session_start()` in `scripts/agent/memory/injection.py`.

## Design decisions
- Replace `importance >= ?` with `(importance >= ? OR pinned = 1)`; the bind parameters, signature, return type, `memory_type = 'semantic'`, branch filter, `ORDER BY pinned DESC, importance DESC, created_at DESC`, and `LIMIT` stay unchanged.
- Parenthesize the OR so the following `AND (? = '' OR branch = '' OR branch = ?)` still applies to pinned rows.

## Alternatives considered
N/A: a separate UNION query for pinned rows was rejected as larger than the single predicate that the docs require.

## Implementation
### Target file
`scripts/agent/memory/retriever.py`

### Procedure
- In `HybridRetriever.top_semantic()`, edit the `WHERE` line (line 280 at plan time): `WHERE memory_type = 'semantic' AND (importance >= ? OR pinned = 1)`.
- Update the docstring first line to say that pinned entries bypass `min_importance`.

### Method
- Keep the query a single parameterized string; do not add a bind parameter.

### Details
- Cycles run in filename order, so this edit lands first; the red check required by the Plan's Phase 1 is done in the next document's cycle by temporarily restoring the old predicate (corrected at execution time).
- `SQLiteHelper("session")` usage and `row_to_entry` mapping are untouched.

## Compatibility considerations
- Behavior change confined to rows that are pinned and below `min_importance`; they now qualify. `top_semantic` is referenced in 3 test files (31 references); `test_memory_layer.py` mocks it and `test_regression_memory_branch.py` uses unpinned rows, so they are unaffected.

## Security considerations
N/A: the SQL stays fully parameterized and gains no interpolated input.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_retriever.py tests/agent/memory/test_memory_layer.py tests/agent/memory/test_regression_memory_branch.py -v`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/agent/memory/retriever.py -c pyproject.toml`
- `uv run python tools/generate_reference_table.py --check` (expect no drift)

## Completion criteria
- The predicate is `(importance >= ? OR pinned = 1)` and the new pinned-below-threshold tests pass.
- Existing `top_semantic` tests and the three modules above pass; lint, type, architecture, and security checks report no new findings.
- Deployment per `skills/deploy/SKILL.md` is a Plan step after validation, not part of this file's edit.

## Out of scope
- Pinned episodic memories (UNK-01), the `max_semantic` versus `memory_max_pinned` cap (UNK-02), scoring changes, and any `docs/*.md` edit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the `top_semantic()` predicate and docstring | Completed | 20261016-095311 | 20261016-095323 | Lands before row 02; red check done in row 02's cycle changed: scripts/agent/memory/retriever.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-095323 | 20261016-101133 | ruff/mypy/lint-imports/bandit clean; memory tests 103 passed; full suite 57 failed (session undo tests, identical 57 with change stashed = pre-existing); docs: N/A no change (agent_11_01 already states behavior) |

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
- **Requirement ID**: REQ-001 (pinned bypasses the importance threshold)
- **Source issue**: issues/20261016-092648_mem002_add-pinned-memory-session-start-injection-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-093429_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-095005
- **Related target files**: scripts/agent/memory/retriever.py