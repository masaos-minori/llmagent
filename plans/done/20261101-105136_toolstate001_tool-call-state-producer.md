## Goal
- Make the agent's workflow tool-execution path the production writer for the `tool_call_state` table in `workflow.sqlite`: every tool call executed under an active workflow task is recorded as `pending` before execution and finalized to `completed`/`failed` after, using the same idempotency key the HTTP transport derives, so `classify_stale_pending` can classify crash-left rows as `interrupted` and the replay path can skip them.

## Priority
High

## Scope
- **In-Scope**:
  - Recorder injection: `ToolCallRecorder` protocol + `WorkflowState.tool_call_recorder` field; set/cleared by the workflow engine adapter around the turn.
  - Producer writes in `scripts/agent/tool_runner.py`: record `pending` before execution, finalize `completed`/`failed` after, leave `pending` on `BaseException`/`CancelledError`.
  - Idempotency-key identity: derive the recorded key at the record point with `shared.http_transport.derive_idempotency_key` (same function the transport uses), uid = `str(ctx.session.session_id)`.
  - `retry_class` from `shared.mcp_dedup.retry_class(name)`.
  - Unit and wiring tests; agent tool-execution flow doc update.
- **Out-of-Scope**:
  - Replay/resume of interrupted calls (`scripts/agent/workflow/workflow_engine.py` replay logic beyond the existing `build_turn_control_message`).
  - Transport-side idempotency (REQ-007 of toolexec001): `scripts/shared/http_transport.py`, `scripts/shared/mcp_dedup.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/state_store.py`, schema, and migrations MUST NOT be modified — the helpers already exist and are consumed as-is.
  - Registry manifest changes (no public API, config, or schema change).
