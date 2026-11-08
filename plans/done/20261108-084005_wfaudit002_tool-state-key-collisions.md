## Goal
Scope the `tool_call_state` lifecycle row key per task so an identical tool call in a later turn creates its own state row instead of silently reusing the first turn's row — without touching the dispatcher-side transport dedup contract.

## Priority
High

## Scope
- **In-Scope**:
  - `scripts/agent/tool_runner.py` — `_state_key` composes the transport key with a task-scope component (`{transport_key}:{task_id}`); `_idempotency_key` (audit-only) untouched.
  - `scripts/agent/workflow/tool_call_state_ops.py` — no key-format knowledge leaks in: helpers keep taking the key as an opaque string (verify finalize/classify call sites pass the composed key consistently).
  - Tests: same tool call content in two different tasks produces two rows with distinct task scoping (identical content inside one task remains one row — retry-invariance, `REQ-003`); finalize updates only the matching row.
  - Docs: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` key description (L78) updated to the composed form.
- **Out-of-Scope**:
  - DDL changes to `tool_call_state` (no PK/column change — the key redesign is a value-composition change).
  - The transport `X-Idempotency-Key` sent to the MCP dispatcher — byte-identical, unchanged (`scripts/shared/http_transport.py`).
  - Purging finished tool-call rows (retention of `tool_call_state` is a separate concern; recorded as `UNK-02`).
- **Dependencies**: After `wfaudit010` (the `snapshot_id` FK on the same table is retired there; no key collision with that column decision remains). Independent of `wfaudit003`, but 003's gate then confirms `tool_call_state` presence for databases created by this design.

## Background
`_state_key` derives the state row key from method/tool/args/session only (`scripts/agent/tool_runner.py:149-160` calling `derive_idempotency_key`, `scripts/shared/http_transport.py:62-75` — sha256 over method/tool/canonical-args/session uid). `record_tool_call` uses `INSERT OR IGNORE` on the `idempotency_key` PRIMARY KEY (`scripts/agent/workflow/tool_call_state_ops.py:64-71`), so a second turn with identical call content keeps the first turn's row (first `task_id` wins); `finalize_tool_call` updates by key alone (L74-80), finalizing turn 1's row during turn 2; `classify_stale_pending` selects `WHERE task_id=?` (L113-115) so a row recorded under an earlier task is never surfaced for the current task. A per-turn audit key already exists separately (`_idempotency_key`, tool_runner L138-146) but is not the state key. Docs claim rows are "keyed by the transport idempotency key and scoped to a `task_id`" (agent_04_03 L78) — stored but not enforced. All verified in the issue's `## Adversarial Validation`.

## Problem
Tool-call lifecycle state is wrong across turns: turn 2 never gets its own pending row, stale classification misses cross-turn rows, and the audit trail attributes a later turn's call to an earlier task.

## Reason for Change
The documented contract (per-task lifecycle rows) is already what the table and readers assume; only the key composition fails to deliver it. A value-level fix restores the documented semantics with no schema change.

## Implementation Intent
Compose the state key as `{transport_key}:{task_id}` at the single derivation point (`_state_key`). The wire transport key stays exactly as today (separate call site in the HTTP transport). `tool_call_state_ops` treats keys as opaque — no format coupling. Every state operation (record / finalize / classify) already flows through the composed key via `ctx.workflow.current_task_id`.

