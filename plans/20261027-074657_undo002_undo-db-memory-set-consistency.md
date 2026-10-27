# Plan: Make /undo delete the same turn set from memory and the session database

## Goal
- `/undo` derives the memory trim from the exact set of rows the DB deletes (with a
  documented reload fallback), so a diverged memory/DB state converges to parity
  instead of widening the divergence.

## Priority
Medium — `/undo` is the recovery command users reach for after a broken turn; it must
restore parity. Path A (upper end): 4 production files on one call path, 3 test files,
1 doc, plus an internal API return-type change.

## Scope
- **In-Scope**:
  - Row-returning DB undo step: `scripts/agent/session_message_repo.py` (new row-level
    undo method) and `scripts/agent/session.py` (`undo_last_turn` delegates and returns
    the deleted rows).
  - `scripts/agent/services/models.py`: `DeletedRow` dataclass + additive
    `UndoResult.deleted_rows`.
  - `scripts/agent/services/undo_service.py`: memory trim driven by the deleted-row
    set; reload-from-DB fallback on ambiguous matching; parity logging.
  - Regression test for the diverged-state parity scenario.
  - Docs: `/undo` parity guarantee (intent + failure behavior).
- **Out-of-Scope**:
  - Preventing divergence (turn001 atomic persistence, turn002 orphan repair — separate
    Plans).
  - `/undo` UX changes beyond parity logging.
  - Redesigning the compression-boundary mechanism (issue AI instruction).
- **Dependencies**:
  - `issues/20261026-224643_turn001_atomic-turn-persistence.md` (now
    `issues/done/`, Plan `plans/20261027-070403_turn001_atomic-turn-persistence.md`
    Frozen but not yet implemented): undo002 remains valid regardless — parity must
    hold for any pre-existing divergence (old sessions, interrupted processes).
    Re-verify remaining reachable divergence states after turn001/turn002 are
    implemented; if fewer states remain, this Plan's fallback branch may become rarely
    exercised but is still required for legacy sessions.

## Background
From the python-code-review pass over the REPL turn path (finding F-007). Re-verified
against current code after the earlier undone-boundary work:
- `scripts/agent/services/undo_service.py` (L22-55): memory-side search for the last
  user message at index >= `ctx.conv.undo_floor`, `cut_idx` walk-back over
  `_memory_injected`/`_ephemeral` artifacts, `ctx.session.undo_last_turn()` DB-first,
  then memory trimmed to the independently computed `cut_idx`. Issue claim confirmed.
- `scripts/agent/session.py` `undo_last_turn` (L204-249): opens its own connection,
  selects the last user row from DB state, deletes `message_id >= last_user_id`,
  returns only the int count — no row identity returned. Confirmed.
- `_memory_injected`/`_ephemeral` markers are memory-only dict keys
  (`scripts/agent/message_schema.py` L20; DB `messages` rows store role/content/
  tool_calls/tool_call_id only) — a full memory reload would silently drop these
  markers from surviving rows, which is why matching (not reload) is the primary path.

## Problem
After memory/DB divergence (persistence failure, synthetic/orphan rows), one undo can
remove different messages from each side; the logged counts (`n_removed` vs cut index)
already differ.

## Reason for Change
Undo must be the one operation guaranteed to bring the two views back together; today
it can widen the gap.

## Implementation Intent
DB side returns what it deleted; memory side deletes exactly that (tail-matching on row
identity), keeping the artifact walk-back as a memory-side extension for memory-only
markers. When tail matching is ambiguous, reload the remaining conversation from the DB
and log the decision (issue AI instruction — this Plan adopts the AI instruction's own
tie-breaker: prefer reload over heuristic matching).

## Requirements
- `REQ-001`: The DB undo step returns the deleted rows as identity data
  (`DeletedRow`: `message_id`, `role`, `content`, `tool_call_id`) in ascending
  `message_id` order; the DB boundary gate (`last_user_id <= undo_floor` → nothing
  undoable) and DB-first ordering are unchanged.
- `REQ-002`: Memory trim is driven by the returned deleted-row set: tail-match memory
  messages to the deleted rows (role + tool_call_id exact; content equality when
  present), extended by the existing `_memory_injected`/`_ephemeral` walk-back. The
  memory-computed index no longer determines what is deleted from the DB side.
