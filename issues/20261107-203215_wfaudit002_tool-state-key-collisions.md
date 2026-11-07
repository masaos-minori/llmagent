# Scope tool_call_state keys per task to stop cross-turn collisions

## Priority
High

## Summary
The agent-side tool-call lifecycle rows (`tool_call_state`) are keyed by a session+content hash that contains no turn or task component, so an identical tool call in a later turn silently reuses the earlier turn's row. Make the recorded lifecycle per-task as documented, without breaking the dispatcher-side dedup contract.

## Background
Code review evidence (Verified):
- `tool_runner` derives the state key from method/tool/args/session only; the same key space is shared with the dispatcher's durable dedup store by design (`docs/23_agent/agent_04_03` documents the key as the shared transport dedup key).
- `tool_call_state_ops.record_tool_call` uses `INSERT OR IGNORE` on the `idempotency_key` primary key, so the row keeps the first turn's `task_id`.
- `finalize_tool_call` updates the row by key, so turn 2 finalizes turn 1's row; turn 2 never has its own state row.
- `classify_stale_pending` selects rows by `task_id`, so a pending row recorded under an earlier task is never surfaced as interrupted to a later turn.
- The same docs state rows are "scoped to a task_id" — the implementation does not provide that scoping.
Context: `issues/done/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` and `issues/done/20261031-175803_toolstate001_tool-call-state-producer.md` established the producer/consumer split.

## Problem
Repeating an identical tool call (same tool, same arguments, same session) in a later turn: no new lifecycle row is created, the earlier row is mutated, and the new call's pending/completed/failed state is invisible to the per-task stale-interrupted reporting. Tool-call lifecycle data is wrong for every repeated call.

## Reason for Change
Correctness of the persisted tool-call lifecycle and of the interrupted-call control message depends on one row per call per task. Today the failure is silent: no error, just missing state. The bug also contradicts the documented per-task scoping.

## Implementation Intent
Keep the transport dedup key (dispatcher contract) unchanged. The lifecycle table needs its own identity that includes the task (or turn) alongside the key — e.g. a composite primary key of (idempotency_key, task_id) — so `record_tool_call` writes one row per task and `finalize_tool_call` finalizes the row belonging to the calling task. Decide explicitly how a completed row from an earlier task interacts with a replayed call.

## Target Files or Areas
- scripts/agent/tool_runner.py (state key derivation)
- scripts/agent/workflow/tool_call_state_ops.py (record / finalize / classify)
- scripts/db/schema_sql.py (tool_call_state DDL)
- docs/23_agent/agent_04_03 (per-task scoping claim)

## Required Changes
- Make the recorded lifecycle row unique per (key, task) so a repeated call in a new turn gets its own row.
- Finalize and stale-classify by the calling task's own row.
- Update the docs section to describe the actual identity of lifecycle rows vs transport dedup rows.

## Constraints
- Do not change the dispatcher-side dedup key format or the shared transport identity (ADR/gateway contract).
- workflow.sqlite has no migration path: a DDL change to `tool_call_state` requires the archive-and-recreate operational procedure, and the startup gate (see the schema-gate sibling issue) must then enforce the new shape.
- Preserve the interrupted-control-message behavior for genuinely stale rows.

## Acceptance Criteria
- Two identical calls in different turns produce two rows with distinct task_ids; each is finalized independently.
- `classify_stale_pending` reports only the current task's rows.
- No regression in the interrupted-call control message tests.

## Testing Expectations
- Unit test: identical (tool, args, session) called in turn 1 and turn 2 -> two rows, per-task finalize correctness.
- Regression tests for `finalize_tool_call` and stale classification.
- Schema consistency checks (`tools/check_db_separation.py`, docs consistency) after the DDL change.

## Documentation Impact
`agent_04_03` must describe the lifecycle row identity accurately (per-task scoping) and the relationship to the transport dedup key. No new implementation-derived detail beyond the identity rule.

## Out of Scope
- Dispatcher-side replay semantics for completed calls.
- Wiring snapshot capture (see the execution_snapshots issue).
- Changing session-level dedup behavior in `shared/mcp_dedup.py`.

## Dependencies
- Coordinate with `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`: any `tool_call_state` DDL change and the gate must land together (gate depends on the final shape).
- Context: `issues/done/20261031-175803_toolstate001_tool-call-state-producer.md` (resolved producer contract).

## Unresolved Questions
- Is dispatcher-side replay of completed results within retention the intended product behavior for repeated identical calls? (Needs confirmation; decides whether the lifecycle fix alone is sufficient.)

## AI Implementation Instruction
Do not touch the transport key derivation shared with the dispatcher. Change only the lifecycle table identity and the record/finalize/classify paths. Treat the DDL change as a schema-shape change: update the startup gate, docs, and the recreate procedure in the same change set.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203215
- **Related target files**: scripts/agent/tool_runner.py, scripts/agent/workflow/tool_call_state_ops.py, scripts/db/schema_sql.py, docs/23_agent/agent_04_03

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle).

- Key derivation confirmed: `_state_key` = `derive_idempotency_key("call_tool", name, args, session_id)` — sha256 of method/tool/canonical-args/session uid, no turn/task component (`scripts/agent/tool_runner.py:149-160`, `scripts/shared/http_transport.py:62-75`). A separate audit-only key containing workflow/task/turn/call ids already exists (`_idempotency_key`, tool_runner L138-146) but is not the state key. — Evidence: `Verified by test` — Confidence: High
- `record_tool_call` confirmed `INSERT OR IGNORE` on the `idempotency_key` PRIMARY KEY (`scripts/agent/workflow/tool_call_state_ops.py:64-71`); `finalize_tool_call` updates `WHERE idempotency_key=?` only (L74-80); `classify_stale_pending` selects `WHERE task_id=? AND state='pending'` (L113-115). — Evidence: `Verified by test` — Confidence: High
- DDL confirmed: `tool_call_state.idempotency_key TEXT PRIMARY KEY`, separate `task_id TEXT NOT NULL`, `snapshot_id` FK into `execution_snapshots` (`scripts/db/schema_sql.py:233-242`) — a second row for the same key in a new task is rejected by the PK. — Evidence: `Verified by test` — Confidence: High
- Docs claim confirmed: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` L78 states rows are "keyed by the transport idempotency key and scoped to a `task_id`" — the implementation stores but does not enforce per-task scoping. — Evidence: `Verified by test` — Confidence: High
- Dependency confirmed real: the DDL change here intersects `wfaudit003` (gate shape) and `wfaudit010` (snapshot_id FK on the same table); all three touch `tool_call_state`/`execution_snapshots` DDL and should share one archive-and-recreate procedure.