- **Dependencies**: Follow-up named by Phase 6 of `plans/done/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (Phase 6 `In Progress`): the `classify_stale_pending` + `build_turn_control_message` injection points landed in committed master (`923102c75`, `d14bf433f`); this plan supplies the missing writer side. Single-path plan; no sibling-issue ordering. Note: the source Issue lists `scripts/shared/tool_http_transport.py` as a landed dependency — it is NOT in committed master (see UNK-05).

## Background
`toolexec001` landed a durable tool-call state platform: the `tool_call_state` table (`scripts/db/migrations_workflow.py`, `923102c75`), the helper layer `scripts/agent/workflow/tool_call_state_ops.py` (`record_tool_call`, `finalize_tool_call`, `pending_tool_calls`, `classify_stale_pending`), the `StateStore` facade (`scripts/agent/workflow/state_store.py:174-199`), and the consumer side in `WorkflowEngine.build_turn_control_message` (`scripts/agent/workflow/workflow_engine.py:110-128`) which classifies stale pending rows as `interrupted` and injects them into the next turn's control message. The consumer side is dead weight until a production writer exists: no production code calls `record_tool_call`/`finalize_tool_call` (only tests), so the `tool_call_state` table is always empty at runtime.

## Problem
Tool calls executed by a crashed workflow are invisible to the recovery path. After a crash the engine has no rows to classify, so the LLM is free to re-issue identical `WAIT_FOR_RESULT` tool calls; the only remaining guard is the dispatcher-side `mcp_dedup` table (`mcp_dedup.sqlite`), which was previously observed failing (two `WAIT_FOR_RESULT` dispatches for one `X-Request-Id`). The agent-side `tool_call_state` guard was designed for exactly this and has no writer.

## Reason for Change
The consumer (replay classification, `build_turn_control_message` control-message injection) and the platform (helpers, facade, schema, `StateStore` accessors) are all committed and verified; the writer is the single remaining gap blocking toolexec001 Phase 6 completion and durable crash-replay behavior.

## Implementation Intent
Inject a recorder handle (structural protocol, satisfied by the existing `StateStore`) into `AgentContext.workflow` at the workflow turn boundary (the adapter, which already holds the `StateStore` and already sets `ctx.workflow.current_task_id`), and record/finalize inside the tool-execution choke point `scripts/agent/tool_runner.py` (`_recorded_call` / `execute_one_tool_call`), which every group/DAG/serial execution path already funnels through and which already receives `ctx`. No new function signatures, no shared-layer changes.

## Requirements
- `REQ-001`: When `ctx.workflow.current_task_id` is set and `ctx.workflow.tool_call_recorder` is not `None`, record a `tool_call_state` row (`state=pending`, `task_id`, `tool`, `retry_class`, `idempotency_key`, `snapshot_id` NULL) before the call is dispatched to the executor.
- `REQ-002`: Finalize the row to `completed` when the call produces a result row (including an error-result row) and to `failed` when the call raises an Exception that `_recorded_call` converts into an error row.
- `REQ-003`: The recorded `idempotency_key` equals `shared.http_transport.derive_idempotency_key("call_tool", name, args, uid)` with `uid == str(ctx.session.session_id)` — the same key the transport sends as `X-Idempotency-Key` for the same call.
- `REQ-004`: `BaseException` (including `asyncio.CancelledError`) propagates and leaves the row `pending`, so `classify_stale_pending` can later mark it `interrupted`.
- `REQ-005`: `WorkflowState` gains a `tool_call_recorder` field typed as a minimal structural protocol (`ToolCallRecorder`: `record_tool_call` / `finalize_tool_call` shapes); the adapter sets it to its `StateStore` at the turn entry where `ctx.workflow.current_task_id` is set and clears it in `finally` at turn exit.
- `REQ-006`: `retry_class` is taken from `shared.mcp_dedup.retry_class(name)`.
- `REQ-007`: Recorder failures are non-fatal: any Exception raised by record/finalize is logged and does not abort the tool call (mirrors `_record_transport_failure` / `tool_audit` non-blocking precedent).
- `REQ-008`: Non-workflow paths (plain REPL turn, recorder `None` or no active task): zero behavior change, zero rows written.
- `REQ-009`: The audit-only `_idempotency_key` (`{workflow_id}:{task_id}:{turn_id}:{call_id}`, `tool_runner.py:123`) stays unchanged and is NOT reused for `tool_call_state`.
- `REQ-010`: No modification to `scripts/shared/http_transport.py`, `scripts/shared/mcp_dedup.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/state_store.py`, schema, or migrations.
- `REQ-011`: The agent tool-execution flow documentation describes the producer lifecycle (record/finalize/crash-pending).

## Implementation Target Files
**Freeze status**: Frozen (issue-to-plan Step 8 validation passed 2026-11-01: all rows exist, are individually evidenced against committed master `a7c9e4fdb`, and are linked to Plan requirements; overlap check run via `tools/check_plan_target_overlaps.py`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_runner.py | Modify | Producer writes: record `pending` before dispatch, finalize `completed`/`failed` after; derive transport-identical key; non-fatal recorder errors | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-009; AC-1, AC-2, AC-3, AC-4, AC-6, AC-7, AC-9 | Choke point `_recorded_call` (`tool_runner.py:65-95`) funnels serial and gathered group paths; `execute_one_tool_call` (`:190-234`) already receives `ctx` and already calls `_idempotency_key`/`audit_tool_exec` (`:213-225`); BaseException propagation documented at `:77-79`, `:83` | tests/agent/test_tool_runner.py | Verified |
| scripts/agent/context.py | Modify | Add `ToolCallRecorder` protocol type and `WorkflowState.tool_call_recorder` field (default `None`) | REQ-005; AC-5 | `WorkflowState` already carries `workflow_id`/`current_task_id` read by `tool_runner._idempotency_key` (`tool_runner.py:128-130`); no new import needed (protocol is typing-only) | tests/agent/test_tool_runner.py, tests/agent/test_orchestrator.py | Verified |
| scripts/agent/workflow_engine_adapter.py | Modify | Set `ctx.workflow.tool_call_recorder = self._state_store` at the turn entry where `current_task_id` is set; clear in `finally` | REQ-005; AC-5 | Adapter constructor already receives `state_store: StateStore` (lines 84, 95); `ctx.workflow.current_task_id = task.task_id` at line 292, cleared at line 300; `handle_llm_turn(control_message=...)` passes the injected control message to `LLMTurnRunner` | tests/agent/test_orchestrator.py | Verified |
| tests/agent/test_tool_runner.py | Modify | Unit tests for record/finalize/pending-retention, key identity, retry_class, no-op and non-fatal recorder paths | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-008; AC-1..AC-4, AC-6..AC-8 | Existing producer-path suite (`TestBuildTurnControlMessage` region also mirrored in `tests/agent/workflow/test_workflow_engine.py:324`); file is committed and stable (no churn flags this session) | (this file) | Verified |
| tests/agent/test_orchestrator.py | Modify | Adapter wiring tests: recorder set on `ctx.workflow` during a workflow turn, cleared after turn exit including on raising turns | REQ-005, REQ-008; AC-5, AC-8 | Only committed suite that drives `WorkflowEngineAdapter` end-to-end (`tests/agent/test_orchestrator.py`) | (this file) | Verified |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Modify | Document the `tool_call_state` producer lifecycle in the tool-execution flow doc | REQ-011; AC-11 | `docs/00_index.md:149` maps "Agent REPL flow / tool execution" to this doc; the table/consumer side is already documented in `docs/23_agent/agent_04_03_state-and-persistence.md` (reference only) | N/A: documentation file | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/workflow/tool_call_state_ops.py | Exact signatures/semantics of `record_tool_call` (INSERT OR IGNORE + commit), `finalize_tool_call` (UPDATE by key), `pending_tool_calls`, `classify_stale_pending`, `ToolCallState` row shape | REQ-001, REQ-002, REQ-004, REQ-010 |
| scripts/agent/workflow/state_store.py | `StateStore` facade methods (lines 174-199) that structurally satisfy `ToolCallRecorder` | REQ-005, REQ-010 |
| scripts/shared/http_transport.py | `derive_idempotency_key` (line 62) and the transport's uid choice `_session_id or sha256(auth_token)` (lines 189-202); defines the key the recorded row must match | REQ-003 |
| scripts/shared/mcp_dedup.py | `retry_class(name)` (line ~165) and the dispatcher-side dedup table semantics (distinct DB, do not conflate) | REQ-006 |
| scripts/agent/workflow/workflow_engine.py | Consumer semantics to preserve: `build_turn_control_message` (line 110), `classify_stale_pending` call (line 128), `pending_timeout_minutes` config source | REQ-004 |
| scripts/agent/llm_turn_runner.py | Production call site `execute_all_tool_calls` (line 158) and `control_message` plumbing (lines 61-122); confirms no change needed there | REQ-005, REQ-008 |
| scripts/agent/commands/mixin_base.py | `set_session_id(str(ctx.session.session_id))` (line 39): proves transport uid equals the session-id string used in the recorded key | REQ-003 |
| scripts/agent/repl_input_loop.py | Same `set_session_id` propagation at the REPL entry (line 111) | REQ-003 |
| scripts/agent/tool_preparation.py | Error-row shape (`:34-58`) that `_recorded_call` converts failures into — the `completed`/`failed` mapping boundary | REQ-002 |
| scripts/db/migrations_workflow.py | `tool_call_state` schema (columns `idempotency_key`, `task_id`, `tool`, `state`, `retry_class`, `snapshot_id`) already migrated | REQ-001, REQ-010 |
| config/mcp_dedup.toml | `pending_timeout_minutes` source for `classify_stale_pending` | REQ-004 |
| tests/agent/workflow/test_workflow_engine.py | `TestBuildTurnControlMessage` (line 324) manual-injection behavior to preserve | REQ-008, REQ-010 |
| tests/agent/workflow/test_workflow_state_store.py | Existing committed coverage of the `StateStore` recording facade — reuse fixtures/patterns for the new unit tests | REQ-001, REQ-003 |
| docs/23_agent/agent_04_03_state-and-persistence.md | Already documents the `tool_call_state` table and consumer side; must stay consistent with the new producer text | REQ-011 |

## Acceptance Criteria
- `AC-1` (REQ-001): With a recorder and an active task, a `tool_call_state` row with `state=pending` exists from the moment execution of the call begins (observable via `pending_tool_calls(task_id)` in tests).
- `AC-2` (REQ-002): After a successful call the row is `completed`; after a call whose execution raised a converted Exception it is `failed`; an error-result row returned normally is `completed`.
- `AC-3` (REQ-003): A test computes `derive_idempotency_key("call_tool", name, args, str(session_id))` and asserts it equals both the recorded row's key and the key the transport produces for the same call with `set_session_id(str(session_id))` applied.
- `AC-4` (REQ-004): A test that raises `CancelledError`/`BaseException` mid-call leaves the row `pending`, and `classify_stale_pending` then returns it as `interrupted`.
- `AC-5` (REQ-005): During a workflow turn `ctx.workflow.tool_call_recorder` is the adapter's `StateStore`; after the turn (including a raising turn) it is `None`.
- `AC-6` (REQ-006): Recorded `retry_class` equals `mcp_dedup.retry_class(name)` for both `idempotent` and `non_idempotent` class names.
- `AC-7` (REQ-007): A recorder whose `record_tool_call`/`finalize_tool_call` raise does not change the tool call's result; the failure is logged.
- `AC-8` (REQ-008): REPL-style runs (recorder `None`, or no active task) write no rows and produce identical behavior to today (existing suites stay green unchanged).
- `AC-9` (REQ-009): `_idempotency_key` composition and `audit_tool_exec` call are unchanged (existing audit tests stay green).
- `AC-10` (REQ-010): `git diff` shows no change to the four protected files, schema, or migrations.
- `AC-11` (REQ-011): The tool-execution flow doc describes record→pending, finalize→completed/failed, crash-retention, and the key identity.

## Tests
- `REQ-001`/`REQ-002` (`tests/agent/test_tool_runner.py`): fake-recorder unit tests asserting pending-then-completed and pending-then-failed sequences, in both serial and gathered group paths.
- `REQ-003` (`tests/agent/test_tool_runner.py`): identity test against `derive_idempotency_key` and a real sqlite `StateStore` (pattern from `tests/agent/workflow/test_workflow_state_store.py`).
- `REQ-004` (`tests/agent/test_tool_runner.py`): `CancelledError` propagation test + `classify_stale_pending` → `interrupted` regression.
- `REQ-006` (`tests/agent/test_tool_runner.py`): retry_class value tests.
- `REQ-007` (`tests/agent/test_tool_runner.py`): raising-recorder test (call result unchanged, warning logged).
- `REQ-008` (`tests/agent/test_tool_runner.py`): recorder-absent test asserting no recorder interaction.
- `REQ-005` (`tests/agent/test_orchestrator.py`): adapter sets/clears `ctx.workflow.tool_call_recorder` around `handle_llm_turn`, including on raising turns.
- Regression: full existing suites (`uv run pytest`) must stay green; `TestBuildTurnControlMessage` injection behavior must not change.

## Documentation Impact
Yes. The "Agent REPL flow / tool execution" row of `docs/00_index.md`'s Document References
by Task table maps to the tool-execution execution doc named in the Implementation Target
Files table; it must gain the producer lifecycle (`REQ-011`, AC-11). The state/persistence
doc already describes the `tool_call_state` table and consumer side and is used as a
consistency reference (Reference Files), not a modification target.

## Assumptions
- Baseline is committed master `a7c9e4fdb` (2026-11-01); all "committed" statements in this Plan were re-verified against it on 2026-11-01 after a mid-session working-tree reset (see UNK-05).
- `session.session_id` is always a positive integer (SQLite autoincrement), so `str(session_id)` is non-empty and the transport's uid branch `self._session_id or ...` always selects it when `set_session_id` was called (both agent entry points verified).
- `StateStore` structurally satisfies the `ToolCallRecorder` protocol via its committed facade methods (`state_store.py:174-189`).
- The `tool_call_state` table exists in production `workflow.sqlite` (migration landed in `923102c75`; covered by `tests/agent/workflow/test_state_store.py`).
- The adapter runs one workflow turn at a time per `AgentContext`, so a single `WorkflowState` field is safe (no concurrent-turn recorder clobbering).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Issue question 1: is the audit `_idempotency_key` the identity used by the transport? (Issue's open question) | — resolved at plan time | Resolved: it is NOT. Recorded key must be `derive_idempotency_key("call_tool", name, args, uid)` re-derived at the record point (`tool_runner.py:213` audit key composition `{workflow_id}:{task_id}:{turn_id}:{call_id}` is audit-only); enforced by REQ-003/REQ-009 and AC-3 | False |
| UNK-02 | Issue question 2: is the transport's uid exactly `session_id`? (Issue's open question) | — resolved at plan time | Resolved: uid is `transport._session_id` (set from `str(ctx.session.session_id)` at `commands/mixin_base.py:39` and `repl_input_loop.py:111`), with a `sha256(auth_token)` fallback only when no session id is set — the Issue's claim is correct for the agent path only because `set_session_id` is always called; verified by code reading, confirmed by AC-3 test | False |
| UNK-03 | Issue question 3: is `ctx.workflow.current_task_id` the correct `task_id` source? | — resolved at plan time | Resolved: yes — set by the adapter (`workflow_engine_adapter.py:292`, cleared at `:300`), same source `build_turn_control_message` and the audit key use; recording is gated on it being set | False |
| UNK-04 | Issue question 4: is `retry_class(name)` the correct `retry_class` source? | — resolved at plan time | Resolved: yes — the same helper the dispatcher's dedup table class uses; enforced by REQ-006/AC-6 | False |
| UNK-05 | Untracked working-tree WIP present at plan start was wiped by concurrent git activity (reflog: 10:23 commit `a5cc49553` + rebase onto PR #4; by 10:47 the untracked files `scripts/shared/tool_http_transport.py`, `scripts/agent/workflow/recovery.py`, `tests/agent/test_tool_state_recovery_e2e.py`, `tests/agent/test_workflow_engine_e2e.py`, `tests/e2e/`, `tests/agent/workflow/test_recovery.py`, `tests/agent/workflow/test_tool_call_state_ops.py`, `tests/shared/test_tool_http_transport.py` were gone and 11 modified tracked files were reset) | Whether the deletion was intentional cleanup or lost work by the concurrent session | User confirmation of the WIP disposition; the source Issue cites some of these as "landed" (Prerequisites/Dependency Files) and they are not in committed master — no target row of this Plan depends on them, but the Issue's recovery-path references (replay tests) do | False |
| UNK-06 | How does the injection point get the `StateStore` instance — does it need a new engine accessor? | — resolved at plan time | Resolved: not needed — `WorkflowEngineAdapter.__init__` already receives `state_store: StateStore` (lines 84, 95) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_runner.py | Modify | High — every tool execution in every mode passes `_recorded_call`/`execute_one_tool_call` | 10 | 1 (single primary author) | N/A — rsynced |
| scripts/agent/context.py | Modify | Medium — shared dataclass imported across the agent layer | 12 | 1 | N/A — rsynced |
| scripts/agent/workflow_engine_adapter.py | Modify | Medium — workflow turn lifecycle | 8 | 1 | N/A — rsynced |
| tests/agent/test_tool_runner.py | Modify | Low | 11 | 1 | N/A — rsynced |
| tests/agent/test_orchestrator.py | Modify | Low | 15 | 1 | N/A — rsynced |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Modify | Low — documentation | 13 | 1 | N/A — not deployed (docs are not synced to `/opt/llm` runtime) |

## Design
- `D1` Producer location — `scripts/agent/tool_runner.py`. `_recorded_call` (lines 65-95) is the single choke point for serial groups, gathered groups, and the DAG/batch paths (all funnel through it; `execute_one_tool_call` at lines 190-234 already holds `ctx`). Record `pending` before delegating to `execute_one_tool_call`; finalize `completed` on any returned result row (including the error-row conversion at lines 87-93 — the call executed and produced its result) and `failed` on the caught-Exception conversion path. `BaseException`/`CancelledError` intentionally propagates today (lines 77-79, 83), which exactly satisfies REQ-004 crash-retention without new control flow.
- `D2` Recorder injection — `WorkflowState.tool_call_recorder: ToolCallRecorder | None` (typing-only protocol in `scripts/agent/context.py`; `StateStore` satisfies it structurally, so `context.py` gains no new import and the import contract agent→shared is untouched). The adapter sets it beside `ctx.workflow.current_task_id` (line 292) and clears it in `finally` beside the existing clear (line 300). `tool_runner` reads `ctx.workflow.tool_call_recorder` — no signature changes anywhere (`llm_turn_runner.py` untouched), which also keeps `TestBuildTurnControlMessage` and the scheduler suites unmodified.
- `D3` Key identity — re-derive at the record point: `derive_idempotency_key("call_tool", name, args, str(ctx.session.session_id))` imported from `scripts/shared/http_transport.py` (allowed: agent→shared, same pattern `toolexec001` established). Matching property: the transport's uid is the same session-id string because `set_session_id(str(session_id))` is called at both entry points; the recorded row therefore matches the dispatcher-side `mcp_dedup` row key for the same call, enabling cross-checking. The audit-only `_idempotency_key` stays as-is (REQ-009).
- `D4` State mapping — `completed` = a result row was produced (soft error results included; they already carry `error_type` in the audit event and diagnostics); `failed` = execution raised a caught Exception; `pending` = crashed/cancelled. This matches the recovery semantics: only `pending` rows feed `classify_stale_pending` → `interrupted`.
- `D5` Failure posture — recorder Exceptions are caught, logged (`logger.warning`), and never abort the call (REQ-007), mirroring `_record_transport_failure` and `tool_audit` posture; a missing row degrades to replay-allowed behavior, never to execution failure.
- `D6` Scope discipline — the helper layer, facade, schema, migrations, and shared transport/dedup are consumed as-is (REQ-010); the dispatcher-side `tool_call_state` table in `mcp_dedup.sqlite` (different schema, `key/status/snapshot_json`) is a distinct object and is not conflated with the agent-side `workflow.sqlite` table.
- Rejected alternatives: `ContextVar`-based recorder (implicit global, harder to test and reason about); wrapping execution at adapter level (loses per-call `name`/`args` needed for the key); threading a new `recorder` parameter through `execute_all_tool_calls`/`scheduler` signatures (unnecessary signature ripple since `ctx` already flows to the choke point).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Preparation (recorder contract)**
   - [ ] Add `ToolCallRecorder` protocol and `WorkflowState.tool_call_recorder` field (REQ-005; scripts/agent/context.py)
2. **Phase 2: Core Logic Implementation (producer writes)**
   - [ ] Record `pending` before dispatch and finalize `completed`/`failed` in the choke point; derive the transport-identical key and `retry_class`; non-fatal recorder errors (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-009; scripts/agent/tool_runner.py)
   - [ ] Set/clear the recorder around the workflow turn in `finally` (REQ-005; scripts/agent/workflow_engine_adapter.py)
3. **Phase 3: Test Implementation**
   - [ ] Unit tests: pending/completed/failed sequences, key identity, retry_class, crash-retention, non-fatal recorder, recorder-absent (REQ-001..REQ-008; tests/agent/test_tool_runner.py)
   - [ ] Adapter wiring tests (REQ-005, REQ-008; tests/agent/test_orchestrator.py)
4. **Phase 4: Documentation & Verification**
   - [ ] Update the tool-execution flow doc with the producer lifecycle (REQ-011; docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md)
   - [ ] Deployment validation/scripts check: N/A — no new config, schema, or service; `scripts/` is rsynced by `deploy.sh`, `config/mcp_dedup.toml` already deployed; run the full gate sequence `uv run pytest`, mypy/ruff, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run radon cc scripts/ -s -n C`, `uv run vulture scripts/ --min-confidence 80`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (all target rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_runner.py | Unit (fake recorder + real sqlite StateStore) | `uv run pytest tests/agent/test_tool_runner.py` | AC-1..AC-4, AC-6..AC-9 green |
| scripts/agent/workflow_engine_adapter.py | Integration (adapter + fake engine/turn) | `uv run pytest tests/agent/test_orchestrator.py` | AC-5 green |
| scripts/agent/context.py | Unit (via both suites) | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_orchestrator.py` | AC-5, AC-8 green |
| scripts/agent/* (regression) | Full suite | `uv run pytest` | 0 failures; existing behavior unchanged (AC-8, AC-9, AC-10) |
| Static gates | Static analysis against measured baselines | `uv run radon cc scripts/agent/tool_runner.py scripts/agent/workflow_engine_adapter.py scripts/agent/context.py -s`; `uv run vulture scripts/ --min-confidence 80`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | radon stays grade A-class at target granularity (baseline: 95 blocks, average A (2.78)); vulture finds no new dead code (baseline: 16 findings, none in target files); bandit gate clean (baseline: 0 medium/high, 51 informational low) |
| Diff coverage | diff-scoped | `uv run pytest --cov=scripts --cov-report=xml` then `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥90% on changed lines (`rules/toolchain.md` §7); baseline coverage measured 2026-11-01 on committed master: tool_runner 99%, workflow_engine_adapter 96%, workflow/state_store 78%, workflow/tool_call_state_ops 98%, workflow/workflow_engine 95%, agent TOTAL 93% |

## Risks
- **Risk**: uid mismatch between the recorded key and the transport-sent key on a code path that never calls `set_session_id` (transport would fall back to `sha256(auth_token)`) → **Mitigation**: AC-3 pins the identity with a direct derive-vs-transport equality test; both agent entry points verified as call sites (`commands/mixin_base.py:39`, `repl_input_loop.py:111`); the fallback branch is documented and out of scope.
- **Risk**: recorder lifecycle leak (exception between set and clear leaves a stale recorder on a reused `AgentContext`) → **Mitigation**: `finally`-guarded clear is part of REQ-005 and AC-5.
- **Risk**: added per-call commits on gathered fan-out add SQLite write pressure → **Mitigation**: one INSERT OR IGNORE + one UPDATE per call on the already-committed WAL store, matching the pattern `record_tool_call` already uses; measured impact limited to the two target modules' complexity gates (radon/vulture baselines above).
- **Risk**: misclassifying soft error results as `failed` would make audits misleading (the recovery path only reads `pending`, so replay safety is unaffected) → **Mitigation**: `D4` mapping is explicit and pinned by AC-2 tests.
- **Risk**: concurrent working-tree churn (UNK-05) could revert or resurrect wiped WIP files mid-implementation → **Mitigation**: implementation branches from frozen committed baseline `a7c9e4fdb`; protected-file check AC-10 catches accidental resurrection or edits of wiped-but-out-of-scope files.

## Rollback
Single-transaction rollback: `git revert` of the implementation commit(s). No schema,
migration, config, or shared-layer change exists to unwind; recorder writes are additive
rows in `workflow.sqlite` (rows can be ignored by the consumer: an empty or partial
`tool_call_state` table degrades to today's behavior — no replay hints).

## Open Issues
- UNK-05 requires user confirmation on the disposition of the wiped untracked WIP (transport client, recovery module, e2e/recovery tests). If that work is meant to be redone, it belongs to toolexec001 Phase 6 / a follow-up issue, not to this plan.
- toolexec001 Phase 6 (verification & staging check of the replay end-to-end path) stays open until this writer lands and an e2e crash→pending→interrupted→replay test exists.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: recorder contract (context.py) | In Progress | — | — | REQ-005 |
| 2 | Phase 2: producer writes (tool_runner.py, workflow_engine_adapter.py) | In Progress | — | — | REQ-001..REQ-004, REQ-006, REQ-007, REQ-009, REQ-005 |
| 3 | Phase 3: test implementation (test_tool_runner.py, test_orchestrator.py) | In Progress | — | — | AC-1..AC-9 |
| 4 | Phase 4: documentation & verification (agent_06_01 doc, full gates) | In Progress | — | — | REQ-011; deploy impact N/A (rsynced) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261101-110802_01_scripts_agent_tool_runner.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261101-110802_02_scripts_agent_context.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261101-110802_03_scripts_agent_workflow_engine_adapter.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261101-110802_04_tests_agent_test_tool_runner.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261101-110802_05_tests_agent_test_orchestrator.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261101-110802_06_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-105136
- **Related target files**: scripts/agent/tool_runner.py, scripts/agent/context.py, scripts/agent/workflow_engine_adapter.py, tests/agent/test_tool_runner.py, tests/agent/test_orchestrator.py, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement | Implementation Target File | Plan Step | Test |
|---|---|---|---|
| REQ-001 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-002 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-003 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-004 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-005 | scripts/agent/context.py; scripts/agent/workflow_engine_adapter.py | 1; 2 | tests/agent/test_orchestrator.py |
| REQ-006 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-007 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py |
| REQ-008 | scripts/agent/tool_runner.py; scripts/agent/workflow_engine_adapter.py | 2 | tests/agent/test_tool_runner.py; tests/agent/test_orchestrator.py |
| REQ-009 | scripts/agent/tool_runner.py | 2 | tests/agent/test_tool_runner.py (existing audit tests) |
| REQ-010 | N/A: constraint verified by `git diff` scope check AC-10 | 4 | N/A: scope check |
| REQ-011 | docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | 4 | N/A: documentation review |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261101-110802 -->