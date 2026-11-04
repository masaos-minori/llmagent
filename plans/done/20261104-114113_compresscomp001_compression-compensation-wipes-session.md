## Goal
- Make turn compensation correct for a turn that compressed the history: when a write fails after the compression rewrite, the session's persisted rows, its `/undo` boundary, and `conv.history` all return to their turn-start values instead of the whole session being deleted.

## Priority
High

## Scope
- **In-Scope**:
  - Capture a pre-rewrite image of the session's rows and `undo_floor_message_id` immediately before the compression rewrite, inside the turn-persistence boundary.
  - Compensation after a rewrite restores that image in one transaction (rows at or below the turn-start marker, with their original `message_id` and `created_at`, plus the `/undo` boundary) instead of deleting rows above the marker.
  - The boundary also restores `conv.undo_floor` to its turn-start value together with `conv.history`.
  - Tests with a real temporary SQLite database, repository tests for the new methods, and the documentation of the compensation guarantee.
- **Out-of-Scope**:
  - Changing when or how compression is triggered, the compression algorithm, or the schema of `messages` and `sessions`.
  - The `/compact` command's own use of `replace_messages` (it runs outside a turn boundary).
  - Restoring a session's compression summary on load (tracked separately).
  - The append-only compensation path (`delete_messages_from`), which stays as it is.
- **Dependencies**: N/A: none. The archived atomic-turn-persistence plan is history only. The session-restore issue (id restoresummary001) concerns what the database holds after compression and is independent in fix order; its tests should reflect the persisted-row rules, not this Plan's restore path.

## Background
The turn-persistence boundary compensates a failed turn by deleting every row with `message_id` above the marker captured at turn start (`MAX(message_id)`). That primitive is correct for appended rows. The compression rewrite (`replace_messages`) deletes all rows of the session and inserts the compressed set, and `messages.message_id` is `AUTOINCREMENT`, so every re-inserted row is above the marker. In a turn the user message is appended through the boundary, then `handle_history_compression` rewrites the session through the boundary, and the tool rounds and the final assistant message are appended afterward (checked in Step 2).

