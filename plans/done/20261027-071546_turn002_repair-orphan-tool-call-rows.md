## Goal
- Repair orphaned assistant `tool_calls` rows (no matching tool-result rows) at the session
  load boundary (`restore_session`) by synthesizing "interrupted" tool-result rows in the
  restored in-memory history, so resumed sessions always send a well-formed, paired message
  sequence to the backend.

## Priority
High (source issue priority: High)

## Scope
- **In-Scope**:
  - Load-time detection of assistant rows carrying `tool_calls` whose every
    `tool_call_id` is not followed by a tool row with the matching `tool_call_id`.
  - In-memory synthesis of missing tool-result rows (deterministic order, identifiable
    marker content, whitelist-conformant shape), with warning log (session id + repaired
    row count).
  - `undo_floor` boundary-index accounting for synthesized rows inserted before the
    compression boundary in `restore_session`.
  - Regression tests: orphan→paired, idempotency (load twice), boundary adjustment, log.
- **Out-of-Scope**:
  - Turn write-path changes / preventing new orphans — covered by the frozen Plan
    `plans/20261027-070403_turn001_atomic-turn-persistence.md`.
  - Writing synthesized rows to the DB at load time (repair is memory-only; see Design).
  - Backend-side validation changes (issue Out of Scope).
  - Removal of orphaned tool rows (tool row without a matching assistant `tool_calls`) —
    not producible by the hard-kill failure mode (tool rows are written only as a group
    after the assistant row) and not part of the issue's repair target; recorded as an
    assumption.
- **Dependencies**: `issues/20261026-224643_turn001_atomic-turn-persistence.md` (Plan
  `plans/20261027-070403_turn001_atomic-turn-persistence.md`, `Frozen`): implement this
  plan after turn001 — turn001 prevents new orphans; this plan repairs existing ones. No
  shared target files with that Plan (verified by `check_plan_target_overlaps.py` after
  freeze).

## Background
- From python-code-review finding F-002. Verified against current source with corrections:
  - The issue names `save_assistant_message` — that symbol does not exist; the assistant
    row is saved via `AgentSession.save("assistant", ...)` in `scripts/agent/llm_turn_runner.py`
    (L141-142) BEFORE tool rows are persisted by `complete_round`.
  - `scripts/agent/tool_runner.py` exists; per-call `Exception` is converted, but
    `BaseException` (incl. `KeyboardInterrupt`/`CancelledError`) propagates out of
    `execute_all_tool_calls` (L77-79), and SIGKILL/power loss between the two persistence
    steps leaves the assistant row with no tool rows — claim confirmed.
  - The issue claims `fetch_messages` "filters orphaned tool-result rows" — **stale**:
    current `fetch_messages` (`scripts/agent/session_message_repo.py` L196-254) applies no
    orphan filter and no pairing check; orphan pairs flow straight into restored history.
  - The issue names `SyntheticToolCallCompletion` in `tool_round_completion.py` — that
    class does not exist; the synthetic-completion semantics to mirror are in
    `scripts/agent/tool_preparation.py` (`_reject`, L52-74) and `tool_runner.py`: tool rows
    with `role=tool`, `tool_call_id`, content = error/interrupted text.
  - Load boundary: `restore_session` (`scripts/agent/services/session_restore.py`) is the
    single consumer of `fetch_messages` (only `cmd_session._load_session` calls it; grep
    found no other load path).

## Problem
- After a hard crash mid tool-round, `/session load` replays a history where an assistant
  `tool_calls` row is not followed by matching `tool` rows; the backend's response is
  undefined (issue Unresolved Question), worst case the session becomes permanently
  unusable. The malformed state is already in the DB.

## Reason for Change
- Crash-resume is a core reliability path; without load-time repair every resume attempt of
  an affected session can fail.

## Implementation Intent
- Add a pure, deterministic repair step inside `restore_session`, applied to the fetched
  message list before `replace_history`: for each assistant message with `tool_calls`, check
  for tool rows with matching `tool_call_id` in the immediately following run of tool
  messages; for each missing one, insert a synthesized tool row (module-level marker
  constant, e.g. `"[interrupted] tool call did not complete before session termination"`)
  positioned in `tool_calls` order. Log a warning with session id and repaired-row count.
  Account for synthesized insertions when converting `undo_floor_message_id` to a history
  index (`_boundary_to_index`). Memory-only: no DB writes, so the repair is trivially
  idempotent.

## Requirements
- `REQ-001`: `restore_session` detects assistant messages carrying `tool_calls` for which
  no tool row with the matching `tool_call_id` exists in the following tool-row run.
- `REQ-002`: Missing tool results are synthesized in memory in `tool_calls` order with a
  module-level marker constant and a whitelist-conformant row shape
  (`role`/`content`/`tool_call_id`; `name` optional) so `replace_history` validation keeps
  them.
