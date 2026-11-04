## Goal
- Make `/session load` keep the conversation summary of a compressed session without weakening the untrusted-restore policy: exactly one summary row, recognized by a shared constant and rebuilt canonically, is restored right after the current system prompt; every other persisted system row is still dropped; ephemeral system rows are no longer persisted by compression; and the `/undo` boundary arithmetic counts what is restored.

## Priority
High

## Scope
- **In-Scope**:
  - Expose the summary shape from `scripts/agent/history.py` as one public constant and one public predicate, and use them in compression and in restore (no copied prefix string).
  - `restore_session`, when a current system prompt is set, restores the last persisted summary-shaped system row (role `system`, content starting with the shared prefix) rebuilt through the canonical builder, positioned after the system prompt; extra summary-shaped rows are dropped with a warning.
  - `_boundary_to_index` counts the restored summary row so the `/undo` floor lands on the same turn as before.
  - `SessionMessageRepository.replace_messages` stops persisting ephemeral system rows (`_ephemeral`, `_memory_injected`) of the compressed set.
  - Tests for the round trip, the forged non-summary row, the `/undo` boundary, and the absence of ephemeral rows; documentation of what `/session load` restores; regeneration of the generated reference document.
- **Out-of-Scope**:
  - How compression chooses turns or builds the summary, and the single-summary rule.
  - Replaying the deleted original turns.
  - The `restore_session` branch used when no current system prompt is set (it keeps its tested behavior; see UNK-01).
  - Persistence compensation after a compressing turn (a separate Plan).
  - Any schema change.
- **Dependencies**: Related to the separate compression-compensation issue (id compresscomp001, already planned): both touch `scripts/agent/session_message_repo.py` and `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` in different places. Either order works; the persisted-row rule decided here (ephemeral system rows are never persisted) applies to that Plan's rewrite tests.

## Background
`HistoryManager.compress` returns the preserved system rows (the system prompt and any ephemeral system rows), then the single `[Conversation summary]` system row, then the remaining turns. The history selection policy pulls every system-role message out before selecting turns, so ephemeral memory and hint rows are preserved through compression. `TurnPersistence.replace_messages` stores that list through `SessionMessageRepository.replace_messages`, which deletes all rows of the session first and stores only role, content, tool calls, and tool call id, so an ephemeral row is stored without its marker key. `restore_session` rebuilds the history as the current system prompt plus the non-system rows and subtracts every system row in `_boundary_to_index` (checked in Step 2).

The owner decided in the planning session: restore the summary as a system row, recognized by shape through a shared constant and rebuilt canonically; the remaining risk is stated under Risks.