## Requirements
- `REQ-001`: `_state_key` returns `{transport_key}:{task_id}` (task component from `ctx.workflow.current_task_id`); when no task is wired, no state row is written (existing behavior preserved).
- `REQ-002`: The X-Idempotency-Key sent over HTTP is unchanged (same `derive_idempotency_key` inputs) — dispatcher-side dedup contract untouched.
- `REQ-003`: Identical call content in a different task produces a distinct state row (`INSERT OR IGNORE` no longer swallows it); within one task, a retry of the same call still reuses one row (retry-invariance preserved).
- `REQ-004`: `finalize_tool_call` and `classify_stale_pending` operate on the composed key/`task_id` and never touch another task's row.
- `REQ-005`: Docs state the composed key; tests pin REQ-001-REQ-004.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | Modify | `_state_key` composes transport key + `task_id` (L149-160); docstring updated | `REQ-001`/`REQ-003` | Key derived from method/tool/args/session only (re-verified at HEAD `ad48bfa28`: `_state_key` calls `derive_idempotency_key("call_tool", pc.name, pc.args, str(ctx.session.session_id))`) | `tests/agent/test_tool_runner*.py` state tests | `Verified` |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | Key description (L78) states the composed form and per-task enforcement | `REQ-005` | Current text already claims task scoping (stale promise, re-verified: L78 "keyed by the transport idempotency key and scoped to a `task_id`") | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Confirmed no-change (Step 2 validation): helpers treat the key as opaque; DDL untouched (`idempotency_key TEXT PRIMARY KEY` single column, re-verified in `scripts/db/schema_sql.py` `tool_call_state` DDL) | `REQ-004` |
| `scripts/shared/http_transport.py` | Confirmed no-change (Step 2 validation): `derive_idempotency_key` (L62-75) stays byte-identical; the state-side composition happens in `tool_runner.py` only | `REQ-002` |
| `scripts/agent/tool_runner.py` (`_record_pending_state`, finalize call sites) | Confirms record and finalize use the same `_state_key` derivation — one edit fixes both | `REQ-001`/`REQ-004` |
| `scripts/agent/workflow/workflow_engine.py` | `build_turn_control_message` / `classify_stale_pending` consumer path (L165-176) | `REQ-004` |
| `scripts/mcp_servers/dispatch.py` | Dispatcher-side dedup consumer of the transport key — proves the wire contract is a separate key space | `REQ-002` |
| `plans/20261108-084001_wfaudit010_snapshots-never-written.md` | Same-table decision (FK retirement) landed before this plan | Dependencies |

## Acceptance Criteria
- `REQ-001`: Unit test: two tasks, identical tool call content -> two `_state_key` values, both recorded as pending rows with their own `task_id`.
- `REQ-002`: Transport test: outgoing X-Idempotency-Key value unchanged from HEAD for the same call (fixture comparison).
- `REQ-003`: Within one task, calling `record_tool_call` twice with the composed key yields one row (INSERT OR IGNORE retry-invariance intact).
- `REQ-004`: Finalize for task A's key leaves task B's identical-content row pending; `classify_stale_pending(A)` never lists B's row.
- `REQ-005`: New tests fail on HEAD (collision swallow) and pass after; full `tests/agent/` suite green.