- `REQ-003`: Ambiguous matching (deleted DB rows not matchable as a contiguous memory
  tail after artifact tolerance) → replace memory history with the remaining rows from
  `fetch_messages` (reload fallback) and log the decision with the row ids; marker loss
  on surviving rows is an accepted, logged consequence of the fallback only.
- `REQ-004`: Both sides are logged with the same `message_id`s (auditability).
- `REQ-005`: `UndoResult` stays backward compatible (`n_removed`, `block_reason`
  unchanged; `deleted_rows` added with a default); `session.undo_last_turn`'s return
  type change (int → `list[DeletedRow]`) is updated in all callers atomically
  (`undo_service.py`, `cmd_context.py` untouched, tests).
- `REQ-006`: Compression-boundary behavior (`undo_floor_message_id` persistence,
  memory-side `ctx.conv.undo_floor` gate, blocked `UndoResult`) is preserved exactly.
- `REQ-007`: Parity invariant: after a successful undo, memory history and
  `fetch_messages` output describe the same conversation (same roles/contents/tool
  rows), including when they diverged beforehand.

## Implementation Target Files
**Freeze status**: Frozen (`issue-to-plan` Step 8 Implementation Target Files
Validation passed — structure check exit 0, all target paths verified against
source, both overlap findings adjudicated Compatible per the target-file rules.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/services/models.py | Add `DeletedRow` frozen dataclass (message_id, role, content, tool_call_id); add `deleted_rows: list[DeletedRow]` (default empty) to `UndoResult` | Row identity must cross the service boundary; current `UndoResult` has only `n_removed`/`block_reason` | REQ-001, REQ-005 | Read: `UndoResult` L120-128 | tests/agent/test_undo_db_memory_parity.py | Verified |
| scripts/agent/session_message_repo.py | New row-level undo method: one connection — read `undo_floor_message_id`, find last user row, SELECT `message_id, role, content, tool_call_id` for `message_id >= last_user_id` ORDER BY message_id, DELETE them, return `(deleted_rows)` ([] when blocked) | Undo SQL today lives in `session.py` (L215-243) with no repo equivalent; row return needs a repo-level home consistent with other session-message operations | REQ-001, REQ-006 | Read: `session.undo_last_turn` L215-243; repo already owns `replace_messages` boundary update (L150-175) and load (L199-253) | tests/agent/test_agent_session.py | Verified |
| scripts/agent/session.py | `undo_last_turn` delegates to the new repo method and returns `list[DeletedRow]` ([] = blocked); removes its inline SQL | Return int count is the root of the independent-side problem; callers updated atomically (REQ-005) | REQ-001, REQ-005 | Read: L204-249 returns `deleted` int; callers: `undo_service.py` L48, `cmd_context.py` uses only `UndoResult` | tests/agent/test_agent_session.py, tests/agent/test_regression_undo_artifact.py | Verified |
| scripts/agent/services/undo_service.py | Trim memory by tail-matching the returned rows (artifact walk-back retained); reload-from-DB fallback on ambiguous match; parity logging with the same ids | Current trim uses an independent `cut_idx` (L30-52); parity guarantee impossible across divergence | REQ-002, REQ-003, REQ-004, REQ-006, REQ-007 | Read: L22-55 | tests/agent/test_undo_db_memory_parity.py | Verified |
| tests/agent/test_agent_session.py | Update `undo_last_turn` cases to the new return type (row lists instead of ints; blocked = []); keep boundary-gate assertions | Existing cases assert ints (`== 0`, counts) at L588-667 | REQ-001, REQ-005, REQ-006 | Read: undo_last_turn section L578-667 | — | Verified |
| tests/agent/test_regression_undo_artifact.py | Update DB-undo assertions to row-list returns; keep artifact walk-back expectations | Cases call `session.undo_last_turn()` and assert counts (L157-218) | REQ-002, REQ-005 | Read: L147-218 | — | Verified |
| tests/agent/test_undo_db_memory_parity.py | New regression module: injected DB/memory divergence → undo leaves both sides describing the same conversation; fallback-reload branch; id logging | No existing test constructs diverged memory/DB state before undo (grep over tests/) | REQ-002, REQ-003, REQ-004, REQ-007 | New file; no name collision (`ls tests/agent`) | — | Verified |
| docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | State the `/undo` parity guarantee: memory and DB trimmed from the same row set; failure behavior when they already differ (parity restored or documented reload fallback) | Current section (L34) describes undo popping "from both" without parity semantics under divergence | REQ-002, REQ-003, REQ-007 | `docs/00_index.md` maps slash-command semantics to agent_07; file exists; `/undo` section at L34 | N/A: documentation only | Verified |

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
| scripts/agent/commands/cmd_context.py | Only consumes `UndoResult.block_reason` / `n_removed` (L128-136) — confirms REQ-005 backward compatibility holds for the command layer | REQ-005 |
| scripts/agent/conversation_state_manager.py | `_EPHEMERAL_KEYS` and `undo_floor` maintenance (L30, handle_history_compression L155-169) — boundary semantics to preserve | REQ-006 |
| scripts/agent/message_schema.py | `_memory_injected`/`_ephemeral` are memory-only keys (L20); DB rows lack them — basis for the match-first, reload-fallback decision | REQ-002, REQ-003 |
| tests/agent/test_session_memory_boundary.py | Existing boundary/memory parity gate — regression gate expected unchanged | REQ-006 |
| tests/agent/test_history_compression_consistency.py | Existing compression-boundary undo tests from earlier undo issues (issue AC-2) | REQ-006 |

## Acceptance Criteria
- `AC-001` (REQ-007): With an injected divergence (extra synthetic tool rows in the DB
  tail), after `/undo`, memory history and `fetch_messages` output describe the same
  conversation.
- `AC-002` (REQ-001, REQ-005): `session.undo_last_turn()` returns the deleted rows
  (ids ascending, roles/contents/tool_call_ids) and `[]` when blocked; `UndoResult`
  keeps `n_removed`/`block_reason` semantics.
- `AC-003` (REQ-006): All existing boundary-gate tests from the earlier undo issues
  pass unchanged (`test_agent_session.py` gate class, `test_history_compression_
  consistency.py`, `test_session_memory_boundary.py`).
- `AC-004` (REQ-003): Ambiguous-match scenario reloads memory from the DB and logs the
  decision with the deleted row ids.
- `AC-005` (REQ-002): Artifact walk-back behavior (memory-only `_memory_injected`/
  `_ephemeral` stripping) unchanged — `test_regression_undo_artifact.py` passes after
  its return-type adaptations.

## Tests
- `T-001` (REQ-007, core regression): construct diverged session (DB has an extra
  orphan tool row in the last turn; memory does not) → undo → assert memory ==
  fetch_messages parity (roles, contents, ids order).
- `T-002` (REQ-001): undo on a healthy session returns DeletedRow list matching the
  previously deleted set; blocked-at-boundary returns []/blocked UndoResult.
- `T-003` (REQ-003): divergence where DB tail contains rows absent from memory AND
  memory tail cannot match contiguously → fallback reload path, warning logged.
- `T-004` (REQ-002): memory-only artifacts before the last user row are trimmed as
  today (parity with `test_regression_undo_artifact.py` expectations).
- Gates: `uv run pytest tests/agent/test_agent_session.py
  tests/agent/test_regression_undo_artifact.py tests/agent/test_session_memory_boundary.py
  tests/agent/test_history_compression_consistency.py`; `mypy`/`ruff` (issue Testing
  Expectations).

## Documentation Impact
Docs update required, driven by REQ-002/REQ-003/REQ-007: the session slash-commands doc
(mapped via `docs/00_index.md` → `agent_07_07_cli-and-commands-slash-commands-session-
mcp.md`, `/undo` section L34) must state the parity guarantee and the divergence
failure behavior. Chosen over `agent_04_01` (state model) to keep this Plan's doc edit
out of the agent_04_01 section already shared by the turn001/turn002 Plans.

## Assumptions
- Overlap adjudication (Step 8b, re-run at freeze): `scripts/agent/session.py` and
  `scripts/agent/session_message_repo.py` are also targeted by the Frozen turn001 Plan.
  Judged **compatible**: turn001 adds `turn_boundary()` to `session.py` and
  transaction/compensation variants to the repo; undo002 changes only `undo_last_turn`
  (session) and adds a new row-returning undo method (repo). Disjoint members and edit
  sites; implement in either order. If implemented after turn001, the new repo undo
  method should follow turn001's connection-reusing pattern (single
  `SQLiteHelper("session").open()` transaction).
