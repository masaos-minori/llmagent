# Implementation Procedure: repl_health.py — require `workflow_schema_version` table

Source plan: `plans/20260711-173032_plan.md` — Design §1 / Implementation step 1

## Goal

Close the gap where a missing `workflow_schema_version` table in `workflow.sqlite` raises a raw, unhandled `sqlite3.OperationalError: no such table: workflow_schema_version` instead of the same clean, remediation-bearing `RuntimeError` every other required workflow table already gets.

## Scope

**In:**
- `scripts/agent/repl_health.py`: add `"workflow_schema_version": ["version", "applied_at"]` to the module-level `REQUIRED_WORKFLOW_TABLES` dict.

**Out:**
- No change to the table/column-checking loop body in `check_workflow_schema()` — it already iterates `REQUIRED_WORKFLOW_TABLES.items()` generically.
- No change to the existing version-mismatch comparison logic (the `SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1` query and its `RuntimeError` on mismatch) — already implemented per `implementations/done/20260710-155445_repl_health_schema_version_check.md`; this item only ensures the table-existence check runs first.

## Assumptions

1. Confirmed via direct read of `scripts/agent/repl_health.py`: `REQUIRED_WORKFLOW_TABLES` (module level, just above `check_workflow_schema()`) currently lists only `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals` — `workflow_schema_version` is absent.
2. Confirmed via direct read: `check_workflow_schema()` already queries `workflow_schema_version` directly (via `WORKFLOW_SCHEMA_VERSION` comparison, added by a prior, already-implemented plan) with no prior existence check — so today, a workflow DB missing this table entirely raises a bare `sqlite3.OperationalError`, not `RuntimeError`.
3. Confirmed via `tests/test_repl_health.py::_create_workflow_db()`: the test helper unconditionally creates `workflow_schema_version` (its `exclude_table` parameter only applies to `tasks`/`attempts`/`processed_events`/`artifacts`/`approvals`) — no existing test exercises "table missing entirely," confirming this is genuinely new coverage, not a duplicate.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Locate the `REQUIRED_WORKFLOW_TABLES` dict definition (module level, immediately before `check_workflow_schema()`).
2. Add a new entry: `"workflow_schema_version": ["version", "applied_at"]`.
3. No other code change is required: the existing `for table, required_cols in REQUIRED_WORKFLOW_TABLES.items():` loop in `check_workflow_schema()` will now check `workflow_schema_version`'s existence and columns the same way as every other table, raising `RuntimeError(f"Workflow schema missing table {table!r}. Run create_workflow_schema() to initialize.")` if it is absent — this happens before the raw `SELECT version FROM workflow_schema_version ...` query later in the function, so that query becomes unreachable once the table is confirmed missing.

### Method

Single-entry additive dict change; no control-flow modification. The generic table/column loop already present in `check_workflow_schema()` is reused as-is.

### Details

- Ordering matters only implicitly: Python dicts preserve insertion order, and the loop iterates `REQUIRED_WORKFLOW_TABLES` before the later version-comparison block in the same function, so adding `workflow_schema_version` anywhere in the dict (order among keys does not affect correctness) guarantees the table-existence check always runs before the version query.
- Do not modify the version-mismatch error message wording (already correct/actionable per plan Design §1: "no change needed there, a negative finding").

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/repl_health.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/repl_health.py` | No new errors |
| Tests | `uv run pytest tests/test_repl_health.py tests/test_startup.py -v` | All pass, including new test for missing `workflow_schema_version` table (see companion test doc) |
| Regression | `uv run pytest tests/ -k "schema or workflow" -q` | No new failures |
