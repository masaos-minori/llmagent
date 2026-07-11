# Implementation Procedure: tests — update `get_pending_approval` → `get_latest_approval` references

Source plan: `plans/20260711-173259_plan.md` — Design §1 / Implementation step 3

## Goal

Update all test-level imports, call sites, and (optionally) test function names that reference the old `get_pending_approval` symbol, so the test suite imports successfully after the rename in `approval_ops.py` (companion doc `20260711-214322_approval_ops_rename_get_latest_approval.md`).

## Scope

**In:**
- `tests/test_workflow_state_store.py`: update import/call sites.
- `tests/test_approval_ops.py`: update import/call sites; rename test function(s) whose name encodes the old symbol (e.g. `test_get_pending_approval_returns_latest` → `test_get_latest_approval_returns_latest`).
- `tests/test_workflow_engine.py`: update import/call sites where this test file references `get_pending_approval` directly (if any beyond exercising `_gate_approval()` indirectly).

**Out:**
- No new test cases in this item — this is a pure rename-propagation pass. New coverage (the orchestrator resume test) is a separate companion doc.
- No change to test *assertions* or fixtures — only the symbol name referenced.

## Assumptions

1. Confirmed via the plan's Assumption 2: `grep -rn "get_pending_approval"` finds exactly 8 test references across these three files (plus the 1 production call site handled in companion docs) — all plain imports/calls, no dynamic dispatch.
2. Renaming test function names that encode the old symbol name (e.g. `test_get_pending_approval_returns_latest`) is cosmetic, not required for correctness — per the plan's Design §1 ("though renaming test function names is cosmetic and not required for correctness"). Do it anyway for consistency, since it costs nothing and avoids a confusing test name referencing a function that no longer exists.
3. This item must land in the same change as `approval_ops.py`'s actual rename (companion doc) — these test files will fail to import (`ImportError`) if the rename lands without this update, or vice versa.

## Implementation

### Target file

`tests/test_workflow_state_store.py`, `tests/test_approval_ops.py`, `tests/test_workflow_engine.py`

### Procedure

1. Run `grep -rn "get_pending_approval" tests/test_workflow_state_store.py tests/test_approval_ops.py tests/test_workflow_engine.py` to enumerate every exact line to change.
2. In each matched line, replace `get_pending_approval` with `get_latest_approval` — covers both `from ... import get_pending_approval` statements and direct call expressions (`get_pending_approval(db, task_id)` → `get_latest_approval(db, task_id)`).
3. In `tests/test_approval_ops.py` specifically, locate any test function whose *name* contains `get_pending_approval` (e.g. `test_get_pending_approval_returns_latest`) and rename it to the equivalent with `get_latest_approval` (e.g. `test_get_latest_approval_returns_latest`). Do not change the test's body/assertions beyond the symbol reference already covered by step 2.
4. Re-run the grep from step 1 after edits to confirm zero remaining matches across these three files.

### Method

Mechanical find-and-replace of a single identifier across three known files, with one additional cosmetic function-rename pass in `test_approval_ops.py`. No new test logic.

### Details

- Do this as one atomic change together with `approval_ops.py`'s actual rename (companion doc `20260711-214322_...md`) and `workflow_engine.py`'s call-site update (companion doc `20260711-214340_...md`) — a partial rollout of only some of these three files/functions would break imports across the whole test suite.
- Double-check `tests/test_workflow_engine.py` for any *indirect* reference (e.g. a mock/patch target string like `"agent.workflow.approval_ops.get_pending_approval"`) — `grep` catches these as plain text matches, but confirm the replacement string is syntactically valid in that context (e.g. inside `monkeypatch.setattr(...)` calls).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to these files:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_workflow_state_store.py tests/test_approval_ops.py tests/test_workflow_engine.py` | 0 errors |
| Tests | `uv run pytest tests/test_workflow_state_store.py tests/test_approval_ops.py tests/test_workflow_engine.py -v` | All pass, no `ImportError`/`AttributeError` from the stale symbol name |
| Manual grep | `grep -rn "get_pending_approval" scripts/ tests/ docs/` | No matches remain anywhere (final confirmation after all companion docs implemented) |