- `REQ-003`: Every repair logs a warning including session id and the number of synthesized
  rows.
- `REQ-004`: Repair is deterministic and idempotent: no DB writes; loading the same session
  twice yields identical history and no duplicate synthesized rows.
- `REQ-005`: `undo_floor` boundary index conversion (`_boundary_to_index`) accounts for rows
  synthesized before the boundary; the floor never points past its intended turn.
- `REQ-006`: No changes to the turn write path, `SessionMessageRepository`, or any DB row
  (issue constraint).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/services/session_restore.py | Add orphan-pairing detection + in-memory synthesis + warning log + boundary-index accounting in `restore_session` | Sole load boundary consumer of `fetch_messages`; currently applies no pairing repair | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 | Read: `restore_session` L47-120 consumes `fetch_messages` and `_boundary_to_index` L26; only caller is `cmd_session._load_session` L249 | tests/agent/test_session_restore.py | Verified |
| tests/agent/test_session_restore.py | Extend: orphan→paired regression, idempotency (load twice), undo_floor adjustment with synthesized rows, warning log assertion | New load-time repair behavior needs regression coverage | REQ-001..REQ-005 | File exists (Step 3 inventory) | — | Verified |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Document load-time orphan repair: what an interrupted tool round looks like after resume (memory-only synthesis, marker, idempotency) | Issue Documentation Impact: state resume/repair behavior in the session persistence docs | REQ-002, REQ-003, REQ-007 (docs) | `docs/00_index.md` "Session / DB persistence" mapping; `agent_04_01` has "Session Persistence Design Intent" + history-vs-DB sections; file exists | N/A: documentation only | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/session_message_repo.py | `fetch_messages` output shape (`role`/`content`/`tool_calls`/`tool_call_id`) and its "no pairing filter today" baseline; MUST NOT be modified | scripts/agent/services/session_restore.py; REQ-001 |
| scripts/agent/tool_preparation.py | Existing synthetic-failure row semantics (`_reject`, L52-74) the synthesized marker must mirror | scripts/agent/services/session_restore.py; REQ-002 |
| scripts/agent/tool_runner.py | Real tool-row shape written by `_collect_tool_result_msgs` (L263-266) and `BaseException` propagation semantics (L77-79) explaining how orphans are produced | scripts/agent/services/session_restore.py; REQ-001 |
| scripts/agent/message_schema.py | `ROLE_KEY_WHITELIST` (L30-35): synthesized rows must use only allowed keys or `replace_history` sanitization drops them | scripts/agent/services/session_restore.py; REQ-002 |
| scripts/agent/commands/cmd_session.py | Only production caller of `restore_session` (`_load_session` L249); confirms no other load path | scripts/agent/services/session_restore.py; REQ-004 |
| scripts/agent/history_selection_policy.py | Existing turn-unit/orphan semantics in compression (L85) to keep repair semantics consistent | scripts/agent/services/session_restore.py; REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001/002): A test DB containing an assistant row with `tool_calls` and zero
  tool rows yields a paired history after `restore_session`; the follow-up request built
  from history contains paired tool calls.
- `AC-002` (REQ-003): The repair emits a warning log containing the session id and repaired
  row count.
- `AC-003` (REQ-004): Loading the same orphaned session twice produces identical history;
  no duplicate synthesized rows; DB row count unchanged after load.
- `AC-004` (REQ-005): With an `undo_floor_message_id` set and synthesized rows inserted
  before the boundary, `ctx.conv.undo_floor` points at the correct post-repair index (never
  past history end, never splits a turn unit).
- `AC-005` (REQ-006): `scripts/agent/session_message_repo.py` and the turn write path are
  byte-identical after this plan (diff scope); existing fetch/restore tests
  (`test_session_message_repo.py`, `test_session_correlation_refresh.py`,
  `test_regression_history_compress_reload.py`) pass unchanged.
- `AC-006` (all): `mypy`/`ruff` pass.

## Tests
- `test_session_restore.py` (extend): orphaned assistant `tool_calls` row → `restore_session`
  output history is paired (REQ-001/002); idempotency: restore twice → equal histories
  (REQ-004); boundary test: `undo_floor` set + orphan before boundary → floor index lands on
  the correct turn after synthesis (REQ-005); warning log asserted with session id and count
  (REQ-003).
- Regression (unchanged execution): `uv run pytest tests/agent/test_session_restore.py
  tests/agent/test_session_message_repo.py tests/agent/test_regression_history_compress_reload.py`
  — repo tests must pass with zero repo-file changes (REQ-006).

