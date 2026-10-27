## Goal
- Make session-DB persistence for one agent turn all-or-nothing: every message write of a
  turn (user message, per-round assistant/tool messages, final assistant message, history
  compression replacement) is routed through one turn persistence boundary owned by the
  orchestrator. On any persistence failure the boundary compensates (removes the turn's
  partial DB rows) and restores `ConvState` memory to its turn-start snapshot, then raises
  `ConversationPersistenceError`. Memory and `session.sqlite` never silently diverge.

## Priority
Medium (source issue priority: P2)

## Scope
- **In-Scope**:
  - New turn persistence boundary module (`scripts/agent/turn_persistence.py`) and
    `ConversationPersistenceError`.
  - Turn-scoped compensation: DELETE of the current turn's message rows (message_id >=
    turn-start marker) in one SQLite transaction when any turn write fails.
  - Phase-grouped writes: assistant tool-call message + its tool-result messages persisted
    in a single transaction instead of separate connections/commits.
  - `ConvState` snapshot/restore for memory rollback.
  - Error wrapping: `sqlite3.Error` from session-DB writes surfaces as
    `ConversationPersistenceError`; REPL catches and surfaces it distinctly.
  - History compression write path (`replace_messages` + `undo_floor_message_id`) integrated
    with the boundary so a mid-turn compression failure is compensated like any other turn
    write.
- **Out-of-Scope**:
  - Orphan `tool_calls` repair on recovery — separate issue
    `issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md` (builds on this boundary).
  - Process-crash (kill -9 / power loss) mid-turn atomicity — compensation runs on the
    Python exception path only; crash-time partial rows are addressed by session-recovery
    (issue turn002), not here. See UNK-04.
  - `/undo` command semantics (`AgentSession.undo_last_turn`) — unchanged, but see UNK-03.
  - `cmd_rag_export*` compression scripts' direct `replace_messages` usage — kept
    backward-compatible; no behavior change required (they rebuild state from DB afterward).
  - `docs/agent/agent_architecture.md` referenced by the issue does not exist; the
    equivalent doc is updated per `docs/00_index.md` mapping (see Documentation Impact).
- **Dependencies**: Per the issue's fix order: implement this plan before or alongside the
  turn002 plan (`issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md`); turn002's
  orphan-repair builds on this boundary.

## Background
- `session.sqlite` is the single source of truth for conversation history; in-memory
  `ConvState` is rebuilt from it on session restore.
- Today each turn performs 3+ independent DB writes, each opening its own connection and
  committing separately: user message (`conversation_state_manager.append_user_message`),
  per-tool-round assistant message (`llm_turn_runner.py` L141-142) and tool results
  (`tool_round_completion.complete_round`), final assistant message
  (`workflow_engine_adapter._execute_attempt` L230), and compression replacement
  (`conversation_state_manager.handle_history_compression` L288).
- If any write fails mid-turn (DB locked, disk I/O error), earlier rows are already
  committed, later rows are missing, `ConvState` keeps the failed-turn messages, and the
  REPL's generic `except Exception` (`repl_input_loop.py` L203-206) only prints the error.
  The next turn then persists against a history that no longer matches the DB.

## Problem
- Verified against current source (issue claims corrected):
  - `ConversationPersistenceError`, `persist_compression`, and `save_assistant_message`
    named in the issue **do not exist** in the current codebase (verified across full git
    history with `rg` and `git log -S`). Raw `sqlite3.Error` propagates to the REPL's
    generic handler. The divergence failure mode the issue describes does reproduce in the
    current write sequence.
  - `complete_round` is in `scripts/agent/tool_round_completion.py`, not
    `conversation_state_manager.py`.
- Failure path today: partial rows committed → memory keeps unsaved messages → next turn's
  `fetch_messages`-based operations, session restore, `/undo`, and session stats all read a
  history inconsistent with what the agent believes.

## Reason for Change
- Session recovery (`session.load_from_db` / `fetch_messages`) and the turn002 orphan-repair
  work assume the DB is a faithful record of completed turns. Without a turn boundary,
  recovery code must guess which partial rows are trustworthy.
- High-churn core files (`orchestrator.py` 8, `context.py` 8 commits/30d) mean divergence
  bugs will keep being reintroduced until the contract is explicit.

