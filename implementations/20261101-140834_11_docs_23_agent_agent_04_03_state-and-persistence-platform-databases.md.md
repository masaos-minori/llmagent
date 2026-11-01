## Goal

Update the StateStore responsibility-scope paragraph and the "fresh, unique task keys" operational bullet in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` to the `task_nonce` (new) name and contract (Plan REQ-005, AC-6).

## Scope

- StateStore Responsibility Scope paragraph (currently `agent_04_03...md:72`): task-key sentences renamed to `task_nonce` (new); the existing "two kinds of keys" contrast (task key vs `tool_call_state.idempotency_key`) is kept and rephrased so the transport dedup key remains the only `idempotency_key` in the workflow database.
- Operational Notes bullet "A new session against a retained `workflow.sqlite` always receives fresh, unique task keys ..." (currently `:99`): reworded to name the nonce explicitly.
- The toolexec001 table row for `tool_call_state` (`:78`) keeps its "transport idempotency key" wording untouched.

## Assumptions

- Plan overlap judgment (re-recorded): compatible with toolexec001's already-landed edits to this file; the Keywords section contains no `idempotency_key` term, so no Keywords change is needed (verified 2026-11-01).
- Line cites are from HEAD `456fb7ca2` (re-verified 2026-11-01).

## Design decisions

- REQ-005's three-way distinction (task identity / task-request deduplication / stage-event idempotency) is stated here once, in the scope paragraph, and db_02 (row 10) carries the schema-side wording; neither doc restates code.

## Alternatives considered

- Also renaming the `tool_call_state` mentions: rejected — that column keeps its name (`tool_call_state.idempotency_key` is the transport dedup key, REQ-010 of toolexec001, already landed).

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. In the scope paragraph (`:72`): replace "Each task row's `idempotency_key`" with "Each task row's `task_nonce` (new)" and adjust the contrast sentence so "the task `task_nonce` (new) is a random task-scoped identifier" replaces the task-side `idempotency_key` phrase.
2. Add the REQ-005 distinction sentence to the same paragraph: task identity is `task_id`; duplicate `create_task` calls are new tasks (no request-level dedup); stage re-execution is prevented by the `processed_events` event key.
3. In Operational Notes (`:99`), reword the bullet to "always receives a fresh `task_id` and a fresh, unique `task_nonce` (new)".
4. Do not touch `:78` or the Keywords section.

### Method
Two targeted paragraph edits in one commit.

### Details
- Keep the link to `agent_09_01_data-layer-session-db.md` and the tool-call lifecycle wording in `:72` intact.

## Compatibility considerations

- `docs/00_index.md` task-scope mapping lists this file for this Plan (Plan Documentation impact: Yes).
- Docs size ceiling and `tools/check_docs_structure.py` must pass (AGENTS.md rule 9).

## Security considerations

- N/A: prose-only change.

## Rollback considerations

- Text revert paired with rows 01-04/12 so docs never name a column absent from the DDL.

## Validation plan

- `uv run python tools/check_docs_structure.py` — no findings.
- `uv run python tools/generate_reference_table.py --check` — no drift.

## Completion criteria

- Both named locations describe `task_nonce` (new) and the three-way distinction; docs checkers pass (AC-6).

## Out of Scope

- `db_02` wording (row 10); `tool_call_state` table documentation (toolexec001, landed).

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

### Verification Notes (2026-11-01)
- Passed against HEAD `6faf6c4cb`: scope paragraph at `:72`,
  `tool_call_state` table row at `:78`, Operational Notes bullet at `:99`
  all confirmed; Keywords section contains no `idempotency_key` term.
- Cycle: cycle 3 (docs wave, together with row 10 and the db_03 update from
  row 12's verification notes).

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
- **Related target files**: docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md