## Tests
- Cross-task distinctness and intra-task retry-invariance tests at the state-ops level using composed keys from `tool_runner` helpers.
- Transport key regression test (value equality against a recorded HEAD fixture).
- Stale-classification isolation test (task A timeout does not interrupt task B's row).

## Documentation Impact
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — key composition sentence at L78 rewritten to `{transport key}:{task_id}`; keep the "shares identity with the dispatcher's durable store" statement scoped to the transport key only.
- Run docs checkers for domain agent per `routing.md`.

## Assumptions
- `ctx.workflow.current_task_id` is always set when a state row is written (validated: `_record_pending_state` returns None when task context is unwired).
- Appending `:task_id` to a 64-hex sha256 keeps keys collision-free and readable; no hash recomposition needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether existing production `tool_call_state` rows (old unscoped keys) need a cleanup: after the change, a resumed old task cannot finalize its old-key row | production row census not taken | one SELECT probe at deploy; rows are audit history — acceptable to leave, or purge pending rows older than the wfaudit001 horizon | `False` |
| `UNK-02` | retention policy for finished `tool_call_state` rows (never pruned today) | owner decision | candidate follow-up issue linked to the `wfaudit001` purge design | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | Modify | every tool-call state write/finalize | 14 | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | docs only | N/A | N/A | not applicable |

## Design
**Key composition at one site.** The only derivation of the state key is `_state_key`; appending the task component there propagates to record, finalize, and stale detection because all three use the same helper output. The wire transport key is derived independently at the HTTP layer, so the dispatcher contract is untouched by construction.

**Why not a composite PRIMARY KEY (`idempotency_key`,`task_id`)**: DDL change on a table with no migration path — it would split the archive-and-recreate procedure and couple this fix to `wfaudit003`/`wfaudit010` schema work. The value-composition achieves the same isolation with zero schema risk, and keeps the PK single-column contract that `INSERT OR IGNORE` retry-invariance relies on.

**Audit trail coherence**: the row's `task_id` column now always matches the key's task component, making `classify_stale_pending`'s `WHERE task_id=?` selection exact.

## Implementation steps
1. **Phase 1: Key composition (`REQ-001`, `REQ-003`, `REQ-004`).** Edit `_state_key`; add cross-task/intra-task tests.
2. **Phase 2: Transport regression (`REQ-002`).** Wire-key fixture test; stale-classification isolation test.
3. **Phase 3: Documentation (`REQ-005`).** Update agent_04_03; docs checkers.

### Release units
**Unit**: wfaudit002-full | **Phases**: 1, 2, 3 | **Reason**: single derivation change; shipping record-side without finalize-side is not representable because both share the helper.

## Validation plan
- `uv run pytest tests/agent/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- New collision test must fail on HEAD (second row silently missing).
- Transport key fixture test must pass on HEAD and after (regression lock).
- Deploy probe (`UNK-01`): `SELECT COUNT(*) FROM tool_call_state WHERE state='pending';` recorded before/after deploy.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 3.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A dispatcher-side consumer expects the state key to equal the wire key | Medium | High (dedup mismatch) | Step 2 grep found state-key consumers only in the agent state path; Phase 2 fixture test locks the wire value separately |
| Old pending rows keyed without task component become unreachable by new code | Medium | Low (stale audit rows) | `UNK-01` probe + optional cleanup in the deploy procedure |
| Key length growth (`64-hex:task_uuid`) hits any implicit length assumption | Low | Low | Column is TEXT; grep confirms no length checks (Step 2) |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Key composition (tool_runner.py edit + cross-task/intra-task tests) | Completed | 20261109-070023 | 20261109-070023 |  |
| 2 | Phase 2: Transport regression (wire-key fixture test; stale-classification isolation test) | Completed | 20261109-070023 | 20261109-070023 |  |
| 3 | Phase 3: Documentation (agent_04_03 key description; docs checkers) | Completed | 20261109-070023 | 20261109-070023 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-141525_01_scripts_agent_tool_runner.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-141525_02_docs_23_agent_agent_04_03_state-and-persistence-platform-databases.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203215_wfaudit002_tool-state-key-collisions.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084005
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (key lacks task component) | `scripts/agent/tool_runner.py` | Composed key with task_id | unit test |
| `REQ-002` | Issue constraint ("without breaking dispatcher dedup") | `scripts/shared/http_transport.py` (no-change) | wire key unchanged | fixture test |
| `REQ-003` | Issue Problem (row reuse) | state-ops behavior via key | cross-task distinct, intra-task invariant | state-ops tests |
| `REQ-004` | Issue Problem (finalize/classify cross-turn) | tool_runner call sites | per-row targeting | isolation tests |
| `REQ-005` | Issue Testing Expectations | tests + docs | fail on HEAD; docs accurate | pytest + docs checkers |

## Notes
- Source verified against HEAD `926dbc109`; evidence in the issue's `## Adversarial Validation`.
- Sequence: `wfaudit010` (FK retirement) -> this plan -> `wfaudit003` (gate list finalized with the final table shape).
- Adversarial re-verification at HEAD `ad48bfa28` (2026-11-08): all key-path claims re-confirmed (`_state_key` = `derive_idempotency_key("call_tool", pc.name, pc.args, session uid)`, L149-160; `record_tool_call` INSERT OR IGNORE on the single-column `idempotency_key` PRIMARY KEY; `finalize_tool_call` UPDATE by key; `classify_stale_pending` `WHERE task_id=?`; docs L78 stale promise confirmed; no length/format validation on stored state keys — the `^[A-Za-z0-9_-]{1,64}$` house key shape is documented only for the transport key in `http_transport.py` and that path is unchanged). The `tool_call_state` DDL confirms `wfaudit010` landed (no `snapshot_id` FK). Two no-change target rows demoted to Reference Files; no procedure documents for them.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-141525 -->