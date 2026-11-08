# Implementation procedure: `scripts/agent/workflow/tool_call_state_ops.py` — drop `snapshot_id` from the tool-call state ops layer

## Goal
Remove the dead `snapshot_id` field from `ToolCallState`, its row read in `_row_to_state`, and the parameter plus INSERT column/value in `record_tool_call`, so the ops layer never names the column in fresh or legacy databases (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: wfaudit010-full

- Dataclass field removal, row-mapping removal, INSERT statement rewrite (3 edits in one file).
- Companion test file `tests/agent/workflow/test_workflow_state_store.py`: delete the snapshot assertion, add the legacy-shape compatibility test.

## Assumptions
- `record_tool_call` keeps its positional signature shape for the four surviving arguments; the sole production caller `scripts/agent/tool_runner.py` (`recorder.record_tool_call(task_id, key, pc.name, retry_class(pc.name))`) never passes the dropped parameter, so it needs no edit (verified at HEAD `367e583d2`).

## Design decisions
- INSERT must not name `snapshot_id` (not merely pass `None`): a legacy database that still has the column accepts the row with the column omitted (NULL satisfies the FK), and a fresh database lacks the column entirely — one INSERT shape works for both (`REQ-003`).
- `SELECT *` statements stay: the row mapping (`_row_to_state`) is the place that names columns, and it drops the `snapshot_id` read there. A leftover legacy column in `SELECT *` output is simply unmapped.

## Alternatives considered
- Keep the dataclass field but always write NULL: rejected — Plan Design "Plumbing removal" requires deletion at every layer in one change so no half-removed API remains (sibling documents cover facade and protocol layers).

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`

### Procedure
1. Delete `snapshot_id: str | None` from the `ToolCallState` dataclass (L30) — 7 fields remain.
2. Delete the `snapshot_id=row["snapshot_id"],` line from `_row_to_state` (L43).
3. Delete the `snapshot_id: str | None = None,` parameter from `record_tool_call` (L55).
4. Rewrite the INSERT (L67-69): column list without `snapshot_id`, placeholders `?, ?, ?, 'pending', ?, ?, ?`, tuple `(idempotency_key, task_id, tool, retry_class, now, now)`.

### Method
- Deletions only; no logic changes. `finalize_tool_call`, `get_*`, and classify helpers stay untouched except through the shared `_row_to_state` mapping.

### Details
- Current state (verified at HEAD `367e583d2`): dataclass has 8 fields including `snapshot_id` (L30); `_row_to_state` (L35) reads `row["snapshot_id"]` (L43) — this read would `KeyError` against a fresh post-retirement database, so step 2 is mandatory together with step 1 (`REQ-003`).
- `pending1[0].snapshot_id is None` at `tests/agent/workflow/test_workflow_state_store.py:711` is the only snapshot-specific test assertion in the suite.

### Companion test files
- `tests/agent/workflow/test_workflow_state_store.py`
  - Procedure: delete the `snapshot_id is None` assertion (L711); add a legacy-shape fixture test that creates `tool_call_state` with the old DDL (including `snapshot_id TEXT REFERENCES execution_snapshots(snapshot_id)` and an `execution_snapshots` table), then runs record → finalize → read through the ops layer and asserts the lifecycle works with the column present but unnamed.
  - Validation: `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` — the legacy-shape test fails pre-change (INSERT names the absent-column fresh path, or read KeyError depending on fixture) and passes post-change.

## Compatibility considerations
- `ToolCallState` is a public dataclass of the workflow package: check `rg '\bToolCallState\b'` blast radius before landing (expect construction sites only in `tool_call_state_ops.py` and tests; the facade returns it unchanged otherwise).
- The facade and protocol layers drop their parameters in sibling documents `20261108-092904_03_scripts_agent_workflow_state_store.py.md` and `20261108-092904_04_scripts_agent_context.py.md` in the same batch — land the batch together so no layer keeps a dead pass-through.

## Security considerations
- N/A: field removal from an existing persistence helper; no new input surface.

## Rollback considerations
- Revert the commit restores the field/parameter; legacy databases are unaffected either way (Plan Design "Existing databases").

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | unit (companion file) | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` | legacy-shape test fails pre-fix, passes post-fix; L711 assertion removed |
| blast radius | static | `rg -l '\bToolCallState\b' tests/ scripts/` | confirm no other construction/read sites before landing |
| grep contract | static | `grep -rn "snapshot_id" scripts/agent/` after batch | empty (Acceptance Criteria REQ-002) |
| gates | static | `rules/toolchain.md` sequence (ruff → mypy → lint-imports → bandit) | clean, no new suppressions |

## Completion criteria
- Dataclass has 7 fields, none named `snapshot_id`; `grep -rn "snapshot_id" scripts/agent/` returns nothing (`Acceptance Criteria REQ-002`).
- Legacy-shape fixture test proves record/finalize/read work against a pre-retirement database (`Acceptance Criteria REQ-003`).
- `tests/agent/workflow/` green (`REQ-005`).

## Out of Scope
- Facade (`state_store.py`) and protocol (`context.py`) parameter removal — sibling documents in the same batch.
- DDL changes — sibling document `20261108-092904_01_scripts_db_schema_sql.py.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Blocks wfaudit003 and wfaudit002: land this plan's batch first |

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
- **Requirement ID**: `REQ-002` (no `snapshot_id` in the API), `REQ-003` (legacy-shape compatibility)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`, `tests/agent/workflow/test_workflow_state_store.py`