## Implementation Intent
- Introduce a `TurnPersistence` boundary object created per turn by the orchestrator. It
  records the turn-start message marker, routes every turn write through
  `SessionMessageRepository` methods that reuse one connection and group each write phase
  into one SQLite transaction (`SQLiteHelper.begin_immediate`, already available), and on
  failure compensates by deleting the turn's rows (message_id >= turn-start) in a single
  transaction, restores `ConvState` from a turn-start snapshot, and raises
  `ConversationPersistenceError` (wrapping `sqlite3.Error`).
- Chosen mechanism: compensation + per-phase transactions (not one long-held transaction
  spanning LLM calls and tool execution — see Design for rationale).
- `SessionMessageRepository`'s existing public methods stay backward compatible
  (`cmd_rag_export*`, `session_stats`, tests keep working); new transaction-aware variants
  are added alongside.

## Requirements
- `REQ-001`: A single turn persistence boundary (`TurnPersistence`) owns all session-DB
  writes of one agent turn; it is created by the orchestrator at turn start and is the only
  path through which turn writes are persisted.
- `REQ-002`: Turn-level all-or-nothing: on any persistence failure inside a turn, the
  boundary deletes all message rows written by that turn (message_id >= turn-start marker)
  in one SQLite transaction; completed earlier phases of the failed turn leave no residue.
- `REQ-003`: All session-DB write failures in the turn path raise
  `ConversationPersistenceError` (agent-layer exception wrapping `sqlite3.Error`); no silent
  swallow and no raw `sqlite3.Error` escaping the turn path.
- `REQ-004`: After a compensated failure, `ConvState` memory equals its turn-start snapshot;
  the in-memory history matches the DB exactly.
- `REQ-005`: Multi-row write phases (assistant tool-call message + its tool-result
  messages; user message append; final assistant message) each execute in one transaction
  on one reused connection instead of separate connections/commits.
- `REQ-006`: History compression persistence stays atomic: `replace_messages` (which already
  updates `sessions.undo_floor_message_id` in its transaction) integrates with the turn
  boundary so a mid-turn compression failure is compensated like any other turn write.
- `REQ-007`: The REPL surfaces `ConversationPersistenceError` with a clear message (turn not
  persisted, history rolled back) and continues the session; subsequent turns operate on the
  consistent DB state.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/turn_persistence.py | New module: `TurnPersistence` boundary (turn-start marker, phase writes, compensation, snapshot restore) + `ConversationPersistenceError` definition | No turn boundary or persistence exception exists today | REQ-001, REQ-002, REQ-003, REQ-004 | `rg` across full history: `TurnPersistence`/`ConversationPersistenceError` absent; `begin_immediate` exists in `scripts/db/helper.py` L239 | tests/agent/test_turn_persistence.py | Verified |
