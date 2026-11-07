# Decide keep-or-retire for the never-written execution_snapshots schema

## Priority
Medium

## Summary
The `execution_snapshots` table, the `snapshot_id` column on `tool_call_state`, and the matching plumbing in the tool-call request path are never written by any code — every value stays null. Make an explicit keep-or-retire decision and align the documentation, which currently describes the table as written.

## Background
Code review evidence (Verified):
- Grep across `scripts/`: no INSERT into `execution_snapshots`; `tool_call_state.snapshot_id` is only ever written as the default null; the tool-call request dataclass carries a `snapshot_id` field that no production caller sets.
- `tool_call_state.snapshot_id` has a foreign key into `execution_snapshots`, a table nothing populates.
- `docs/23_agent/agent_04_03` states the tool-call lifecycle is written "through `tool_call_state_ops.py`" covering "the `tool_call_state` / `execution_snapshots` tables" — a stale claim: only `tool_call_state` is written.
- Origin: the snapshot concept was introduced by the idempotency/snapshot plan `plans/done/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` and the producer plan `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md`; the producer shipped without snapshot capture.
- `tools/check_db_separation.py` lists `execution_snapshots` as a workflow-domain table, giving it the appearance of live schema.

## Problem
The schema, the foreign key, the dataclass field, and the docs all assert a capability (execution snapshots) that does not exist. Implementers reading any of them will assume snapshot state is available; the FK also constrains future `tool_call_state` changes to a table nobody fills.

## Reason for Change
Dormant schema is cheapest to retire now, before the lifecycle-key redesign (sibling issue) changes the same table and before anyone builds on the null-valued field. A keep decision is equally acceptable but must be recorded as a deliberate reservation with an owner.

## Implementation Intent
Two clean outcomes: (a) retire — drop the table, the column, the FK, the dataclass field, the db-separation listing entry, and the docs sentence; or (b) keep as a documented reservation — mark the table as reserved-not-written in the schema docs and gate discussions, and state what would populate it. Mixing (null plumbing with silent docs) is not an outcome.

## Target Files or Areas
- scripts/db/schema_sql.py (table DDL, FK)
- scripts/agent/workflow/tool_call_state_ops.py (column plumbing)
- scripts/agent/context.py (request field)
- tools/check_db_separation.py (table listing)
- docs/23_agent/agent_04_03, docs/41_db pages

## Required Changes
- Record the keep-or-retire decision (owner sign-off) before code changes.
- Apply the chosen outcome consistently across DDL, code fields, tooling listings, and docs.

## Constraints
- If retired: workflow.sqlite has no migration path — the change is a shape change handled by archive-and-recreate, and the startup gate (sibling issue) must land with the new shape.
- If kept: no speculative writer code is added; documentation must say "reserved, not written".
- Do not break the current `tool_call_state` reads/writes either way.

## Acceptance Criteria
- One decision recorded with owner sign-off.
- Code, DDL, tooling lists, and docs all match the decision.
- The docs no longer claim `execution_snapshots` is written.

## Testing Expectations
- If retired: schema tests and the db-separation checks updated; workflow tests green without the column.
- If kept: a docs consistency check confirms the reservation wording exists; no code test changes required.

## Documentation Impact
This issue is partly documentation-driven: `agent_04_03` lifecycle paragraph and the `docs/41_db` workflow table reference must match the decision. Remove the current stale written-table claim regardless of the decision.

## Out of Scope
- Designing a real snapshot capture feature.
- The lifecycle-key redesign itself (sibling issue owns it).
- Dedup-store contents.

## Dependencies
- Decision feeds `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md` (required-table list) — resolve this issue's decision first.
- Coordinate DDL sequencing with `issues/20261107-203215_wfaudit002_tool-state-key-collisions.md` (same table, one recreate procedure preferred).

## Unresolved Questions
- Is `execution_snapshots` an intentional reservation for a planned capture feature (Needs confirmation with the owner)?

## AI Implementation Instruction
Do not write any snapshot-capture code in this issue. If retiring, remove every reference listed in Target Files in one change set, including the docs sentence; if keeping, only fix the docs. Record the owner decision in the issue thread before implementing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203223
- **Related target files**: scripts/db/schema_sql.py, scripts/agent/workflow/tool_call_state_ops.py, scripts/agent/context.py, tools/check_db_separation.py, docs/23_agent/agent_04_03, docs/41_db

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle).

- No-write claim confirmed: grep across `scripts/` finds no `INSERT INTO execution_snapshots`; the only `snapshot_id` references are the DDL (`scripts/db/schema_sql.py:227-228`, FK on `tool_call_state.snapshot_id` at L239) and pass-through parameters that default to `None` (`state_store.py:112,116`, `tool_call_state_ops.py:55,67-69`, `context.py:297`). No production caller passes a non-None value (grep for `snapshot_id=` finds none). — Evidence: `Verified by test` (grep) — Confidence: High
- Stale doc claim confirmed verbatim: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md:72` says the tool-call lifecycle covers "the `tool_call_state` / `execution_snapshots` tables, written through ... `tool_call_state_ops.py`", and the table map at L79 describes `execution_snapshots` as "recorded at call time" — neither is true of the code. — Evidence: `Verified by test` — Confidence: High
- Dependency confirmed: the keep-or-retire decision gates `wfaudit003`'s required-shape list (`execution_snapshots` in or out of the gate) and `wfaudit002`'s DDL edit (FK on `tool_call_state.snapshot_id` must be resolved before re-keying that table). Decide this first. — Evidence: `Derived from confirmed evidence` — Confidence: High