## Problem
After loading a session that was ever compressed, the model has neither the old turns (deleted at compression) nor their summary (dropped by restore), and nothing tells the user. The persisted set can also hold the ephemeral memory block, which is stored indefinitely and never restored (the Issue's reproduction showed the summary row present in the rows and absent from the restored history; the code path was re-read in Step 2).

Verification corrections and findings:
1. The existing restore tests pin the drop of persisted system rows (`test_system_message_appears_exactly_once_when_db_also_has_system`, `test_memory_injected_messages_not_carried_into_restored_history`, and the `/undo` conversion test whose snapshot row `"[summary]"` has no canonical prefix and stays dropped). They stay valid because only the canonical summary shape is newly restored.
2. The branch used when no current system prompt is set keeps every persisted row, system rows included (`test_no_system_prompt_content_uses_db_messages_as_is` pins it). In production the startup prompt setup always assigns the prompt, so this branch is a test and degenerate case. It is left unchanged and recorded as UNK-01, because changing it is outside the Issue's scope.
3. Pre-single-summary data can contain several summary-shaped rows (compression collapses them into one only at the next compression). The Issue requires exactly one restored summary; the Plan keeps the last one (highest `message_id`, the most recent compression) and logs a warning for the dropped others.
4. `_SUMMARY_PREFIX` is private to `history.py` and used only there in scripts; tests use the literal text. Making it public is additive.
5. The ephemeral filter belongs in `SessionMessageRepository.replace_messages`, the single place that turns history rows into persisted rows for both the turn path and `/compact`; `ConversationStateManager` needs no change.

## Reason for Change
`/session load` is the documented way to continue earlier work, and compressed sessions are the long ones people want to continue. Losing the summary is a silent correctness failure.

## Implementation Intent
Recognize the summary by a shared shape, not by role alone: restore only a system row whose content starts with the shared prefix, rebuild it through the canonical builder so no extra keys or stored markers survive, and place it after the current system prompt. Keep dropping every other persisted system row. Stop persisting ephemeral system rows so the stored session matches what is restorable.

## Requirements
- `REQ-001`: `scripts/agent/history.py` MUST expose the summary prefix as a public constant and a public predicate recognizing a summary row (role `system`, content starting with the prefix), and compression (`_split_system_msgs`, `_build_summary_msg`) and restore MUST use them; no copy of the prefix string remains in `scripts/`.
- `REQ-002`: `restore_session`, when a current system prompt is set, MUST restore exactly one summary row, the last summary-shaped persisted system row rebuilt through the canonical builder, positioned immediately after the system prompt; extra summary-shaped rows MUST be dropped with a warning; any other persisted system row MUST still be dropped; the current system prompt MUST still replace any persisted prompt row; the branch without a current prompt MUST be unchanged.
- `REQ-003`: `_boundary_to_index` MUST count the restored summary row when it lies within the snapshot, so `ctx.conv.undo_floor` lands on the same turn as before the change and `/undo` behaves as before for sessions with and without a summary.
- `REQ-004`: `SessionMessageRepository.replace_messages` MUST NOT persist messages carrying `_ephemeral` or `_memory_injected`; the persisted boundary MUST remain the maximum `message_id` of the persisted rows; with all messages ephemeral or invalid the existing "nothing persisted" behavior applies.
- `REQ-005`: Tests MUST show, with a stubbed session API and with a compression-then-restore round trip on a temporary database, that the summary is restored after the system prompt, that a forged non-summary system row is not restored, that the `/undo` boundary points at the same turn, and that no ephemeral system row is persisted after a compression; they MUST fail on the pre-change code and pass after it.
- `REQ-006`: Documentation MUST state that `/session load` restores the summary row, which system rows are not restored and why (untrusted restore), and that ephemeral system rows are not persisted.
- `REQ-007`: The generated agent reference document MUST be regenerated so it lists the new public predicate.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/history.py` | Shared summary shape | Rename `_SUMMARY_PREFIX` to a public constant, add the public summary predicate, and use both in `_split_system_msgs` and `_build_summary_msg` (checked in Step 2) | REQ-001; AC-1 | `_SUMMARY_PREFIX = "[Conversation summary]"` is used by `_split_system_msgs` and `_build_summary_msg` only in `scripts/` (rg, checked in Step 2) | `tests/agent/test_history_manager.py` | Verified |
| `scripts/agent/services/session_restore.py` | Restore and boundary | In `restore_session`, restore the last summary-shaped row canonically after the system prompt and drop the rest; update `_boundary_to_index` to count the restored row (checked in Step 2) | REQ-002, REQ-003; AC-2, AC-3, AC-4 | `restore_session` builds `system_msgs + [m for m in repaired if m["role"] != "system"]`; `_boundary_to_index` subtracts every system row of the snapshot (checked in Step 2) | `tests/agent/test_session_restore.py` | Verified |
| `scripts/agent/session_message_repo.py` | Ephemeral rows | Skip messages carrying `_ephemeral` or `_memory_injected` when `replace_messages` builds the rows to insert (checked in Step 2) | REQ-004; AC-5 | `replace_messages` filters only by role and stores role, content, tool calls, and tool call id, so a marked row is stored without its marker (checked in Step 2) | `tests/agent/test_session_message_repo.py`, `tests/agent/test_history_compression_consistency.py` | Verified |
| `tests/agent/test_session_restore.py` | Restore tests | Add the summary-restored, forged-row, multiple-summary, undo-boundary, and idempotency tests with the file's stubbed session API (checked in Step 2) | REQ-005; AC-2, AC-3, AC-4, AC-6 | The file has `_make_ctx`, restore tests for system-row handling, and boundary tests including `test_undo_floor_converts_boundary_to_index` (checked in Step 2) | `tests/agent/test_session_restore.py` | Verified |
| `tests/agent/test_session_message_repo.py` | Persistence tests | Add tests that ephemeral system rows are not persisted by `replace_messages` and that the boundary equals the maximum persisted id (checked in Step 2) | REQ-004, REQ-005; AC-5 | The file has `replace_messages` tests including a summary-row case and the boundary test (checked in Step 2) | `tests/agent/test_session_message_repo.py` | Verified |
| `tests/agent/test_history_compression_consistency.py` | Round trip | Add the compress, persist, restore round trip on the file's patched database, including a forged non-summary system row and the `/undo` boundary (checked in Step 2) | REQ-005; AC-2, AC-3, AC-5 | The file has the `session_and_conn` fixture and compression-boundary tests (checked in Step 2) | `tests/agent/test_history_compression_consistency.py` | Verified |
| `tests/agent/test_history_manager.py` | Predicate tests | Add tests for the public predicate and for compression still producing the canonical summary row (checked in Step 2) | REQ-001; AC-1 | The file asserts summary rows by the literal prefix text in several compression tests (checked in Step 2) | `tests/agent/test_history_manager.py` | Verified |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Load behavior | Describe what `/session load` restores (system prompt, summary row) and which system rows are not, with the untrusted-restore reason (checked in Step 2) | REQ-006; AC-7 | The load section describes orphan repair and the undo floor only, not system or summary rows (checked in Step 2) | N/A: documentation | Verified |
| `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Persistence model | State that ephemeral system rows are not persisted and that the summary row is restored on load (checked in Step 2) | REQ-006; AC-7 | "Compression Persistence Model" says the summary row is persisted with `role=system` and nothing about restore or ephemeral rows (checked in Step 2) | N/A: documentation | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference | Regenerate with `tools/generate_reference_table.py --type agent` so the new public predicate is listed (checked in Step 2) | REQ-007; AC-8 | The document lists public functions per module, and `--check` reports no drift before the change (checked in Step 2) | N/A: generated documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/history_selection_policy.py` | Pulls every system-role message out before turn selection, so ephemeral rows survive compression into the persisted set | REQ-004 |
| `scripts/agent/conversation_state_manager.py` | Produces `_memory_injected` rows and calls the compression persistence; unchanged | REQ-004 |
| `scripts/agent/context.py` | `replace_history` validates restored rows as untrusted and strips ephemeral keys; the restore policy this Plan keeps | REQ-002 |
| `scripts/agent/turn_persistence.py` | Routes the compressed set to `replace_messages`; unchanged | REQ-004 |
| `scripts/agent/startup_prompt_setup.py` | Always assigns the current system prompt, which makes the prompt-set branch the production path | REQ-002 |
| `tests/agent/test_history_selection_policy.py` | Pins that system rows are never compressed; must keep passing | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): the prefix literal appears once in `scripts/` (the public constant); compression and restore use the constant and the predicate.
- AC-2 (REQ-002, REQ-005): after compression and a restore with a current system prompt, the restored history contains exactly one summary row positioned right after the system prompt, with the canonical shape and no extra keys.
- AC-3 (REQ-002, REQ-005): a persisted system row that is not the summary shape is still dropped, and extra summary-shaped rows beyond the last are dropped with a warning.
- AC-4 (REQ-003, REQ-005): `ctx.conv.undo_floor` after a restore points at the same turn as before the change, for sessions with and without a summary row.
- AC-5 (REQ-004, REQ-005): after a compression the persisted rows contain no ephemeral memory or hint row, and the persisted boundary equals the maximum persisted id.
- AC-6 (REQ-005): the new tests fail on the pre-change code and pass after the change; the existing restore tests pass unchanged.
- AC-7 (REQ-006): the two documents state the restored summary, the dropped system rows with the reason, and the non-persistence of ephemeral rows; the docs checkers report no findings.
- AC-8 (REQ-007): `uv run python tools/generate_reference_table.py --check` exits 0.

## Tests
- `REQ-005`: in `tests/agent/test_session_restore.py`, a summary row among persisted rows is restored once after the canonical prompt; a forged system row without the prefix is dropped; two summary-shaped rows keep only the last and log a warning; the boundary test with a summary in the snapshot lands on the same turn; a second restore reproduces the same history.
- `REQ-005`: in `tests/agent/test_history_compression_consistency.py`, compress a history that contains a memory-injected system row, persist it through `replace_messages`, assert the stored rows hold no ephemeral row, then restore on the temporary database and assert the summary, the forged-row case, and the `/undo` boundary.
- `REQ-004`: repository tests for the ephemeral filter and the boundary.
- `REQ-001`: predicate tests in `tests/agent/test_history_manager.py`.
- Tests use stubbed or temporary databases only.
- Regression: `tests/agent/test_session_restore.py`, `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_session_message_repo.py`, `tests/agent/test_history_manager.py`, `tests/agent/test_history_selection_policy.py`, the undo tests (`rg -l undo tests/agent`), `tests/agent/test_message_schema.py`.

## Documentation Impact
Yes. REQ-006 drives updates of the state and persistence model document and the history compression document (located through the scan and `docs/00_index.md` "Document References by Task"); REQ-007 regenerates the generated reference. No concrete values.

## Assumptions
- A single summary-shaped row is the normal persisted state after the single-summary rule; several rows appear only in data stored before it, and keeping the last one is the best available choice (checked in Step 3).
- The last summary-shaped row in `message_id` order is the most recent compression's summary.
- Rows restored through `replace_history` stay validated as untrusted; the rebuilt summary row carries only `role` and `content`, so it passes validation with no ephemeral or extra keys.
- Step 8b overlap judgement (`tools/check_plan_target_overlaps.py`): the Plan for the compression-compensation issue (`plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md`) shares `scripts/agent/session_message_repo.py`, `tests/agent/test_session_message_repo.py`, `tests/agent/test_history_compression_consistency.py`, and `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`. Judged compatible: that Plan adds new capture and restore methods and leaves `replace_messages` unchanged, while this Plan edits only `replace_messages`; the documents are edited in different sections; its pre-rewrite image holds only persisted rows, which after this Plan never include ephemeral system rows. The Plan for the memory-persistence logging issue (`plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md`) shares only the generated reference document, which each Plan regenerates from live code; compatible in either order.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the restore branch used when no current system prompt is set should also drop non-summary system rows (today it keeps every persisted row, pinned by a test). | The branch is not reachable in production startup (the prompt is always assigned); the owner's intent for it is not recorded. | Separate Issue if the owner wants the same filter there. | False |
| UNK-02 | Whether dropping all persisted system rows was originally a deliberate security decision that also covered the summary, or an oversight. | The history of the original decision was not traced. | The owner decision recorded in this Plan resolves the design; no further evidence is needed to implement it. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/history.py` | Modify | Low: rename of one private constant plus one added function | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/services/session_restore.py` | Modify | Medium: every `/session load` and the `/undo` floor | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/session_message_repo.py` | Modify | Medium: the compressed set written by every compression and `/compact` | 5 | N/A | not applicable (rsynced) |
| `tests/agent/test_session_restore.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_session_message_repo.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_history_compression_consistency.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_history_manager.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_13_reference-api-generated.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, the restored form (owner decision). Restore the summary as a `system` row, recognized only by the shared shape and rebuilt through the canonical builder. Alternatives rejected: a `user`-role form (would not be recognized by compression's system-row summary handling, risking a second summary after the next compression and widening scope into `history.py` compression), and not restoring (keeps the data loss). Compatibility: the single-summary rule and the compression algorithm are unchanged.

Decision 2, restoration rules. Only the last summary-shaped row is kept, rebuilt with only `role` and `content`, inserted right after the current system prompt; every other persisted system row is dropped as before; the branch without a current prompt is unchanged. The rebuilt row still goes through `replace_history`, which validates every restored row as untrusted.

Decision 3, the `/undo` arithmetic. The current formula is `1 + n_snapshot - system_count + insertions`. The restored summary row counts as one restored row when it lies within the snapshot, so `system_count` excludes it; rows after the snapshot are unaffected. A test pins the same turn before and after for sessions with and without a summary.

Decision 4, ephemeral rows. The filter lives in `SessionMessageRepository.replace_messages`, so both the turn path and `/compact` stop persisting them with one change; no schema change.

Consumer scan (`uv run python tools/scan_change_consumers.py --seed _SUMMARY_PREFIX`, run in Step 3; candidates only): `scripts/agent/history.py` (target; the only `scripts/` consumer), `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` (target), and tests that use the literal text (`not affected`: they do not import the private name).

No persisted schema, public API of other modules, or shared constant of other modules is changed.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the restore, round-trip, and persistence tests and record that they fail on the current code (REQ-005; `tests/agent/test_session_restore.py`, `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_session_message_repo.py`).
2. **Phase 2: Shared summary shape**
   - [ ] Make the constant public, add the predicate, and use both in compression, with predicate tests (REQ-001; `scripts/agent/history.py`, `tests/agent/test_history_manager.py`).
3. **Phase 3: Persist side**
   - [ ] Skip ephemeral system rows in `replace_messages` (REQ-004; `scripts/agent/session_message_repo.py`).
4. **Phase 4: Restore side**
   - [ ] Restore the last summary-shaped row canonically and update the boundary arithmetic (REQ-002, REQ-003; `scripts/agent/services/session_restore.py`).
5. **Phase 5: Documentation**
   - [ ] Update the two prose documents, regenerate the reference with `uv run python tools/generate_reference_table.py --type agent`, and run the docs checkers (REQ-006, REQ-007; `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`, `docs/23_agent/agent_13_reference-api-generated.md`).
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py` (REQ-002; `scripts/agent/services/session_restore.py`).

### Release units
**Unit**: summary-persist-restore | **Phases**: 3, 4 | **Reason**: stopping the persistence of ephemeral rows and restoring the summary change the stored and the rebuilt history together; the boundary arithmetic is only correct when both agree, so they are validated and released together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/session_restore.py`, `scripts/agent/session_message_repo.py` | Unit with stubs and a temporary database round trip | `uv run pytest tests/agent/test_session_restore.py tests/agent/test_history_compression_consistency.py tests/agent/test_session_message_repo.py -v` | New tests fail before Phase 3-4, pass after; existing restore tests pass |
| `scripts/agent/history.py` | Unit | `uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_selection_policy.py -v` | All pass |
| Undo and schema regression | Unit | the undo tests and `uv run pytest tests/agent/test_message_schema.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture / size | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Generated reference | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Three documents | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `repair_orphan_tool_calls` at C (14) and `restore_session` at B (10) in `session_restore.py`, and B methods in `history.py`; the change MUST NOT raise `restore_session` above grade B, which means the summary selection goes into a small helper function. `vulture` shows no finding in the two files; diff-cover is recorded at implementation time.

## Risks
- **Risk**: A local actor who can write the session database adds a row whose content starts with the summary prefix and gains system-role authority for that text (user and assistant rows never carry that authority) → **Mitigation**: owner-accepted residual risk of the chosen design; it is bounded to one row, rebuilt with only `role` and `content`, restored after the current system prompt, and every non-summary system row is still dropped; the shape is recognized through one shared constant so the rule has one place to harden later.
- **Risk**: Several summary-shaped rows in old data lose information when only the last is kept → **Mitigation**: a warning names the dropped count; data written under the single-summary rule has one row.
- **Risk**: The boundary arithmetic lands one turn off for sessions with a summary → **Mitigation**: REQ-003 and AC-4 pin the same-turn property for sessions with and without a summary, in the stubbed and the round-trip tests.
- **Risk**: Dropping ephemeral rows from persistence changes the row count that older documents or tests assume → **Mitigation**: the persistence tests and documentation are updated in the same release unit; the regression set includes the compression consistency tests.
- **Risk**: `restore_session` complexity grows → **Mitigation**: selection goes into a helper and the grade stays B.
- **Risk**: Overlap with the compression-compensation Plan in `session_message_repo.py` and the persistence-model document → **Mitigation**: different methods and sections; the shared rule is stated in Scope Dependencies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing restore, round-trip, and persistence tests | Pending | — | — | |
| 2 | Phase 2: shared public summary constant and predicate | Pending | — | — | |
| 3 | Phase 3: skip ephemeral system rows when persisting | Pending | — | — | |
| 4 | Phase 4: restore the summary and update the boundary arithmetic | Pending | — | — | |
| 5 | Phase 5: documentation and generated reference | Pending | — | — | |
| 6 | Phase 6: deployment hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-115505
- **Related target files**: scripts/agent/history.py, scripts/agent/services/session_restore.py, scripts/agent/session_message_repo.py, tests/agent/test_session_restore.py, tests/agent/test_session_message_repo.py, tests/agent/test_history_compression_consistency.py, tests/agent/test_history_manager.py, docs/23_agent/agent_04_01_state-and-persistence-state-model.md, docs/23_agent/agent_04_02_state-and-persistence-history-compression.md, docs/23_agent/agent_13_reference-api-generated.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | AI Implementation Instruction (one shared constant); `_SUMMARY_PREFIX` in `history.py` | scripts/agent/history.py | 2 | AC-1 | Predicate tests | Confirmed by repository evidence |
| REQ-001 | AI Implementation Instruction | tests/agent/test_history_manager.py | 2 | AC-1 | Predicate and canonical-summary tests | Explicit in issue |
| REQ-002 | Required Changes bullet 1; Constraints bullets 1 and 3 | scripts/agent/services/session_restore.py | 4 | AC-2, AC-3 | Restore tests with stubbed session API | Explicit in issue |
| REQ-003 | Required Changes bullet 3; Acceptance Criteria bullet 4 | scripts/agent/services/session_restore.py | 4 | AC-4 | Boundary tests with and without a summary | Explicit in issue |
| REQ-004 | Required Changes bullet 2; Acceptance Criteria bullet 3 | scripts/agent/session_message_repo.py | 3 | AC-5 | Persistence tests | Explicit in issue |
| REQ-005 | Required Changes bullet 4; Acceptance Criteria bullet 5 | tests/agent/test_session_restore.py | 1 | AC-2, AC-3, AC-4, AC-6 | New restore tests | Explicit in issue |
| REQ-005 | Required Changes bullet 4 | tests/agent/test_history_compression_consistency.py | 1 | AC-2, AC-3, AC-5 | Round-trip test | Explicit in issue |
| REQ-005 | Required Changes bullet 4 | tests/agent/test_session_message_repo.py | 1 | AC-5 | Ephemeral filter tests | Explicit in issue |
| REQ-006 | Documentation Impact | docs/23_agent/agent_04_01_state-and-persistence-state-model.md | 5 | AC-7 | `tools/check_docs_*` | Explicit in issue |
| REQ-006 | Documentation Impact; section found in Step 2 | docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | 5 | AC-7 | `tools/check_docs_*` | Derived from confirmed evidence |
| REQ-007 | Derived: new public function listed in the generated reference | docs/23_agent/agent_13_reference-api-generated.md | 5 | AC-8 | `tools/generate_reference_table.py --check` | Confirmed by repository evidence |