- Tail matching key: `(role, tool_call_id, content)`. Content equality is safe for the
  tail because the deleted region is bounded by the last user row and turn-sized;
  ambiguity only triggers the documented reload fallback (REQ-003), per the issue AI
  instruction's tie-breaker.
- Memory injection rows ARE persisted to the DB (`handle_memory_injection` saves them),
  only their `_memory_injected` marker is memory-only — so matched memory rows keep
  their markers on the primary path (no marker loss unless the fallback fires).
- `stat_turns` decrement and `UndoResult` reporting semantics stay as today.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Remaining reachable divergence states after turn001/turn002 implementations land (issue Unresolved Question, confidence Medium) | turn001/turn002 are Frozen Plans, not yet implemented | Implement undo002 now (legacy sessions and interrupted processes retain divergence regardless); re-verify frequency after turn001/turn002 implementation per the issue's dependency note | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/services/models.py | Add DeletedRow; extend UndoResult additively | services layer consumers of UndoResult (cmd_context, undo_service) | 4 | — | None |
| scripts/agent/session_message_repo.py | New undo method | session layer | 3 | — | None (uses existing schema, no migration) |
| scripts/agent/session.py | undo_last_turn return-type change | direct callers only (undo_service; tests) | 5 | — | None |
| scripts/agent/services/undo_service.py | Parity trim + fallback + logging | `/undo` command path | 1 | — | None |
| tests/agent/test_agent_session.py | Return-type updates | test suite | — | — | None |
| tests/agent/test_regression_undo_artifact.py | Return-type updates | test suite | — | — | None |
| tests/agent/test_undo_db_memory_parity.py | New module | test suite | — | — | None |
| docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | /undo parity semantics | docs | — | — | None |