| scripts/agent/session_message_repo.py | Add connection-reusing, transaction-grouped variants of save/save_many/replace_messages; wrap `sqlite3.Error` as `ConversationPersistenceError`; add compensation delete (`delete_messages_from(message_id)`) | Each save today opens its own connection + commit (L56-89, L91-129); no error wrapping | REQ-002, REQ-003, REQ-005, REQ-006 | Read: `save`/`save_many`/`replace_messages` each open `SQLiteHelper("session").open(write_mode=True)` separately | tests/agent/test_session_message_repo.py | Verified |
| scripts/agent/session.py | Expose a `turn_boundary()` factory returning a `TurnPersistence` bound to the session; keep existing facade methods behavior-compatible | `AgentSession` is the session-layer facade already imported by all turn components | REQ-001 | Read: facade already delegates to `SessionMessageRepository`; 13 importers listed in Step 3 | tests/agent/test_agent_session.py | Verified |
| scripts/agent/context.py | Add `ConvState.snapshot_messages()` and `ConvState.restore_messages(snapshot)` (lock-guarded) | ConvState owns the memory list; rollback must be atomic w.r.t. its lock (L119-134) | REQ-004 | Read: `append_message`/`replace_history` mutate `self._messages` under `self._lock`; no snapshot API | tests/agent/test_context.py | Verified |
| scripts/agent/orchestrator.py | Create the `TurnPersistence` boundary per `execute_turn`; take the memory snapshot; on `ConversationPersistenceError` run compensation + restore and re-raise | Orchestrator owns the turn lifecycle and already catches turn exceptions (L208) | REQ-001, REQ-004 | Read: `execute_turn` wraps phase 1-3 in one try block | tests/agent/test_orchestrator.py | Verified |
| scripts/agent/conversation_state_manager.py | Route user-message append and compression writes through the boundary handle; keep memory mutation semantics, rollback handled by boundary | Today appends memory then `ctx.session.save` per call (L115-118, L288) | REQ-001, REQ-005, REQ-006 | Read: `append_user_message` L115-118; `handle_history_compression` L288 | tests/agent/test_history_compression_consistency.py | Verified |
| scripts/agent/llm_turn_runner.py | Persist the assistant tool-call message via the boundary instead of `ctx.session.save` (L142) | Per-round separate commit is one of the partial-write sources | REQ-001, REQ-005 | Read: L141-142 `append_message` + `ctx.session.save("assistant", ...)` | tests/agent/llm_turn_runner 用例は tests/agent/test_llm_turn_runner.py | Verified |
| scripts/agent/tool_round_completion.py | Persist tool-result messages via the boundary, grouped in one phase transaction with the round's assistant message (L86) | `save_many` currently commits separately from the assistant save moments earlier | REQ-001, REQ-005 | Read: `complete_round` L86 `ctx.session.save_many(tool_messages)` | tests/agent/test_tool_round_completion.py | Verified |
| scripts/agent/workflow_engine_adapter.py | Persist the final assistant message via the boundary instead of `ctx.session.save` (L230) | Final-answer save is the last independent commit of the turn | REQ-001, REQ-005 | Read: `_execute_attempt` L230 | tests/agent/test_llm_turn_runner.py 経由で間接カバレッジ；既存 workflow テストで回帰確認 | Verified |
| scripts/agent/repl_input_loop.py | Catch `ConversationPersistenceError` before generic `Exception` (L203-206) and surface a distinct "turn not persisted, history rolled back" message | Generic handler cannot distinguish persistence failures from other turn errors | REQ-007 | Read: `_repl_loop` generic except → `_surface_turn_error` | tests/agent/test_repl_error_handling.py | Verified |
| tests/agent/test_turn_persistence.py | New test module: boundary commit, compensation on injected failure, exception type, snapshot restore | No test exists for turn-level atomicity (none today) | REQ-001..REQ-004 | New file; name collision checked (`ls scripts/agent tests/agent`) | — | Verified |
| tests/agent/test_session_message_repo.py | Extend: transaction-grouped variants, compensation delete, `ConversationPersistenceError` wrapping | Existing tests cover per-method behavior only | REQ-002, REQ-003, REQ-005 | Exists; current cases enumerate per-method save/fetch | — | Verified |
| tests/agent/test_history_compression_consistency.py | Extend: mid-turn compression failure compensated; memory restored; `undo_floor` consistent | Existing tests cover successful compression consistency only | REQ-004, REQ-006 | Exists: `replace_messages` already updates `undo_floor_message_id` atomically | — | Verified |
| tests/agent/test_llm_turn_runner.py | Update mocks/expectations for boundary-routed persistence | Write path signature/routing changes in runner | REQ-005 | Exists (Step 3 test inventory) | — | Verified |
| tests/agent/test_tool_round_completion.py | Update mocks/expectations for boundary-routed persistence | Write path changes in `complete_round` | REQ-005 | Exists (Step 3 test inventory) | — | Verified |
| tests/agent/test_agent_session.py | Extend: `turn_boundary()` factory behavior | New facade method | REQ-001 | Exists (Step 3 test inventory) | — | Verified |
| tests/agent/test_orchestrator.py | Extend: failure-injection at a turn write → compensation + restore + re-raise | Turn lifecycle behavior change | REQ-001, REQ-004 | Exists (Step 3 test inventory) | — | Verified |
| tests/agent/test_context.py | Extend: `snapshot_messages`/`restore_messages` semantics incl. lock behavior | New ConvState API | REQ-004 | Exists (Step 3 test inventory) | — | Verified |
| tests/agent/test_repl_error_handling.py | Extend: `ConversationPersistenceError` surfaced distinctly, loop continues | New REPL error branch | REQ-007 | Exists (Step 3 test inventory) | — | Verified |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Document the turn persistence boundary contract: all-or-nothing turn writes, `ConversationPersistenceError`, compensation semantics, memory-rollback rule | New architectural contract for session state/persistence | REQ-001, REQ-003, REQ-004 | `docs/23_agent/agent_00_document-guide.md` maps "persistence vs memory state" to agent_04; file exists | N/A: documentation only | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/helper.py | `begin_immediate`/`begin_exclusive`/`_begin_transaction` (L219-236) and `open(reuse_connection=...)` are the transaction primitives the boundary reuses; MUST NOT be modified | scripts/agent/turn_persistence.py; REQ-002, REQ-005 |
| scripts/db/schema_sql.py | `sessions`/`messages` schema incl. `undo_floor_message_id` (L94-100); confirms no schema change is needed | scripts/agent/session_message_repo.py; REQ-002, REQ-006 |
| scripts/cli/cmd_rag_export.py | Downstream consumer of `replace_messages` that must keep working unchanged | scripts/agent/session_message_repo.py; REQ-006 |
| scripts/agent/llm_transport_errors.py | Project convention for subsystem-local error modules; model for `ConversationPersistenceError` placement | scripts/agent/turn_persistence.py; REQ-003 |
| tests/integration/test_session_recovery.py | Existing end-to-end recovery behavior that must not regress | scripts/agent/orchestrator.py; REQ-002 |
| docs/00_index.md | Task-scope mapping for the documentation row | docs/23_agent/agent_04_01_state-and-persistence-state-model.md |