## Documentation Impact
- Yes. Per `docs/00_index.md` "Session / DB persistence" mapping, the state/persistence doc
  (`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, Implementation Target
  Files row) must state the resume/repair behavior: interrupted tool rounds appear paired
  after load, synthesized rows are memory-only with an identifiable marker, and crash-time
  orphan prevention is turn001's boundary (failure-behavior note). Driven by REQ-002/REQ-003.
  Run `tools/check_doc_claims.py` after the doc edit per `routing.md`.

## Assumptions
- `restore_session` is the only session-history load path in the repository today (verified:
  only `cmd_session._load_session` calls it; no startup-time resume flag found). A future
  startup-resume feature must route through it to inherit the repair.
- The llamacpp backend tolerates — or rejects — only the unpaired sequence; synthesis
  (chosen strategy) makes the sequence well-formed regardless, so the backend-behavior
  unknown does not change the implementation shape (issue guard: implementation must stop
  and report if live-backend confirmation contradicts this).
- Orphaned tool rows (tool row without assistant `tool_calls`) are not producible by the
  hard-kill path and are left to existing validation (`replace_history` keeps them;
  backend tolerance untested) — out of scope here.
- Overlap judgment (Step 8b): `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`
  is also targeted by the Frozen Plan
  `plans/20261027-070403_turn001_atomic-turn-persistence.md` — judged **compatible**:
  turn001 documents the turn write-boundary contract; this Plan adds the load-time repair
  section. Implement turn001's doc section first.
- Memory-only synthesis is acceptable: `session_stats` counts and `fetch_messages` DB counts
  may differ by the synthesized rows until the next compression `replace_messages` persists
  the repaired history (logged at load time).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How the llamacpp backend actually responds to an assistant `tool_calls` row with no matching tool rows (hard rejection vs tolerated) (issue Unresolved Question) | No live-backend experiment recorded | Confirm by resuming a crafted orphaned session against the live backend during the implementation phase; stop-and-report if it contradicts the synthesis strategy (issue AI instruction) | False |
| UNK-02 | Whether synthesized (memory-only) rows should eventually be persisted to the DB (currently only via a later compression `replace_messages`) | No product decision in the issue | Default memory-only per this Plan; revisit only if UNK-01 or ops feedback requires it | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/services/session_restore.py | Add load-time repair | Single production caller (`cmd_session`); no write-path impact | 4 | 1 (dominant author >70%) | File sync via `deploy/deploy.sh` |
| tests/agent/test_session_restore.py | Extend tests | Test-only | — | — | N/A: tests not deployed |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Add repair behavior section | Docs only | — | — | N/A: docs not deployed |

## Design
- Path A (3 target files): repair confined to the load boundary; no new module — a pure
  module-level function `repair_orphan_tool_calls(messages, session_id) ->
  tuple[list[LLMMessage], int]` inside `session_restore.py`, called between
  `fetch_messages` and boundary computation/`replace_history`.
- Pairing rule: for each assistant message with `tool_calls`, the matching tool rows are
  searched in the contiguous run of `role="tool"` messages immediately following it
  (mirrors how `_collect_tool_result_msgs` emits them, `tool_runner.py` L263-266); missing
  ids synthesized in `tool_calls` order right after the last tool row of the run (or right
  after the assistant message when no run exists — the crash case).
- Synthesis chosen over stripping dangling `tool_calls` (issue Unresolved Question 2):
  synthesis preserves the model's record of what it attempted and mirrors the existing
  synthetic-row shape used by `tool_preparation._reject` (role=tool, tool_call_id,
  marker content); stripping would rewrite assistant semantics.
- Marker: module-level constant in `session_restore.py`; identifiable in logs/history,
  whitelist-conformant (`content` text only) so `_sanitize_message`/`replace_history`
  validation keeps the row.
- Boundary accounting: `repair_orphan_tool_calls` returns the number of rows synthesized
  before each existing message index; `_boundary_to_index` adds the insertions preceding the
  boundary snapshot so `undo_floor` lands on the same turn as before repair.
- Idempotency: pure function over the fetched list; DB untouched; second load re-synthesizes
  the same rows over the same orphan base — output identical (test-pinned).

## Implementation steps
1. **Phase 1: Core repair logic**
   - [ ] Implement `repair_orphan_tool_calls` (detection + synthesis + marker constant +
     log) in the restore service (REQ-001, REQ-002, REQ-003;
     scripts/agent/services/session_restore.py)
   - [ ] Integrate into `restore_session` call order (fetch → repair → boundary index
     accounting → `replace_history`) (REQ-005; scripts/agent/services/session_restore.py)
2. **Phase 2: Tests**
   - [ ] Add orphan→paired, idempotency, undo_floor adjustment, and log-assertion cases
     (REQ-001..REQ-005; tests/agent/test_session_restore.py)
3. **Phase 3: Verification & documentation**
   - [ ] Run targeted + full test suites, `mypy`, `ruff`, diff-scope check that
     `scripts/agent/session_message_repo.py` is untouched (REQ-006, AC-005/006)
   - [ ] Confirm backend behavior against live llamacpp backend with a crafted orphaned
     session in a dev DB (stop-and-report if contradicted) (UNK-01)
   - [ ] Update state/persistence doc + run `tools/check_doc_claims.py` (REQ-002, REQ-003;
     docs/23_agent/agent_04_01_state-and-persistence-state-model.md)
   - [ ] Deployment check: `deploy/deploy.sh` syncs the modified service file; no schema or
     config change (all REQ)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/services/session_restore.py | Unit: crafted orphaned-session DB fixture | `uv run pytest tests/agent/test_session_restore.py` | Paired history, idempotent, floor correct, warning logged |
| scripts/agent/session_message_repo.py (unchanged) | Regression | `uv run pytest tests/agent/test_session_message_repo.py` | Passes with zero changes to the file |
| All targets | Static + regression | `uv run pytest`, `uv run mypy scripts/`, `uv run ruff check scripts/`, `diff-cover` after Phase 2 | Clean, no findings |
| Backend behavior | Integration (dev DB + live backend, implementation phase) | Resume crafted orphaned session, inspect follow-up request | Sequence accepted; confirms synthesis strategy (UNK-01) |

## Risks
- **Risk**: Backend-behavior unknown (UNK-01) could invalidate the synthesis choice. →
  **Mitigation**: synthesis produces a standard well-formed sequence identical to existing
  synthetic completions already accepted by the backend in normal operation; Phase 3 live
  check with stop-and-report per the issue's AI instruction.
- **Risk**: Pairing detection misclassifies a legitimate multi-round sequence (assistant →
  tools → assistant → tools) if the contiguous-run rule is implemented loosely. →
  **Mitigation**: rule mirrors `tool_runner`'s emit order (all tool rows immediately after
  their assistant row); multi-round positive test included in Phase 2.
- **Risk**: undo_floor off-by-N after synthesis. → **Mitigation**: explicit insertion-count
  accounting + boundary test (AC-004); existing clamping logic in `restore_session` remains
  as the outer safety net.
- **Risk**: Memory-only synthesis makes `SessionRestoreResult.n_messages` (DB row count)
  diverge from restored history length. → **Mitigation**: repair log states both counts;
  result semantics documented in Phase 3 docs update.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Core repair logic | Completed | — | 20261027-185706 | Implement after turn001 plan Rows 01-03 implemented; full suite 10232 passed, diff coverage 98% |
| 2 | Phase 2: Tests | Completed | — | 20261027-185706 | Rows 01-03 implemented; full suite 10232 passed, diff coverage 98% |
| 3 | Phase 3: Verification & documentation | Completed | — | 20261027-183906 | 110403_03 implemented; 4 doc checkers clean |

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
- **Source issue**: issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-071546
- **Related target files**: scripts/agent/services/session_restore.py,
  tests/agent/test_session_restore.py,
  docs/23_agent/agent_04_01_state-and-persistence-state-model.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; tool_runner.py BaseException evidence (L77-79) | scripts/agent/services/session_restore.py | Phase 1 | AC-001 | test_session_restore.py | Explicit in issue (symbol names corrected) |
| REQ-002 | Required Changes 2; Unresolved Questions 2 (synthesis chosen); tool_preparation.py L52-74 | scripts/agent/services/session_restore.py | Phase 1 | AC-001 | test_session_restore.py | Explicit in issue |
| REQ-003 | Required Changes 3 | scripts/agent/services/session_restore.py | Phase 1 | AC-002 | test_session_restore.py | Explicit in issue |
| REQ-004 | Constraints 3 (idempotency); Testing Expectations 3 | scripts/agent/services/session_restore.py | Phase 1 | AC-003 | test_session_restore.py | Explicit in issue |
| REQ-005 | Derived: `_boundary_to_index` interaction with inserted rows (session_restore.py L26-45) | scripts/agent/services/session_restore.py | Phase 1 | AC-004 | test_session_restore.py | Derived from confirmed evidence |
| REQ-006 | Constraints 2 + Out of Scope (no write-path change) | scripts/agent/services/session_restore.py | Phase 3 | AC-005 | diff-scope check + test_session_message_repo.py regression | Explicit in issue |
| REQ-001..REQ-003 | Testing Expectations 1-3 | tests/agent/test_session_restore.py | Phase 2 | AC-001..AC-004 | test_session_restore.py | Explicit in issue |
| REQ-002, REQ-003 | Documentation Impact | docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Phase 3 | N/A: documentation check via check_doc_claims.py | N/A: documentation only | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-110403 -->