## Design
- Flow after change (`undo_service.undo_last_turn(ctx)`):
  1. Boundary gate unchanged: memory search at index >= `ctx.conv.undo_floor`; None →
     blocked (unchanged). Memory search remains for the gate only (issue allows it).
  2. `deleted_rows = ctx.session.undo_last_turn()` → repo method executes
     floor-read + last-user-select + row SELECT + DELETE in one connection/transaction
     (DB-first ordering preserved, REQ-001/REQ-006). `[]` → blocked (maps to today's
     `removed == 0` branch).
  3. Memory reconciliation: walk memory tail backwards matching `deleted_rows` in
     reverse order; tolerate memory-only `_memory_injected`/`_ephemeral` artifacts via
     the existing walk-back; full match → delete matched suffix. Mismatch → fallback:
     `ctx.conv.history = fetched remaining rows` (session load boundary already builds
     `LLMMessage` dicts via `fetch_messages`) + warning log with deleted ids.
  4. Log: single log line listing deleted `message_id`s and the memory side's matched/
     reloaded state (REQ-004).
- `DeletedRow` lives in `scripts/agent/services/models.py` (issue's named home);
  `session_message_repo.py` imports it — consistent with the repo's existing role in
  the services/session boundary. (If a repo-layer import cycle appears, the dataclass
  stays in models.py and the repo constructs plain tuples — implementation procedure
  will confirm; models.py has no agent-layer imports today.)
- No compensation/rollback machinery added (contrast with the turn001 Plan): parity is
  achieved by construction — one row set drives both sides.

## Implementation steps
1. **Phase 1: Row-returning DB undo step**
   - [ ] Add `DeletedRow` + `UndoResult.deleted_rows` (REQ-001, REQ-005;
     scripts/agent/services/models.py)
   - [ ] Add row-level undo method (single transaction; SELECT+DELETE; boundary gate)
     (REQ-001, REQ-006; scripts/agent/session_message_repo.py)
   - [ ] Re-point `session.undo_last_turn` to the repo method, return
     `list[DeletedRow]` (REQ-001, REQ-005; scripts/agent/session.py)
2. **Phase 2: Memory reconciliation in the service**
   - [ ] Tail-match trim + artifact walk-back retention + reload fallback + id logging
     (REQ-002, REQ-003, REQ-004, REQ-007; scripts/agent/services/undo_service.py)
3. **Phase 3: Tests and docs**
   - [ ] Update return-type assertions (REQ-005, REQ-006;
     tests/agent/test_agent_session.py, tests/agent/test_regression_undo_artifact.py)
   - [ ] New parity regression module T-001..T-004 (REQ-002, REQ-003, REQ-004, REQ-007;
     tests/agent/test_undo_db_memory_parity.py)
   - [ ] Update the `/undo` section with the parity guarantee (REQ-002, REQ-003,
     REQ-007; docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md)
   - [ ] Run the full validation plan below; `deploy.sh` impact: none (no schema
     migration, no deployment file touched)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/session_message_repo.py + session.py | Unit: row-return undo, boundary gate | `uv run pytest tests/agent/test_agent_session.py tests/agent/test_regression_undo_artifact.py` | Updated cases pass |
| scripts/agent/services/undo_service.py | Unit/integration: T-001..T-004 with real temp DB | `uv run pytest tests/agent/test_undo_db_memory_parity.py` | Parity holds after injected divergence |
| boundary gates | Regression gate unchanged | `uv run pytest tests/agent/test_session_memory_boundary.py tests/agent/test_history_compression_consistency.py` | Pass unchanged (AC-003) |
| command layer | Regression gate | `uv run pytest tests/agent/commands/test_agent_cmd_context.py` | UndoResult consumption unchanged (AC-002) |
| lint/type | Static checks | `uv run ruff check . && uv run mypy scripts/agent/services/undo_service.py scripts/agent/services/models.py scripts/agent/session.py scripts/agent/session_message_repo.py` | Clean (issue Testing Expectations) |

## Risks
- **Risk**: `session.undo_last_turn` return-type change breaks an unlisted caller →
  **Mitigation**: repo-wide grep found only `undo_service.py` + tests as callers;
  AC-002/REQ-005 atomic-update rule; validation plan includes the command-layer gate.
- **Risk**: fallback reload loses `_memory_injected`/`_ephemeral` markers on surviving
  rows → **Mitigation**: primary path is match-based (markers kept); fallback logs the
  decision with ids; marker loss affects only artifact walk-back efficiency, not
  conversation content.
- **Risk**: implementing after turn001 changes `session_message_repo.py` structure →
  **Mitigation**: overlap adjudicated compatible in Assumptions; new method follows
  whatever connection pattern the file has at implementation time.
- **Risk**: content-equality matching mis-selects identical repeated messages →
  **Mitigation**: matching is a reverse-order contiguous tail walk bounded by the last
  user row, not a global search; ambiguity routes to the deterministic reload fallback.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: row-returning DB undo step | Pending | — | — | |
| 2 | Phase 2: memory reconciliation in the service | Pending | — | — | |
| 3 | Phase 3: tests and docs | Pending | — | — | |

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
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-10-27 07:46:57
- **Related target files**: `scripts/agent/services/models.py`,
  `scripts/agent/session_message_repo.py`, `scripts/agent/session.py`,
  `scripts/agent/services/undo_service.py`, `tests/agent/test_agent_session.py`,
  `tests/agent/test_regression_undo_artifact.py`,
  `tests/agent/test_undo_db_memory_parity.py`,
  `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Section | Source Content | Target File | Implementation Phase | Acceptance Criteria | Test Case | Basis |
|---|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes 1 | DB returns deleted row identity | scripts/agent/session_message_repo.py | Phase 1 | AC-002 | T-002 | Confirmed by repository evidence (session.py L215-249) |
| REQ-002 | Required Changes 2 | Memory trim from deleted row set | scripts/agent/services/undo_service.py | Phase 2 | AC-005 | T-004 | Confirmed (L30-52 independent cut_idx) |
| REQ-003 | AI Implementation Instruction | Reload beats heuristic on ambiguity | scripts/agent/services/undo_service.py | Phase 2 | AC-004 | T-003 | Confirmed (message_schema L20 marker loss analysis) |
| REQ-004 | Required Changes 3 | Same-id logging both sides | scripts/agent/services/undo_service.py | Phase 2 | AC-004 | T-001 | Confirmed (L54 divergent log) |
| REQ-005 | Constraints 3 | UndoResult compatible / callers atomic | scripts/agent/services/models.py | Phase 1 | AC-002 | T-002 | Confirmed (models L120-128; caller grep) |
| REQ-006 | Constraints 1-2 | Boundary + DB-first preserved | scripts/agent/session.py | Phase 1 | AC-003 | T-002 | Confirmed (L216-234 gate) |
| REQ-007 | Acceptance Criteria 1 | Divergence → parity after undo | tests/agent/test_undo_db_memory_parity.py | Phase 3 | AC-001 | T-001 | Derived from confirmed evidence |