## Acceptance Criteria
- `AC-001` (REQ-001): Grep-enforced: no turn-path component calls `ctx.session.save*` or
  `SessionMessageRepository` write methods directly during `execute_turn`; all writes go
  through the boundary object.
- `AC-002` (REQ-002): Injecting a `sqlite3.Error` at any single turn write leaves zero
  message rows from that turn in `session.sqlite` (compensation delete verified in tests).
- `AC-003` (REQ-003): Every persistence-failure test asserts `ConversationPersistenceError`
  is raised; no test path exposes a raw `sqlite3.Error` from the turn write path.
- `AC-004` (REQ-004): After a compensated failure, `ConvState.messages` equals the
  turn-start snapshot (element-wise) and equals `fetch_messages()` output.
- `AC-005` (REQ-005): A tool round's assistant + tool-result rows are written in one
  transaction on one connection (verified by test using a single injected failure point
  leaving either all or none of the round's rows).
- `AC-006` (REQ-006): A compression failure mid-turn leaves DB rows and
  `sessions.undo_floor_message_id` at their pre-turn values and memory restored.
- `AC-007` (REQ-007): REPL test shows a distinct persistence-error message and the loop
  continues with a consistent state; existing REPL error tests still pass.
- `AC-008` (all): Existing session/recovery/compression test suites
  (`test_session_recovery.py`, `test_history_compression_consistency.py`,
  `test_regression_history_compress_reload.py`, `test_session_message_repo.py`) pass
  unchanged except where the plan explicitly extends them; `import-linter` contract still
  passes.

## Tests
- `test_turn_persistence.py` (new): boundary happy path; injected failure at each phase
  (user append, round N, final save, compression) → compensation deletes exactly the turn's
  rows, `ConversationPersistenceError` raised, memory restored (REQ-001..REQ-005).
- `test_session_message_repo.py`: grouped-transaction variants commit atomically;
  compensation delete; `sqlite3.Error` → `ConversationPersistenceError` wrapping (REQ-002,
  REQ-003, REQ-005).
- `test_history_compression_consistency.py`: compression-failure compensation keeps
  `undo_floor_message_id`, messages, and memory mutually consistent (REQ-004, REQ-006).
- `test_llm_turn_runner.py`, `test_tool_round_completion.py`: boundary-routed persistence
  mocks; a failed round leaves no partial round rows (REQ-005).
- `test_orchestrator.py`: turn-level failure injection → compensation + restore + re-raise
  (REQ-001, REQ-004).
- `test_context.py`: snapshot/restore correctness including concurrent-mutation safety
  (REQ-004).
- `test_repl_error_handling.py`: distinct surfacing and loop continuation (REQ-007).
- Regression: full `uv run pytest` suite, especially
  `tests/integration/test_session_recovery.py` and
  `tests/agent/test_regression_history_compress_reload.py` (AC-008).

## Documentation Impact
- Yes. Per `docs/00_index.md` "Session / DB persistence" and
  `docs/23_agent/agent_00_document-guide.md` (persistence vs memory state → chapter 04),
  the state/persistence doc (`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`,
  Implementation Target Files row) must document the turn boundary contract, compensation
  semantics, and `ConversationPersistenceError` — driven by REQ-001, REQ-003, REQ-004.
  Run `tools/check_doc_claims.py` after the doc edit per `routing.md`.

## Assumptions
- Compensation (application-level delete + memory restore) is acceptable turn atomicity;
  a single SQLite transaction held across the whole turn (LLM calls + tool execution) is
  rejected — rationale in Design. UNK-01 records the residual decision for the design step.
- Only the REPL/orchestrator writes `messages` rows for a given session during a turn
  (verified: no agent processes or session-DB writers running now; `fuser
  /opt/llm/db/session.sqlite` empty at analysis time 2026-10-27).
- Existing public `SessionMessageRepository` API stays backward compatible for
  `cmd_rag_export*` and stats consumers.
- No schema change is required (turn marker is computed from `message_id`, not stored;
  `scripts/db/schema_sql.py` unchanged) — confirmed by reading schema.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Final write-grouping granularity: per-phase transactions + turn compensation (planned) vs one deferred transaction per turn committed at phase points | Runtime trade-off not measured: lock hold time under real tool execution durations | Confirm during implementation-design step (`python-design`); Phase 1 tests pin the chosen granularity | False |
| UNK-02 | Turn-start marker robustness on a fresh session (first turn, no rows) and after a compensated failure (message_id gaps) | None yet observed; edge behavior of `max(message_id)` needs test coverage | Covered by new edge-case tests in `test_turn_persistence.py` | False |
| UNK-03 | Interaction of turn compensation with `/undo` semantics: compensation deletes only current-turn rows; must not bypass/confuse the `undo_floor_message_id` gate | Issue does not specify; `undo_last_turn` (session.py L204-249) is the closest existing mechanism | Design decision at implementation; document alongside boundary contract | False |
| UNK-04 | Process-crash (no Python exception) mid-turn leaves uncompensated partial rows; whether startup-time consistency check is needed | Not covered by any current recovery code; issue turn002 scope boundary | Decide in the turn002 plan (session recovery); record as follow-up if it stays out | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/turn_persistence.py | New module | New file; imported by orchestrator/session only | 0 (new) | N/A (new) | New file synced by `deploy/deploy.sh` scripts copy — verify in Phase 3 |
| scripts/agent/session_message_repo.py | Add variants + error wrapping | 7 importers incl. `cmd_rag_export*`, `cmd_rag_export_session*` | 3 | 1 (dominant author >70%) | File sync |
| scripts/agent/session.py | Add facade method | 13 importers across agent/cli/tests | 5 | 1 (dominant author >70%) | File sync |
| scripts/agent/context.py | Add snapshot/restore | `ConvState` used by nearly all agent modules | 8 | 1 (dominant author >70%) | File sync |
| scripts/agent/orchestrator.py | Turn boundary integration | Hub: imported by repl/cmd_agent/tests; imports 12+ modules | 8 | 1 (dominant author >70%) | File sync |
| scripts/agent/conversation_state_manager.py | Route writes through boundary | Owned by orchestrator; used by cmd_agent | 2 | 1 (dominant author >70%) | File sync |
| scripts/agent/llm_turn_runner.py | Write routing change | Imported by orchestrator + tests | 3 | 1 (dominant author >70%) | File sync |
| scripts/agent/tool_round_completion.py | Write routing change | Imported by orchestrator + tests | 2 | 1 (dominant author >70%) | File sync |
| scripts/agent/workflow_engine_adapter.py | Write routing change | Imported by orchestrator + tests | 5 | 1 (dominant author >70%) | File sync |
| scripts/agent/repl_input_loop.py | New except branch | REPL core loop (`_repl_loop` is CC D(30) — do not restructure here) | 6 | 1 (dominant author >70%) | File sync |

## Design
- Mechanism (grounded in Step 5/7 analysis):
  - `TurnPersistence` created per turn by the orchestrator via
    `AgentSession.turn_boundary()`. It holds the turn-start marker (max existing
    `message_id` for the session at turn start; 0 for a fresh session), a `ConvState`
    snapshot, and one reused `SQLiteHelper("session")` write connection.
  - Each persistence phase (user append / assistant+tool round / final assistant /
    compression replace) runs inside `SQLiteHelper.begin_immediate` on the reused
    connection (existing primitive, `helper.py` L219-236 already rolls back on any
    exception and re-raises).
  - On failure of any phase (or any later turn failure that must not persist): compensation
    = DELETE of `messages` rows `message_id >= turn_start` for this session in one
    transaction (mirrors `undo_last_turn`'s message_id-based delete, `session.py`
    L235-242), then `ConvState.restore_messages(snapshot)`, then raise
    `ConversationPersistenceError` (wraps `sqlite3.Error`; defined in
    `turn_persistence.py` per the subsystem-local error-module convention of
    `llm_transport_errors.py`).
  - Rejected alternative: one transaction spanning the whole turn — SQLite WAL write lock
    would be held across LLM calls and tool executions (seconds to minutes; bash/subagent
    tools can run minutes), blocking concurrent writers to `session.sqlite` and losing
    already-completed rounds on crash; busy_timeout is finite. Compensation preserves
    per-phase durability while still guaranteeing turn all-or-nothing on the failure path.
- Step 5 baseline: radon CC on targets has no D-rank in the files to be modified
  (highest B(10) `workflow_engine_adapter._run_execute_stage`); `repl_input_loop._repl_loop`
  is D(30) but only a new except branch is added there — no restructuring. vulture
  (min-confidence 80) and bandit clean on session-layer files. MyPy strictness config:
  `python_version 3.13`, `warn_return_any`, `warn_unused_ignores` (pyproject). diff-cover:
  no diff at planning time; run in Phase 3 after implementation.
- Operational dependency state (Step 7): no agent processes running; `fuser` on
  `/opt/llm/db/session.sqlite` (from `config/agent.toml`) returned nothing; no schema
  migration tooling exists (schema lives in `scripts/db/schema_sql.py`); no external
  services involved.

## Implementation steps
1. **Phase 1: Persistence boundary foundation**
   - [ ] Create `TurnPersistence` + `ConversationPersistenceError` (REQ-001, REQ-002,
     REQ-003, REQ-004; scripts/agent/turn_persistence.py)
   - [ ] Add transaction-grouped variants, compensation delete, and error wrapping in the
     repository (REQ-002, REQ-003, REQ-005, REQ-006; scripts/agent/session_message_repo.py)
   - [ ] Add `turn_boundary()` facade factory (REQ-001; scripts/agent/session.py)
   - [ ] Add `snapshot_messages`/`restore_messages` to `ConvState` (REQ-004;
     scripts/agent/context.py)
   - [ ] Unit tests for boundary, repo variants, snapshot (REQ-001..REQ-005;
     tests/agent/test_turn_persistence.py, tests/agent/test_session_message_repo.py,
     tests/agent/test_context.py, tests/agent/test_agent_session.py)
2. **Phase 2: Turn-flow integration**
   - [ ] Orchestrator creates the boundary per turn, snapshot + compensation on failure
     (REQ-001, REQ-004; scripts/agent/orchestrator.py)
   - [ ] Route user-append and compression writes through the boundary (REQ-001, REQ-005,
     REQ-006; scripts/agent/conversation_state_manager.py)
   - [ ] Route assistant/tool/final saves through the boundary, grouping each round into
     one phase transaction (REQ-001, REQ-005; scripts/agent/llm_turn_runner.py,
     scripts/agent/tool_round_completion.py, scripts/agent/workflow_engine_adapter.py)
   - [ ] REPL catches `ConversationPersistenceError` distinctly and continues (REQ-007;
     scripts/agent/repl_input_loop.py)
   - [ ] Update/extend integration-level tests (REQ-001..REQ-007;
     tests/agent/test_orchestrator.py, tests/agent/test_llm_turn_runner.py,
     tests/agent/test_tool_round_completion.py, tests/agent/test_history_compression_consistency.py,
     tests/agent/test_repl_error_handling.py)
3. **Phase 3: Verification & documentation**
   - [ ] Run targeted tests, then full suite, mypy, ruff, bandit, import-linter, diff-cover
     (AC-008; per `rules/toolchain.md`)
   - [ ] Deployment/scripts check: confirm `deploy/deploy.sh` syncs the new module and
     `init_db.sh`/`schema_sql.py` remain untouched (no schema change) (all REQ)
   - [ ] Update the state/persistence doc with the boundary contract and run
     `tools/check_doc_claims.py` (REQ-001, REQ-003, REQ-004;
     docs/23_agent/agent_04_01_state-and-persistence-state-model.md)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/turn_persistence.py | Unit: phase success, failure injection at every phase | `uv run pytest tests/agent/test_turn_persistence.py` | All-or-nothing per turn; `ConversationPersistenceError` on every injected DB failure |
| scripts/agent/session_message_repo.py | Unit: grouped transactions, compensation delete, error wrapping | `uv run pytest tests/agent/test_session_message_repo.py` | No partial phase rows; wrapped errors |
| scripts/agent/context.py | Unit: snapshot/restore incl. concurrent access | `uv run pytest tests/agent/test_context.py` | Snapshot equals restore; lock safety |
| scripts/agent/orchestrator.py + turn components | Integration: failure injection through real turn | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_session_recovery.py` | Memory == DB after failure; recovery unaffected |
| scripts/agent/repl_input_loop.py | Unit: error surfacing | `uv run pytest tests/agent/test_repl_error_handling.py` | Distinct message; loop continues |
| All targets | Static + regression | `uv run pytest`, `uv run mypy scripts/`, `uv run ruff check scripts/`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run lint-imports`, `diff-cover` after Phase 2 | Clean; no new findings; import contract preserved |

## Risks
- **Risk**: Compensation DELETE removes `messages` rows `message_id >= turn_start` — if any
  other component wrote rows for the same session mid-turn they would be removed too.
  → **Mitigation**: verified assumption that only the turn path writes session message rows
  during a turn (no other session-DB writers observed); documented boundary rule "no direct
  message writes outside the boundary during a turn"; covered by AC-001 grep check.
- **Risk**: Hot-file collisions with sibling plans in the same batch —
  `orchestrator.py`/`llm_turn_runner.py`/`repl_input_loop.py` are also touched by
  history001/sess007/sess008-area issues. → **Mitigation**: this plan freezes first (issue
  declares fix order); `check_plan_target_overlaps.py` run at each later plan's freeze;
  implement this plan before overlapping ones.
- **Risk**: Process killed mid-turn (no exception) still leaves partial rows; compensation
  does not run. → **Mitigation**: residual gap explicitly scoped to turn002 (startup
  orphan/consistency repair); UNK-04 tracked.
- **Risk**: Bus factor 1 on every target file (dominant author >70%); single reviewer
  bottleneck. → **Mitigation**: strong test coverage in Phase 1 before touching hot files;
  characterization-style regression tests listed in AC-008.
- **Risk**: `repl_input_loop._repl_loop` is a complexity hotspot (CC D(30)); careless edit
  could worsen it. → **Mitigation**: change limited to adding one except branch before the
  generic handler; no restructuring in this plan (per project policy against unrelated
  refactors).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Persistence boundary foundation | Pending | — | — | |
| 2 | Phase 2: Turn-flow integration | Pending | — | — | Blocked by Phase 1 completion |
| 3 | Phase 3: Verification & documentation | Pending | — | — | |

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
- **Source issue**: issues/20261026-224643_turn001_atomic-turn-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-070403
- **Related target files**: scripts/agent/turn_persistence.py,
  scripts/agent/session_message_repo.py, scripts/agent/session.py, scripts/agent/context.py,
  scripts/agent/orchestrator.py, scripts/agent/conversation_state_manager.py,
  scripts/agent/llm_turn_runner.py, scripts/agent/tool_round_completion.py,
  scripts/agent/workflow_engine_adapter.py, scripts/agent/repl_input_loop.py,
  tests/agent/test_turn_persistence.py, tests/agent/test_session_message_repo.py,
  tests/agent/test_history_compression_consistency.py, tests/agent/test_llm_turn_runner.py,
  tests/agent/test_tool_round_completion.py, tests/agent/test_agent_session.py,
  tests/agent/test_orchestrator.py, tests/agent/test_context.py,
  tests/agent/test_repl_error_handling.py,
  docs/23_agent/agent_04_01_state-and-persistence-state-model.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Failure Path Analysis, Required Actions 1 | scripts/agent/turn_persistence.py | Phase 1 | AC-001 | test_turn_persistence.py | Derived from confirmed evidence |
| REQ-001 | Required Actions 1 | scripts/agent/orchestrator.py | Phase 2 | AC-001 | test_orchestrator.py | Derived from confirmed evidence |
| REQ-001 | Required Actions 1 | scripts/agent/session.py | Phase 1 | AC-001 | test_agent_session.py | Derived from confirmed evidence |
| REQ-001 | Required Actions 1 | scripts/agent/conversation_state_manager.py | Phase 2 | AC-001 | test_history_compression_consistency.py | Derived from confirmed evidence |
| REQ-001 | Required Actions 1 | scripts/agent/llm_turn_runner.py | Phase 2 | AC-001 | test_llm_turn_runner.py | Confirmed by repository evidence (L141-142) |
| REQ-001 | Required Actions 1 | scripts/agent/tool_round_completion.py | Phase 2 | AC-001 | test_tool_round_completion.py | Confirmed by repository evidence (L86) |
| REQ-001 | Required Actions 1 | scripts/agent/workflow_engine_adapter.py | Phase 2 | AC-001 | test_llm_turn_runner.py | Confirmed by repository evidence (L230) |
| REQ-001 | Required Actions 5 | docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Phase 3 | AC-001 | N/A: documentation check via check_doc_claims.py | Explicit in issue |
| REQ-002 | Failure Mode, Required Actions 2 | scripts/agent/turn_persistence.py | Phase 1 | AC-002 | test_turn_persistence.py | Explicit in issue |
| REQ-002 | Required Actions 2 | scripts/agent/session_message_repo.py | Phase 1 | AC-002 | test_session_message_repo.py | Derived from confirmed evidence |
| REQ-003 | Failure Path Analysis, Required Actions 3 | scripts/agent/turn_persistence.py | Phase 1 | AC-003 | test_turn_persistence.py | Explicit in issue (exception type name corrected: symbol absent in code today) |
| REQ-003 | Error Handling (raw sqlite3.Error today) | scripts/agent/session_message_repo.py | Phase 1 | AC-003 | test_session_message_repo.py | Confirmed by repository evidence |
| REQ-003 | Required Actions 3 | scripts/agent/repl_input_loop.py | Phase 2 | AC-003, AC-007 | test_repl_error_handling.py | Confirmed by repository evidence (L203-206) |
| REQ-004 | Failure Mode (memory/DB divergence), Required Actions 4 | scripts/agent/context.py | Phase 1 | AC-004 | test_context.py | Derived from confirmed evidence |
| REQ-004 | Required Actions 4 | scripts/agent/orchestrator.py | Phase 2 | AC-004 | test_orchestrator.py | Derived from confirmed evidence |
| REQ-004 | Failure Path Analysis | scripts/agent/conversation_state_manager.py | Phase 2 | AC-004 | test_history_compression_consistency.py | Confirmed by repository evidence (L115-118, L288) |
| REQ-005 | Failure Path Analysis (3+ independent writes), Required Actions 2 | scripts/agent/session_message_repo.py | Phase 1 | AC-005 | test_session_message_repo.py | Confirmed by repository evidence |
| REQ-005 | Failure Path Analysis | scripts/agent/llm_turn_runner.py | Phase 2 | AC-005 | test_llm_turn_runner.py | Confirmed by repository evidence |
| REQ-005 | Failure Path Analysis | scripts/agent/tool_round_completion.py | Phase 2 | AC-005 | test_tool_round_completion.py | Confirmed by repository evidence |
| REQ-005 | Failure Path Analysis | scripts/agent/workflow_engine_adapter.py | Phase 2 | AC-005 | N/A: covered via test_llm_turn_runner.py + workflow regression suite | Confirmed by repository evidence |
| REQ-005 | Failure Path Analysis (user append) | scripts/agent/conversation_state_manager.py | Phase 2 | AC-005 | test_history_compression_consistency.py | Confirmed by repository evidence |
| REQ-006 | Affected Modules (History Compression); replace_messages already atomic in one transaction | scripts/agent/session_message_repo.py | Phase 1 | AC-006 | test_history_compression_consistency.py | Confirmed by repository evidence |
| REQ-006 | Affected Modules (History Compression) | scripts/agent/conversation_state_manager.py | Phase 2 | AC-006 | test_history_compression_consistency.py | Confirmed by repository evidence |
| REQ-007 | Required Actions 3 (explicit persistence error handling) | scripts/agent/repl_input_loop.py | Phase 2 | AC-007 | test_repl_error_handling.py | Derived from confirmed evidence |
