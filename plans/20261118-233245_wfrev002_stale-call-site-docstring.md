## Goal
- Correct the docstring of `pending_tool_calls` (`scripts/agent/workflow/tool_call_state_ops.py`) so it stops asserting that the turn-entry detection path calls it, and instead describes the function's actual behavior and its test-only usage.

## Priority
Low

## Scope
- **In-Scope**: Rewrite only the `pending_tool_calls` docstring in `scripts/agent/workflow/tool_call_state_ops.py`.
- **Out-of-Scope**: Removing or wiring `pending_tool_calls` into production; changing the function body, signature, return contract, or imports; touching `classify_stale_pending`, `workflow_engine.py`, or any other function; any test change.
- **Dependencies**: Context (not blocking): `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` established that `pending_tool_calls` is test-only; this issue only corrects the docstring that wfaudit009 left in place. If wfaudit009's follow-up later removes the function, this issue becomes moot.
  - **Depends on**: N/A: none

## Background
`tool_call_state_ops.pending_tool_calls` documents itself as "The only method the turn-entry detection path (workflow_engine) calls; kept cheap via the ``idx_tool_call_state_task_state`` index." That description is false on two counts. The turn-entry detection path in `scripts/agent/workflow/workflow_engine.py:180` calls `self._store.classify_stale_pending(task_id, timeout_seconds)`, not `pending_tool_calls`. And a repository-wide grep finds zero callers of `pending_tool_calls` inside `scripts/`; it is invoked only from tests (`tests/agent/workflow/test_workflow_state_store.py` and `tests/agent/workflow/test_workflow_engine.py:782`). `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` already established that `pending_tool_calls` is test-only, but scoped the fix to removing or wiring the helper, not to correcting the ops-level docstring that still names a nonexistent production caller.

## Problem
The docstring points future readers and agents at a call edge that does not exist. Anyone tracing "who detects stale pending tool calls" from this docstring will land on `pending_tool_calls`, which is never called in production, instead of the real entry point `classify_stale_pending`. The mismatch is purely documentary; no behavior depends on it.

## Reason for Change
Doc/code mismatches compound: the next person who removes this test-only helper (a natural follow-up to wfaudit009) inherits a docstring that blames a wrong caller, and any agent following the docstring wastes time on a dead path. It is a small, self-contained correction with no behavioral risk.

## Implementation Intent
Rewrite the `pending_tool_calls` docstring to describe reality: it returns a task's pending tool-call rows oldest-first and is exercised by tests, while the turn-entry stale-detection path uses `classify_stale_pending`. Reference the real caller (`classify_stale_pending`) only to correct the record, not to imply `pending_tool_calls` is production-used. Do not rename the function, change its signature, or wire it into production here — those belong to a separate test-only-helper cleanup if the owner chooses it. Keep the existing `idx_tool_call_state_task_state` index reference, which is accurate (the index exists on `tool_call_state(task_id, state)` per `scripts/db/schema_sql.py:225`).

## Requirements
- `REQ-001`: Rewrite the `pending_tool_calls` docstring so it no longer claims the turn-entry detection path (or the engine) calls it; state accurately that it returns pending rows oldest-first and is used by tests; optionally cross-reference `classify_stale_pending` as the actual stale-detection entry point.

