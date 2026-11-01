## Goal

Update the section 7 task-key paragraph in `docs/41_db/db_02_architecture_and_schema-schema-reference.md` to the `task_nonce` (new) name and contract (Plan REQ-005, AC-6).

## Scope

- The section 7 paragraph (currently `db_02...md:48`) "Each `tasks` row carries an `idempotency_key` ..." is rewritten to name the column `task_nonce` (new) and state the three-way distinction: task identity (`task_id`), task-request deduplication (absent: duplicate task creation is allowed, each call produces a new row), and stage-event idempotency (`processed_events.event_id`, section 7 text elsewhere).
- No other section of the file changes; `tool_call_state.idempotency_key` (a tool-call table column) keeps its name and description.

## Assumptions

- Plan overlap judgment (re-recorded): the shared-doc row is compatible with toolexec001 (already landed; the `tool_call_state` bullet at `:48`'s neighboring version paragraph and section 7 tool-call text stay untouched); `docs/41_db/db_02_...md` is not a row of any other open Plan except via the same-key rename wording.
- Line cites are from HEAD `456fb7ca2` (re-verified 2026-11-01).

## Design decisions

- Documentation states the contract, not code (Plan REQ-005 "without restating code"): describe `task_nonce` (new) as a globally unique opaque UUID4 generated per `create_task()` call, never caller-derived, with the UNIQUE constraint as a backstop only.

## Alternatives considered

- Keeping the old name in docs until a later cleanup: rejected by AC-6 — docs must match the renamed contract in the same landing wave as rows 01-04 and 12.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. In the section 7 key paragraph (`:48`), replace `idempotency_key` references for the tasks table with `task_nonce` (new) and keep the uniqueness/backstop wording.
2. Add one sentence making the three-way distinction explicit: `task_id` is task identity; a second `create_task` call with identical arguments is a new task (no request-level dedup); stage re-execution is prevented by the event key in `processed_events`, not by the task nonce.
3. Leave the `tool_call_state.idempotency_key` wording in this file unchanged.

### Method
Single-paragraph rewrite plus one added sentence; no headings added or removed.

### Details
- The paragraph currently ends "a new session against a retained file always receives fresh, unique keys." — retain that sentence, rephrased with the new name if needed.
- If the version paragraph at `:46` or the tasks-table listing elsewhere names the column, rename those mentions in the same edit.

## Compatibility considerations

- `docs/00_index.md` task-scope mapping already lists this file for this Plan (Plan Documentation impact: Yes).
- `tools/check_docs_structure.py` and the docs size ceiling must pass after the edit (AGENTS.md rule 9).

## Security considerations

- N/A: prose-only change.

## Rollback considerations

- Revert is a text revert of the paragraph; must be reverted together with rows 01-04/12 so docs never describe a column name absent from the DDL.

## Validation plan

- `uv run python tools/check_docs_structure.py` — no findings.
- `uv run python tools/generate_reference_table.py --check` — no drift (this file is not the generated reference doc; confirm the mention audit stays clean).

## Completion criteria

- Section 7 names `task_nonce` (new), states the identity / request-deduplication / stage-event distinction, and both docs checkers pass (AC-6).

## Out of Scope

- `docs/23_agent/agent_13_reference-api-generated.md` (not a target, Plan Documentation impact); `agent_04_03` wording (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the docs checkers (`check_docs_structure.py`, `generate_reference_table.py --check`) | Pending | — | — | No test step applies to a docs-only row |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: docs/41_db/db_02_architecture_and_schema-schema-reference.md