## Problem
After a successful compression, a failing later boundary write runs the compensation delete, which matches every re-inserted row. The session ends with zero persisted rows while `conv.history` is restored to the old uncompressed snapshot (checked in Step 2 by reading `TurnPersistence._fail_from_error`, `SessionMessageRepository.replace_messages`, and `delete_messages_from`; the Issue's own throwaway reproduction showed marker 6, ids 7 to 9, 0 rows left).

Verification corrections and findings:
1. Re-reading the code shows a second inconsistency the Issue does not name: `ConversationStateManager.handle_history_compression` sets `ctx.conv.undo_floor` in memory after the rewrite, but `ConversationState.restore_messages` restores only the history list, so after a compensated failure the in-memory `undo_floor` stays at the compressed length while the history is back to the uncompressed snapshot. The database `undo_floor_message_id` is also left at the post-rewrite boundary because the rewrite updated it in its transaction.
2. `messages` has a `created_at` column; a faithful restore must capture it, not only role, content, tool calls, and tool call id. No other table references `messages.message_id` (schema read in Step 3), so a delete-and-reinsert restore has no dependent rows to lose.
3. The existing test for a failing compression write patches `SessionMessageRepository.replace_messages` by name. The rewrite itself is already atomic (one transaction; a failure rolls back), and compensating it with `delete_messages_from` is correct. Keeping the `replace_messages` name and signature therefore keeps that test meaningful.
4. `ConversationStateManager` needs no change: the boundary encapsulates the rewrite, so the Issue's listed `conversation_state_manager.py` is a reference file, not a target.
5. The compression rewrite runs at most once per turn in the code read (`_prepare_turn_input` path); the design still keeps only the first captured image so a repeated rewrite cannot overwrite the turn-start state.

## Reason for Change
This is silent loss of the user's whole persisted conversation, triggered by a transient database error in a turn that happened to compress. The atomicity feature exists to prevent this class of loss, so it must not cause it.

## Implementation Intent
Choose mechanism (b) of the Issue's options: capture what is needed to undo the rewrite before it happens. Alternatives rejected: one transaction across the turn (the turn's writes use several connections and worker-thread calls; a rewrite of that scope is large) and deferring the rewrite to turn end (the rewrite would then include this turn's rows, moving the `/undo` boundary and changing `/undo` semantics, which the Issue forbids). The append-only path keeps its current behavior and cost because no image is captured unless a rewrite runs.

## Requirements
- `REQ-001`: When a turn's compression rewrite has succeeded and a later write fails, compensation MUST restore the session's persisted rows to their turn-start content (same `message_id` and `created_at`, rows at or below the turn-start marker only) and `sessions.undo_floor_message_id` to its pre-rewrite value.
- `REQ-002`: The restore MUST run in one transaction and MUST fail safe: if it fails, the rows present stay untouched, the error is logged, and the boundary MUST NOT fall back to the delete-above-marker compensation; the original persistence error is still raised.
- `REQ-003`: After a compensated failure, `conv.history` and `conv.undo_floor` MUST equal their turn-start values and the persisted rows MUST agree with `conv.history`.
- `REQ-004`: A turn without a rewrite MUST keep the current compensation (delete rows above the marker) with no pre-image capture; a failing compression write itself MUST keep its current compensation; the `/undo` boundary MUST stay consistent with the surviving rows.
- `REQ-005`: Tests with a real temporary SQLite database MUST compress, inject a failing later write, and assert the rows equal the turn-start rows, equal `conv.history`, and the boundary equals its pre-turn value; they MUST fail on the pre-change code and pass after it; the existing failing-compression-write test MUST be kept.
- `REQ-006`: The documentation MUST state the compensation guarantee after a turn that compressed (what the database holds after a failed turn).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/session_message_repo.py` | Pre-image capture and restore | Add a read that captures the session's rows (id, role, content, tool calls, tool call id, `created_at`) and `undo_floor_message_id`, and a one-transaction restore that deletes the session's rows, re-inserts the image rows at or below the marker with their ids, and resets the boundary; `replace_messages` and `delete_messages_from` stay unchanged (checked in Step 2) | REQ-001, REQ-002, REQ-004; AC-1, AC-2, AC-4 | `replace_messages` deletes all rows and re-inserts in one transaction and updates the boundary; `delete_messages_from` deletes `message_id > marker`; the module is 15453 bytes, under the 20480 size gate with room for two methods (checked in Step 2) | `tests/agent/test_session_message_repo.py`, `tests/agent/test_history_compression_consistency.py` | Verified |
| `scripts/agent/turn_persistence.py` | Boundary compensation | In `replace_messages`, capture the pre-image before the rewrite in the same worker-thread call and keep the first one after the rewrite succeeds; in `_compensate`, restore the image instead of deleting above the marker; fail safe when the restore fails; store `conv.undo_floor` at construction and restore it with the history (checked in Step 2) | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4 | `replace_messages` offloads the repository call with `asyncio.to_thread`; `_compensate` always deletes above the marker; `_fail_from_error` restores only `conv.history` via `restore_messages` (checked in Step 2) | `tests/agent/test_turn_persistence.py`, `tests/agent/test_history_compression_consistency.py` | Verified |
| `tests/agent/test_history_compression_consistency.py` | Real-database failing test | Add the compress-then-fail test with the real boundary and the real repository on the file's patched in-memory database, asserting rows, boundary, `conv.history`, and `conv.undo_floor`; keep `test_compression_failure_restores_pre_turn_state` (checked in Step 2) | REQ-005; AC-5, AC-6 | The file has the `session_and_conn` fixture, a `_TurnBoundaryStub`, and a failing-compression test that patches `SessionMessageRepository.replace_messages` (checked in Step 2) | `tests/agent/test_history_compression_consistency.py` | Verified |
| `tests/agent/test_turn_persistence.py` | Boundary unit tests | Add tests for restore-after-rewrite, the first-image-only rule, the fail-safe path (restore failure does not delete), the append-only path unchanged, and `conv.undo_floor` restoration (checked in Step 2) | REQ-002, REQ-003, REQ-004; AC-2, AC-3, AC-4 | The file exercises the boundary's save, replace, compensation, and error paths (checked in Step 2) | `tests/agent/test_turn_persistence.py` | Verified |
| `tests/agent/test_session_message_repo.py` | Repository tests | Add tests that the captured image round-trips ids and `created_at`, that the restore resets the boundary, and that a failing restore leaves the rows untouched (checked in Step 2) | REQ-001, REQ-002; AC-1, AC-2 | The file has `TestReplaceMessages`-style tests for `replace_messages` against a patched database (checked in Step 2) | `tests/agent/test_session_message_repo.py` | Verified |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Compensation guarantee | Update the "Turn Persistence Boundary" compensation bullet: after a turn that compressed, the rows return to their turn-start content and boundary, not only rows above the marker are removed (checked in Step 2) | REQ-006; AC-7 | The bullet states only rows with `message_id` above the marker are removed, which is false after a rewrite (checked in Step 2) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/conversation_state_manager.py` | `handle_history_compression` routes the rewrite through the boundary and sets `conv.undo_floor` afterward; stays unchanged | REQ-003 |
| `scripts/agent/session.py` | `turn_boundary` captures the marker and the history snapshot; the facade `replace_messages` is used outside a turn | REQ-001 |
| `scripts/agent/context.py` | `ConversationState.restore_messages` restores history only; `undo_floor` field definition | REQ-003 |
| `scripts/db/schema_sql.py` | `messages` columns and foreign keys (no table references `message_id`); `sessions.undo_floor_message_id` | REQ-001 |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | States `replace_messages` updates the boundary in the same transaction; stays true | REQ-006 |
| `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Compression persistence model; stays true | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): a turn that compresses and then fails a later write leaves the session's persisted rows identical to the turn-start rows (ids, role, content, tool calls, tool call id, `created_at`), never empty.
- AC-2 (REQ-002): when the restore itself fails, no row is deleted by the boundary and the original persistence error is raised.
- AC-3 (REQ-003): `conv.history` equals the turn-start snapshot, `conv.undo_floor` equals its turn-start value, and the persisted rows agree with `conv.history`.
- AC-4 (REQ-004): an append-only failed turn still deletes only rows above the marker and captures no image; the existing failing-compression-write test passes unchanged.
- AC-5 (REQ-005): the new real-database test fails on the pre-change code and passes after the change.
- AC-6 (REQ-004): the persisted `undo_floor_message_id` equals its pre-turn value after a compensated failure.
- AC-7 (REQ-006): the persistence-model document states the guarantee and the docs checkers report no findings, with no concrete values copied.

## Tests
- `REQ-005`: in `tests/agent/test_history_compression_consistency.py`, six prior rows, the real boundary at turn start, a real compression rewrite, then a failing later `save_phase_grouped` (injected `sqlite3.OperationalError`); assert rows equal turn-start rows, equal `conv.history`, boundary and `conv.undo_floor` at their pre-turn values.
- `REQ-002`, `REQ-003`, `REQ-004`: boundary unit tests in `tests/agent/test_turn_persistence.py` (restore after rewrite, first image only, restore failure leaves rows and still raises the persistence error, append-only path).
- `REQ-001`, `REQ-002`: repository tests in `tests/agent/test_session_message_repo.py` (round-trip of ids and `created_at`, boundary reset, failing restore leaves rows).
- Tests use a temporary or patched database only and never the real session database.
- Regression: `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_turn_persistence.py`, `tests/agent/test_session_message_repo.py`, the undo tests (`rg -l undo tests/agent`), `tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`.

## Documentation Impact
Yes. REQ-006 drives an update of the state and persistence model document (the "Turn Persistence Boundary" section), located through the scan and `docs/00_index.md` "Document References by Task". No concrete values.

## Assumptions
- A single writer owns a session during a turn (the REPL runs turns serially), so the image read just before the rewrite equals the persisted turn-start rows plus this turn's appended rows; rows at or below the marker are unchanged by append-only writes (read in Step 3).
- The in-memory snapshot already equals the turn-start rows for a session that was not loaded with validation drops; a divergence there is the separate restore issue, not this Plan.
- Capturing the whole session image only when a rewrite runs is acceptable in memory: a rewrite happens only after the history exceeded the compression limit and at most once per turn.
- Overlap with other Frozen Plans is judged by `tools/check_plan_target_overlaps.py` in Step 8b.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a new class or public symbol in `session_message_repo.py` appears in the generated agent reference document and so makes `tools/generate_reference_table.py --check` report drift. | The generator output for the new symbols was not run before the change. | Implementer runs the check in Phase 5; if it drifts, amend the Plan with `tools/amend_plan.py` for the generated document. | False |
| UNK-02 | How likely a `sqlite3.Error` after a successful compression is in practice (busy timeout, disk full). | Not measured; the Issue's severity assumes it can happen. | Not needed for the fix; recorded as the Issue's own open question. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/session_message_repo.py` | Modify | Medium: every message write and the session load path use the repository | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/turn_persistence.py` | Modify | Medium: every turn write routes through the boundary | 2 | N/A | not applicable (rsynced) |
| `tests/agent/test_history_compression_consistency.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_turn_persistence.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_session_message_repo.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, the mechanism: capture a pre-rewrite image and restore it on compensation (alternatives and why they were rejected are in Implementation Intent). Compatibility: `replace_messages` and `delete_messages_from` keep their names and signatures, so existing tests and the `/compact` path are untouched; only the boundary's compensation changes, and only after a rewrite.

Decision 2, where the image is captured: in the boundary's `replace_messages`, inside the same `asyncio.to_thread` call that performs the rewrite, so the database work stays on the worker thread. The image is kept only after the rewrite succeeds (a failed rewrite rolls back atomically and the existing delete-above-marker compensation is correct for it), and only the first image of a turn is kept.

Decision 3, the restore: one transaction (`begin_immediate`) that deletes the session's rows, re-inserts the image's rows with `message_id` at or below the marker preserving id and `created_at`, and resets `undo_floor_message_id`. A failure rolls back, leaves the rows untouched, and is logged; the boundary never falls back to the delete-above-marker path in that case because that path is what wipes a rewritten session.

Decision 4, the in-memory side: `TurnPersistence` stores `conv.undo_floor` at construction and restores it next to `restore_messages`, so memory and database describe the same conversation.

Consumer scan (`uv run python tools/scan_change_consumers.py --seed replace_messages`, run in Step 3; candidates only): production callers are `scripts/agent/turn_persistence.py` (target), `scripts/agent/session.py` (facade, `not affected`: signature unchanged), `scripts/agent/commands/cmd_rag_export.py` (`not affected`: outside a turn); the many orchestrator and tool tests that stub `boundary.replace_messages` with an `AsyncMock` are `not affected`.

No persisted schema, public API, or shared constant is changed.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the real-database compress-then-fail test and record that it fails on the current code (REQ-005; `tests/agent/test_history_compression_consistency.py`).
2. **Phase 2: Repository image and restore**
   - [ ] Add the image capture and the one-transaction restore (REQ-001, REQ-002; `scripts/agent/session_message_repo.py`).
   - [ ] Add the repository tests (REQ-001, REQ-002; `tests/agent/test_session_message_repo.py`).
3. **Phase 3: Boundary compensation**
   - [ ] Capture the image before the rewrite, restore it on compensation, fail safe, and restore `conv.undo_floor` (REQ-001, REQ-002, REQ-003, REQ-004; `scripts/agent/turn_persistence.py`).
   - [ ] Add the boundary unit tests (REQ-002, REQ-003, REQ-004; `tests/agent/test_turn_persistence.py`).
4. **Phase 4: Documentation**
   - [ ] Update the compensation description and run the docs checkers (REQ-006; `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`).
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py` (REQ-001; `scripts/agent/session_message_repo.py`, `scripts/agent/turn_persistence.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/turn_persistence.py`, `scripts/agent/session_message_repo.py` | Integration-style with a temporary database | `uv run pytest tests/agent/test_history_compression_consistency.py -v` | New test fails before Phase 3, passes after; existing failing-compression test passes |
| Boundary and repository | Unit | `uv run pytest tests/agent/test_turn_persistence.py tests/agent/test_session_message_repo.py -v` | All pass |
| Regression | Unit and integration | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v` and the undo tests | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture / size | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`, `uv run python tools/check_db_separation.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Reference tables | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| State and persistence document | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `SessionMessageRepository.save_many` at C (13) and several B methods in `session_message_repo.py`, and nothing worse than B in `turn_persistence.py` and `conversation_state_manager.py`; the new methods MUST NOT raise a function above grade B. `vulture` shows no finding in the three files; diff-cover is recorded at implementation time.

## Risks
- **Risk**: The restore re-inserts rows with explicit ids and could collide with rows written concurrently → **Mitigation**: the restore deletes all of the session's rows first inside one `begin_immediate` transaction, and a single writer owns a session during a turn.
- **Risk**: `session_message_repo.py` grows toward the module size gate → **Mitigation**: the module is 15453 of 20480 bytes; two compact methods fit, and `tools/check_module_size.py` runs in Phase 5.
- **Risk**: The captured image is large for a long session → **Mitigation**: it is captured only when a rewrite runs, which already means the history exceeded the compression limit, and it is released with the boundary at turn end.
- **Risk**: A restore failure leaves memory and database disagreeing → **Mitigation**: the fail-safe path never deletes rows (REQ-002), logs the failure, and still raises the persistence error so the turn is reported as not persisted.
- **Risk**: Test blast radius of the boundary change → **Mitigation**: the scan shows most callers stub `boundary.replace_messages`; only the boundary tests and the consistency file exercise the real compensation, and the existing failing-compression test stays unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing real-database compress-then-fail test | Completed | — | 20261105-081336 |  |
| 2 | Phase 2: repository image capture, restore, and tests | Completed | — | 20261105-081336 |  |
| 3 | Phase 3: boundary compensation, undo floor restore, and tests | Completed | — | 20261105-081336 |  |
| 4 | Phase 4: documentation update | Completed | — | 20261105-081336 |  |
| 5 | Phase 5: deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261104-224326_01_scripts_agent_session_message_repo.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261104-224326_02_scripts_agent_turn_persistence.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261104-224326_03_tests_agent_test_history_compression_consistency.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261104-224326_04_tests_agent_test_turn_persistence.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261104-224326_05_tests_agent_test_session_message_repo.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261104-224326_06_docs_23_agent_agent_04_01_state-and-persistence-state-model.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-114113
- **Related target files**: scripts/agent/session_message_repo.py, scripts/agent/turn_persistence.py, tests/agent/test_history_compression_consistency.py, tests/agent/test_turn_persistence.py, tests/agent/test_session_message_repo.py, docs/23_agent/agent_04_01_state-and-persistence-state-model.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Problem sequence | scripts/agent/session_message_repo.py | 2 | AC-1 | Repository round-trip tests | Confirmed by repository evidence |
| REQ-001 | Required Changes bullet 1 | scripts/agent/turn_persistence.py | 3 | AC-1 | Compress-then-fail test | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2 | scripts/agent/session_message_repo.py | 2 | AC-2 | Failing-restore repository test | Explicit in issue |
| REQ-002 | Required Changes bullet 2 | scripts/agent/turn_persistence.py | 3 | AC-2 | Fail-safe boundary test | Explicit in issue |
| REQ-003 | Acceptance Criteria bullet 2; undo_floor finding from Step 2 | scripts/agent/turn_persistence.py | 3 | AC-3 | `conv.undo_floor` and history assertions | Confirmed by repository evidence |
| REQ-004 | Constraints bullets 2-3; Required Changes bullet 4 | scripts/agent/turn_persistence.py | 3 | AC-4, AC-6 | Append-only and failing-compression tests | Explicit in issue |
| REQ-004 | Constraints bullets 2-3 | scripts/agent/session_message_repo.py | 2 | AC-4 | Existing `replace_messages` and delete tests | Explicit in issue |
| REQ-005 | Required Changes bullet 3; Acceptance Criteria bullet 3 | tests/agent/test_history_compression_consistency.py | 1 | AC-5 | New real-database test | Explicit in issue |
| REQ-005 | Testing Expectations | tests/agent/test_turn_persistence.py | 3 | AC-2, AC-3, AC-4 | Boundary unit tests | Explicit in issue |
| REQ-005 | Testing Expectations | tests/agent/test_session_message_repo.py | 2 | AC-1, AC-2 | Repository tests | Explicit in issue |
| REQ-006 | Documentation Impact | docs/23_agent/agent_04_01_state-and-persistence-state-model.md | 4 | AC-7 | `tools/check_docs_*` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261104-224326 -->