## Implementation Target Files
**Freeze status**: Frozen (set from `Draft` after `issue-to-plan` Step 8's
Implementation Target Files Validation passed — `audit_plan_target_paths.py` reports
0 findings; the row is `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify — rewrite the `pending_tool_calls` docstring only (L90-95); leave the function body, signature, and the `idx_tool_call_state_task_state` index reference unchanged | REQ-001; AC-2 | The current docstring (L91-94) asserts the turn-entry detection path calls `pending_tool_calls`; `rg pending_tool_calls scripts/` shows zero production callers; real entry point is `classify_stale_pending` at `workflow_engine.py:180` (checked in Step 2/3) | `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py:782` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Confirm `classify_stale_pending` (L180) is the real turn-entry stale-detection entry point, so the corrected docstring cross-reference is accurate. | REQ-001 |
| `scripts/db/schema_sql.py` | Confirm `idx_tool_call_state_task_state` exists on `tool_call_state(task_id, state)` (L225-226), so the preserved index reference stays accurate. | REQ-001 |
| `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py` | Confirm the test-only call sites that exercise `pending_tool_calls` (unchanged by this Plan). | REQ-001 |

## Acceptance Criteria
- **AC-1 (REQ-001)**: A grep for `pending_tool_calls` in `scripts/` still shows zero production callers.
- **AC-2 (REQ-001)**: The docstring no longer states that the turn-entry detection path (or the engine) calls `pending_tool_calls`.
- **AC-3 (REQ-001)**: No test fails; the function remains importable and tested; the `idx_tool_call_state_task_state` index reference stays accurate.

## Tests
Not required by the issue (docstring-only, no behavior impact). As a safety net, the implementation phase runs the existing `tests/agent/workflow/test_workflow_state_store.py` to confirm the function is still importable and tested after the edit (AC-3); ruff/mypy clean on the touched file is sufficient.

## Documentation Impact
This is the documentation change: correct one code docstring so it matches the code. No operator-facing docs are affected.

## Assumptions
- The edit is confined to the docstring triple-quoted string at L91-94; no code, import, or signature line changes.
- The `idx_tool_call_state_task_state` index reference is accurate and should be preserved (confirmed against `schema_sql.py:225`).
- The function's test-only status holds across `test_workflow_state_store.py` and `test_workflow_engine.py` (verified in Step 2/3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to also align the docstring's index reference with the real index name. Verification found `idx_tool_call_state_task_state` IS the actual index name (`schema_sql.py:225`), so no correction is needed; this row records that the issue's implicit assumption held. | None — resolved by repository evidence in Step 2/3. | N/A: no action required. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

Blast Radius is judged qualitatively (Path A): the change is a docstring edit with no behavioral or caller impact. `Churn (30d)` and `Bus Factor` are `N/A` because Path A skips the historical analysis.

## Design
Classification: **Path A** (see `skills/issue-to-plan/SKILL.md` Routing). Modification scope is a single file, a docstring-only edit with no behavior, caller, signature, or schema change. Step 2/3 verified: `pending_tool_calls` has zero callers in `scripts/` (radon A(2); vulture/bandit clean), is invoked only from tests, and the real stale-detection entry point is `classify_stale_pending` at `workflow_engine.py:180`. The referenced index `idx_tool_call_state_task_state` exists (`schema_sql.py:225`), so the preserved reference is accurate.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Rewrite the `pending_tool_calls` docstring** (`scripts/agent/workflow/tool_call_state_ops.py`, REQ-001)
   - [ ] Replace the L91-94 docstring so it no longer claims the turn-entry detection path (or the engine) calls `pending_tool_calls`.
   - [ ] Describe accurately: returns the task's pending tool-call rows oldest-first; exercised by tests; the turn-entry stale-detection entry point is `classify_stale_pending` (`workflow_engine.py:180`).
   - [ ] Preserve the `idx_tool_call_state_task_state` index reference (accurate) and leave the function body, signature, and imports unchanged.

### Release units
N/A: no release unit — the single docstring edit validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Static: format, lint, types | `uv run ruff format --check scripts/agent/workflow/tool_call_state_ops.py`; `uv run ruff check scripts/agent/workflow/tool_call_state_ops.py`; `uv run mypy --no-namespace-packages scripts/` | ruff/mypy clean |
| `tests/agent/workflow/test_workflow_state_store.py` | Unit: function still importable and tested after the edit | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` | Passes; `pending_tool_calls` still callable |

## Risks
- **Risk**: Accidentally changing the function body, signature, or an import while editing the docstring. → **Mitigation**: confine the edit to the L91-94 docstring triple-quoted string; ruff/mypy clean; existing tests still pass (AC-3).
- **Risk**: Introducing a second documentary inaccuracy while rewriting. → **Mitigation**: verify the preserved `idx_tool_call_state_task_state` reference against `schema_sql.py:225` before finalizing (already confirmed in Step 2/3).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Rewrite the `pending_tool_calls` docstring (`scripts/agent/workflow/tool_call_state_ops.py`, REQ-001) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-221536_wfrev002_stale-call-site-docstring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-233245
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullets 1-3; Implementation Intent | `scripts/agent/workflow/tool_call_state_ops.py` | Step 1 | AC-1, AC-2, AC-3 | T (test_workflow_state_store.py) | Confirmed by repository evidence |
