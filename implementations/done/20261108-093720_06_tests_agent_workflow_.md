# Implementation procedure: `tests/agent/workflow/` — status vocabulary tests (rejections, consistency)

## Goal
Add the test surface that pins the vocabulary contract: per-helper rejection cases and the writer-consistency test (`REQ-002`, `REQ-004`, `REQ-005`).

## Scope
**Release unit**: wfaudit005-full

- New file `tests/agent/workflow/test_workflow_status_vocabulary.py` (new): vocabulary-consistency test and per-helper rejection cases for `update_task_status`, `finish_attempt`, `finalize_tool_call`.
- `tests/agent/workflow/test_workflow_state_store.py`: extend existing lifecycle tests with one `ValueError` rejection assertion each (row-unchanged check).
- The DDL-vs-constants equality test is owned by the sibling document `20261108-093720_05_scripts_db_schema_sql.py.md` (companion `tests/db/test_create_schema.py`) and is NOT written here.

## Assumptions
- The plan's target row is the directory `tests/agent/workflow/`; this document maps that row to the concrete files above (its "self" row in the plan table).
- New tests must fail on the pre-change HEAD `11c20696a` (silent acceptance) and pass after Phase 1 (`REQ-005`, Plan Validation plan).

## Design decisions
- Rejection cases live in both places: a fresh dedicated file (`test_workflow_status_vocabulary.py`) holds the vocabulary-focused suite (consistency + rejections with row-unchanged asserts); `test_workflow_state_store.py` gets the minimal "raises and writes nothing" assertions inside its existing lifecycle fixtures so regression coverage sits next to the lifecycle it protects (Plan Tests section: "Per-helper rejection tests (`ValueError`, no write)").
- Consistency test approach: a static assertion list of known writer call sites (engine L213-224 statuses, adapter `_status_for_exit` returns `halted`, `state_store.py` recovery UPDATE `failed` L224-225, `idempotency_ops.py` INSERT `running`, `tool_runner.py` L104/L108 `failed`/`completed` via the recorder facade — re-verified at HEAD `11c20696a`) compared against the frozensets — a code-side list, not a runtime grep (Plan `REQ-004`: "greps-walk of writer call sites, or a static assertion list").

## Alternatives considered
- Runtime grep-walk of `scripts/` inside the test: rejected — brittle against formatting changes; the static list fails loudly and names the drifted site.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_status_vocabulary.py` (new)

### Procedure
1. Create the new file (new) with: a rejection test per helper (`"done"` → `pytest.raises(ValueError)` and `row unchanged` assert on a fresh fixture database); a consistency test asserting the known writer literal list ⊆ the `models.py` frozensets; a guard test asserting the three frozensets' exact membership per `REQ-001`.
2. In `tests/agent/workflow/test_workflow_state_store.py`, extend one existing lifecycle test per helper with the rejection assertion (task: `update_task_status(..., "done")`; attempt: `finish_attempt(..., "done")`; tool-call: `finalize_tool_call(..., "done")`).

### Method
- Fixture databases created with `create_workflow_schema()`; row-unchanged asserted via `SELECT status`/`SELECT state` before/after the rejected call.
- Import vocabulary constants from `agent.workflow.models` in the new file.

### Details
- Current state (re-verified at HEAD `11c20696a`): `tests/agent/workflow/` still holds eight test files, all asserting happy paths only for these helpers (Plan target-row evidence); no `test_workflow_status_vocabulary.py` exists yet.
- `tests/agent/workflow/` also contains `test_workflow_models.py` and `test_state_store.py` — untouched by this row; facade-level rejection behavior is the same helpers' guards.

## Compatibility considerations
- No source-code change in this document; test-only row.
- Row mapping: the plan's frozen row names the directory `tests/agent/workflow/`; the concrete files edited are those listed in Scope (document-to-row correspondence recorded here per the plan-table mapping).

## Security considerations
- N/A: tests only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/workflow/test_workflow_status_vocabulary.py` | new-file tests | `uv run pytest tests/agent/workflow/test_workflow_status_vocabulary.py -q` | fails pre-Phase-1 (no rejection raised), passes after Phase 1 (`REQ-005`) |
| `tests/agent/workflow/test_workflow_state_store.py` | extended lifecycle | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` | same fail-pre/pass-post for the added assertions |
| whole dir regression | existing suite | `uv run pytest tests/agent/workflow/ -q` | green |

## Completion criteria
- All three helpers reject out-of-vocabulary statuses with no write, and the consistency test passes (`Acceptance Criteria REQ-002`, `REQ-004`); new tests fail on HEAD and pass after Phase 1 (`REQ-005`).

## Out of Scope
- DDL-vs-constants equality test (sibling seq 05 companion).
- Source-side changes (sibling docs 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the new vocabulary test file per Procedure | Completed | 20261108-130538 | 20261108-130538 | Blocks wfaudit001 and wfaudit007: land this plan's batch first memo3 adversarial verification pass at HEAD 11c20696a: stale check clean; 8 test files confirmed, new file absent; tool_runner completed/failed added to consistency list; fail-on-HEAD baseline = 11c20696a test_workflow_status_vocabulary.py created: membership + consistency + 3 rejection tests |
| 2 | Extend test_workflow_state_store.py lifecycle tests with rejection assertions | Completed | 20261108-130538 | 20261108-130538 | rejection assertions added to test_update_status, test_finish_attempt_completed, test_finalize_moves_state_and_bumps_updated_at |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-130538 | 20261108-130538 | ruff+format pass; tests/agent/workflow 164 passed; fail-on-HEAD proven via stash of 3 guard files: 3 rejection tests FAILED pre-change then restored (REQ-005); stale_detector clean pre-implementation, only expected new_target_exists after file creation |

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
- **Requirement ID**: `REQ-002` (rejection coverage), `REQ-004` (writer-consistency test), `REQ-005` (fail-on-HEAD proof)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `tests/agent/workflow/test_workflow_status_vocabulary.py`, `tests/agent/workflow/test_workflow_state_store.py`