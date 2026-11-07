# Enforce tool_call_state presence in the workflow schema gate

## Priority
Medium

## Summary
The workflow-database startup gate accepts databases without the `tool_call_state` (and `execution_snapshots`) tables even though the runtime writes depend on `tool_call_state`. Bring the required-shape list and the gate in line with the tables the workflow domain actually needs.

## Background
Code review evidence (Verified):
- `scripts/db/schema_sql.py` defines the workflow schema including `tool_call_state` and `execution_snapshots` in one `_WORKFLOW_SCHEMA` block created by `create_workflow_schema()`.
- The workflow schema gate's required-tables constant lists only `tasks`, `attempts`, `processed_events`, `artifacts`.
- Incremental migrations for workflow.sqlite were retired (`issues/done/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`), so the gate is the only mechanism guaranteeing shape on an existing database.
- `docs/41_db` and `docs/90_deployment` repeat the four-table list, propagating the gap into operator documentation.

## Problem
A `workflow.sqlite` created before `tool_call_state` existed (or hand-edited) passes the startup gate and deploy pre-flight, then the first workflow turn fails on insert with an operational "no such table" error far from the cause. Since migrations no longer exist, the operator's only repair is archive-and-recreate — which the gate could have surfaced at startup instead.

## Reason for Change
The gate is the domain's sole shape guarantee. Any table the runtime requires must be part of the accepted shape, otherwise "startup passed" carries no meaning for the tool-call lifecycle. The companion issue on lifecycle keys may also change the `tool_call_state` DDL, which makes the gate gap more consequential.

## Implementation Intent
Make the required-shape list a single source of truth derived from (or explicitly cross-checked against) the workflow DDL, so a table added to the schema cannot be forgotten in the gate. Keep the reject-and-archive behavior unchanged; only the shape definition changes.

## Target Files or Areas
- scripts/agent/services/workflow_schema.py (required tables / columns)
- scripts/db/schema_sql.py (workflow DDL as reference)
- deploy/init_db.sh (pre-flight wording, if it duplicates the list)
- docs/41_db and docs/90_deployment (required-table lists)

## Required Changes
- Add `tool_call_state` to the required-tables set (and decide the status of `execution_snapshots` — see the snapshots issue: if retired, drop it from the DDL instead).
- Verify the deploy pre-flight and any duplicate table lists use the same source of truth.
- Update the operator-facing required-table lists in docs.

## Constraints
- Legacy-marker rejection semantics must not change.
- A gate change is a startup behavior change: existing deployed databases created by the current `create_workflow_schema()` already contain the tables, so this must not newly reject any database the current code created.

## Acceptance Criteria
- A workflow database lacking `tool_call_state` is rejected at startup with the established diagnostic message.
- A database created by the current `create_workflow_schema()` continues to pass.
- Docs list matches the enforced shape.

## Testing Expectations
- Gate unit tests: missing `tool_call_state` rejected; full current schema accepted.
- Deploy pre-flight test continues to pass against a freshly created database.
- Docs consistency check for the updated required-table lists.

## Documentation Impact
`docs/41_db` schema pages and `docs/90_deployment` pre-flight description must state the enforced table set. Record the source-of-truth relationship (gate derived from the DDL) as an intent statement, not a duplicated table dump.

## Out of Scope
- Reintroducing any workflow.sqlite migration path.
- Changes to session/eventbus/dedup database gates.
- The lifecycle-key redesign itself (tracked separately).

## Dependencies
- Blocks on the outcome of `issues/20261107-203215_wfaudit002_tool-state-key-collisions.md` for the final `tool_call_state` shape (columns / primary key); land after that decision.
- Related decision input: `issues/20261107-203223_wfaudit010_snapshots-never-written.md` (keep-or-retire `execution_snapshots`).
- Context: `issues/done/20261031-135607_wfschema001_schema-preflight-creates-database.md` (resolved preflight behavior).

## Unresolved Questions
- Keep or retire `execution_snapshots` (decide together with the snapshots issue before finalizing the gate list).

## AI Implementation Instruction
Do not touch legacy-marker handling or error wording. Prefer deriving or cross-checking the gate list against the DDL constant over hand-copying a second list. Update duplicate table lists in deploy scripts and docs in the same change.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203216
- **Related target files**: scripts/agent/services/workflow_schema.py, scripts/db/schema_sql.py, deploy/init_db.sh, docs/41_db, docs/90_deployment

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle).

- Required-tables constant confirmed: `REQUIRED_WORKFLOW_TABLES` in `scripts/agent/services/workflow_schema.py:44-57` lists only `tasks`, `attempts`, `processed_events`, `artifacts` (with per-table required columns). — Evidence: `Verified by test` — Confidence: High
- Workflow DDL confirmed to contain the ungated tables: `execution_snapshots` (`scripts/db/schema_sql.py:227`) and `tool_call_state` (L233-242) are created by the same workflow schema block. — Evidence: `Verified by test` — Confidence: High
- Duplicate list confirmed in the deploy pre-flight: `deploy/init_db.sh:46` hardcodes `REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts"`. — Evidence: `Verified by test` — Confidence: High
- Docs propagation confirmed: the four-table list appears in `docs/41_db/db_02_architecture_and_schema-schema-reference.md:46`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md:143`, `docs/90_deployment/deployment_01_deployment.md:165` and `:300`. Separately, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` documents the two lifecycle tables but not the gate gap. — Evidence: `Verified by test` — Confidence: High
- Constraint "must not newly reject a database the current code created" confirmed satisfiable by inspection: `create_workflow_schema()` creates all six tables, so adding `tool_call_state` to the gate only rejects databases that already fail at first insert. — Evidence: `Derived from confirmed evidence` — Confidence: High
- Dependency confirmed: the gate's final required-shape list depends on the `wfaudit010` keep-or-retire decision (`execution_snapshots`) and the `wfaudit002` `tool_call_state` key redesign; this Plan must be written after both decisions.
