## Goal
- Make `memory_disabled` an accurate per-turn degraded-state flag instead of a one-way
  latch: clear it when a later injection attempt succeeds, log/notify only on state
  transitions, and document the memory-degraded state.

## Priority
Medium (source issue priority: Medium)

## Scope
- **In-Scope**:
  - Clear `conv.memory_disabled` (and reset `memory_warning_shown`) when
    `handle_memory_injection` completes without exception.
  - Transition-only warning logging in the injection failure handler (no per-turn log
    spam when a failure persists).
  - Regression tests for flag transitions: failure -> degraded -> success -> recovered ->
    failure again re-warns; persistent failure logs once.
  - Field-semantics comment update and docs entry for the degraded state.
- **Out-of-Scope**:
  - Memory subsystem internals (retrieval, storage schema) — issue Out of Scope.
  - Startup abort policy — unchanged; `startup_prompt_setup.py` stays as-is (verified:
    its flag set is already recovered per-turn by the new clear-on-success rule, so no
    code change is needed there).
  - A `/memory` subcommand for permanent disable — not needed: the flag is not a
    functional gate (see Design), so no permanent-disable UX is added.
  - Approval/turn-flow changes elsewhere in `workflow_engine_adapter.py`.
- **Dependencies**: N/A: none. (Note: `context.py` and
  `scripts/agent/conversation_state_manager.py` are also targeted by the Frozen Plan
  `plans/20261027-070403_turn001_atomic-turn-persistence.md` — see Assumptions for the
  Step 8b overlap judgment.)

## Background
- From python-code-review finding F-004. Verified against current source with one
  significant correction to the issue's premise:
  - `conversation_state_manager.handle_memory_injection` sets `ctx.conv.memory_disabled =
    True` on injection failure (L144) — confirmed.
  - `startup_prompt_setup.py` sets it on startup read failure (L81) — confirmed.
  - No code path resets it to `False` — confirmed (grep: only L144/L81 assign True).
  - **Correction**: the issue assumes the flag disables memory for the rest of the
    session. It does not gate anything: `handle_memory_injection` is called every turn
    (`workflow_engine_adapter.py` L321, no `memory_disabled` check anywhere), so
    injection already retries on every subsequent turn. What is permanently wrong today
    is (a) the flag's accuracy — it stays `True` even after later successes, making the
    status/warning misleading; (b) per-turn `logger.warning` spam on persistent failure
    (L143); (c) `memory_warning_shown` never resets, so a second degradation period in
    the same session is silent.
  - Display paths confirmed: `repl.py` L132-139 (startup), `repl_input_loop.py` L246-247
    (first degraded turn) — both one-shot via `memory_warning_shown`.

## Problem
- A transient failure leaves `memory_disabled=True` and `memory_warning_shown=True` for
  the whole session even after injection recovers, so the user-visible degraded state is
  permanently misleading, persistent failures log every turn, and a later genuine
  degradation goes unnoticed.

## Reason for Change
- Accurate degraded-state visibility and bounded logging; the recovery mechanism
  (per-turn retry) already exists and only needs correct flag bookkeeping.

## Implementation Intent
- In `handle_memory_injection` (`scripts/agent/conversation_state_manager.py`):
  - Success path (no exception from `memory.on_user_prompt`): if `memory_disabled` was
    True, set it to False, reset `memory_warning_shown` to False, and log one warning
    marking recovery.
  - Failure path: set `memory_disabled = True`; log the warning only on the
    False->True transition (already-degraded failures log at debug level only); keep the
    existing `memory_warning_shown` gating for the user-facing prompt.
- No changes to the injection call site, startup paths, or REPL display logic — they
  already consume these two flags correctly once the bookkeeping is right.

## Requirements
- `REQ-001`: After an injection attempt completes without exception,
  `conv.memory_disabled` is `False` (cleared on success, including when no snippets were
  returned).
- `REQ-002`: On recovery from a degraded state, `conv.memory_warning_shown` is reset to
  `False` so a later degradation re-warns once per degradation period.
- `REQ-003`: On persistent failure across multiple turns, the failure is logged at warning
  level only on the False->True transition; subsequent degraded turns log at debug level
  and the turn is not delayed or raised (bounded, no spam).
- `REQ-004`: `ConversationState.memory_disabled` field comment reflects the per-turn
  degraded-state semantics (no longer "failed during startup").
- `REQ-005`: Docs state the degraded state: when it appears, that injection is retried
  every turn, and how the user can tell (one warning per degradation period).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/conversation_state_manager.py | Clear `memory_disabled` + reset `memory_warning_shown` on successful injection; transition-only failure logging | Flag is set True at L144 and never cleared; failure logs `logger.warning` every turn (L143) | REQ-001, REQ-002, REQ-003 | Read: `handle_memory_injection` L121-147; called per turn from `workflow_engine_adapter.py` L321 with no gate | tests/agent/test_memory_injection_recovery.py | Verified |
| scripts/agent/context.py | Update `memory_disabled`/`memory_warning_shown` field comments to per-turn degraded-state semantics | Comments say "failed during startup" (L110-111), contradicting per-turn reality | REQ-004 | Read: `ConversationState` field comments L110-111 | tests/agent/test_memory_injection_recovery.py (semantics pinned behaviorally) | Verified |
| tests/agent/test_memory_injection_recovery.py | New regression module: failure->degraded->success->recovered->failure re-warns; persistent failure logs once; no turn stall | No existing test covers flag recovery (grep: `memory_disabled` tests assert the latch behavior only) | REQ-001, REQ-002, REQ-003 | New file; no name collision (`ls tests/agent`) | — | Verified |
| docs/23_agent/agent_11_01_memory-overview-and-modes.md | Add degraded-state subsection (appearance condition, per-turn retry, user-visible signal) | Issue Documentation Impact; no docs entry exists today (`grep memory_disabled docs/` empty) | REQ-005 | `docs/23_agent/agent_00_document-guide.md` maps memory chapter to agent_11; file exists | N/A: documentation only | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/workflow_engine_adapter.py | Confirms `handle_memory_injection` is invoked every turn inside the execute stage (L321) — the existing retry mechanism this Plan builds on; MUST NOT be modified | scripts/agent/conversation_state_manager.py; REQ-001 |
| scripts/agent/startup_prompt_setup.py | Startup failure path (L81) sets the flag; confirms no startup change is needed because the new clear-on-success rule recovers it | scripts/agent/conversation_state_manager.py; REQ-001 |
| scripts/agent/repl.py | Startup degraded warning path (L132-139) — consumes the two flags unchanged | scripts/agent/conversation_state_manager.py; REQ-002 |
| scripts/agent/repl_input_loop.py | First-degraded-turn warning path (L246-247) — consumes the flags unchanged | scripts/agent/conversation_state_manager.py; REQ-002 |
| tests/agent/test_startup_prompt_setup.py | Existing startup-failure expectations that must pass unchanged | scripts/agent/conversation_state_manager.py; REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001): Test: injection fails once -> `memory_disabled` True; next attempt
  succeeds -> `memory_disabled` False.
- `AC-002` (REQ-002): After recovery, a subsequent failure warns again (warning emitted
  once per degradation period); user-facing `memory_warning_shown` gating re-arms.
- `AC-003` (REQ-003): N consecutive failed turns produce exactly one warning log (plus
  debug-level repeats); no exception propagates into the turn.
- `AC-004` (REQ-004): Field comments describe per-turn degraded-state semantics.
- `AC-005` (all): Existing memory tests pass unchanged
  (`tests/agent/commands/test_memory_status.py`, `test_cmd_memory.py`,
  `tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_orchestrator.py`,
  `tests/integration/test_orchestrator_integration.py`); `mypy`/`ruff` pass.

## Tests
- New `tests/agent/test_memory_injection_recovery.py`: flag transition sequence with a
  fake memory service (fail, succeed, fail), asserting AC-001..AC-003 including
  transition-only warning counts via a log capture fixture.
- Regression (unchanged files): the suite listed in AC-005.

## Documentation Impact
- Yes. Per `docs/23_agent/agent_00_document-guide.md` (memory chapter 11), add the
  degraded-state note to `docs/23_agent/agent_11_01_memory-overview-and-modes.md`
  (Implementation Target Files row): appearance condition, per-turn automatic retry,
  one-warning-per-degradation-period signal. Driven by REQ-005. Run
  `tools/check_doc_claims.py` after the doc edit per `routing.md`.

## Assumptions
- Step 8b overlap judgment (pre-registered): `scripts/agent/context.py` and
  `scripts/agent/conversation_state_manager.py` are also targeted by the Frozen Plan
  `plans/20261027-070403_turn001_atomic-turn-persistence.md` — judged **compatible**:
  turn001 touches ConvState snapshot/restore and csm write routing; this Plan touches the
  memory-degraded flags and injection logging (disjoint members). Implement either order;
  re-run `check_plan_target_overlaps.py` at freeze.
- `memory_disabled` has no functional consumers beyond the two warning-display paths
  (verified by repo-wide grep: 5 references, none gating execution) — so changing its
  lifecycle cannot alter turn behavior.
- Empty-snippet success counts as "healthy injection" for clearing the flag (the failure
  signal is the exception, not empty results).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Issue Unresolved Question: whether permanent disable was intentional | Resolved by repository evidence: the flag never gated execution, so no permanent-disable semantics exist to confirm or preserve | None needed; recorded in Background | False |
| UNK-02 | Whether `/memory status` should also surface the degraded flag | `MemoryStatus` (memory service dataclass) has no injection-state field; plumbing `conv` state into it touches the memory service boundary | Out of scope for this Plan (issue allows "status or warning path"; the warning path is used). File as a follow-up only if the user wants status visibility | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/conversation_state_manager.py | Injection flag bookkeeping + logging | Orchestrator-owned turn phase; behavior-visible only in warnings | 2 | 1 (dominant author >70%) | File sync |
| scripts/agent/context.py | Comment-only field semantics | `ConversationState` used broadly but no code change | 8 | 1 (dominant author >70%) | File sync |
| tests/agent/test_memory_injection_recovery.py | New test module | Test-only | — | — | N/A: tests not deployed |
| docs/23_agent/agent_11_01_memory-overview-and-modes.md | Docs section | Docs only | — | — | N/A: docs not deployed |

## Design
- Path A. The existing architecture already retries injection every turn
  (`workflow_engine_adapter._run_execute_stage` -> `handle_memory_injection`, L321); the
  defect is bookkeeping inside `handle_memory_injection` only. Fix confined to that method
  (per the issue's AI instruction: stay inside the injection-failure boundary).
- State machine: healthy(False) --failure--> degraded(True, warn once) --success-->
  healthy(False, warn-once recovery notice, re-arm warning flag) — bounded by turn count
  (one attempt per turn), so no separate backoff is needed; a persistent failure costs one
  `on_user_prompt` call per turn and one warning total.
- Logging rule: warning only on transitions (False->True and True->False); steady-state
  degraded turns log debug. This satisfies the "bounded retries / no log spam" constraint
  without adding timers (no timers in the Code Mode runtime — and none needed in the agent
  either: retry cadence equals turn cadence).
- Success detection = `memory.on_user_prompt` returns (even empty list); the exception is
  the failure signal, matching the current except-block semantics.

## Implementation steps
1. **Phase 1: Flag bookkeeping in the injection handler**
   - [ ] Clear-on-success + re-arm `memory_warning_shown` + transition-only logging in
     `handle_memory_injection` (REQ-001, REQ-002, REQ-003;
     scripts/agent/conversation_state_manager.py)
   - [ ] Update field comments to per-turn degraded-state semantics (REQ-004;
     scripts/agent/context.py)
2. **Phase 2: Tests**
   - [ ] New transition/logging regression module (REQ-001..REQ-003;
     tests/agent/test_memory_injection_recovery.py)
   - [ ] Run AC-005 regression suites unchanged (REQ-001..REQ-003)
3. **Phase 3: Verification & documentation**
   - [ ] Full validation per `rules/toolchain.md` (`uv run pytest`, `uv run mypy scripts/`,
     `uv run ruff check scripts/`) (AC-005)
   - [ ] Add degraded-state section to the memory overview doc + run
     `tools/check_doc_claims.py` (REQ-005; docs/23_agent/agent_11_01_memory-overview-and-modes.md)
   - [ ] Deployment check: `deploy/deploy.sh` syncs the two source files; no config/schema
     change (all REQ)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/conversation_state_manager.py | Unit with fake memory service (fail/succeed sequences) | `uv run pytest tests/agent/test_memory_injection_recovery.py` | AC-001..AC-003 pass; warning count per degradation period == 1 |
| scripts/agent/conversation_state_manager.py (existing behavior) | Regression | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py tests/agent/test_startup_prompt_setup.py` | Pass unchanged |
| scripts/agent/context.py | Comment-only; behavior pinned by the new tests | `uv run mypy scripts/ && uv run ruff check scripts/` | Clean |
| docs/23_agent/agent_11_01_memory-overview-and-modes.md | Docs claim check | `uv run python tools/check_doc_claims.py` | Pass |

## Risks
- **Risk**: Clearing on empty-success could mask a memory backend that "succeeds" while
  returning nothing useful. → **Mitigation**: success = call returned without exception,
  matching current failure semantics; retrieval quality is explicitly out of scope
  (issue Out of Scope).
- **Risk**: Resetting `memory_warning_shown` on recovery makes repeated flapping sessions
  noisy (one warning per flap). → **Mitigation**: flapping implies flapping failures which
  are also user-relevant; per-transition warning is the issue's intended behavior
  ("re-show a degraded-state indicator"); steady-state degraded turns stay quiet
  (AC-003 test).
- **Risk**: Overlap with the Frozen turn001 Plan on `context.py` /
  `conversation_state_manager.py` if implemented concurrently. → **Mitigation**: disjoint
  members per the Assumptions judgment; implement turn001 first if both are scheduled in
  the same window.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Flag bookkeeping in the injection handler | Completed | — | 20261027-185706 | Rows 01-04 implemented; full suite 10235 passed, diff coverage 98% |
| 2 | Phase 2: Tests | Completed | — | 20261027-185706 | Rows 01-04 implemented; full suite 10235 passed, diff coverage 98% |
| 3 | Phase 3: Verification & documentation | Completed | — | 20261027-185706 | Rows 01-04 implemented; full suite 10235 passed, diff coverage 98% |

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
- **Source issue**: issues/20261026-224838_memory001_retry-memory-injection-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-072306
- **Related target files**: scripts/agent/conversation_state_manager.py,
  scripts/agent/context.py, tests/agent/test_memory_injection_recovery.py,
  docs/23_agent/agent_11_01_memory-overview-and-modes.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; corrected by repository evidence (per-turn call at workflow_engine_adapter.py L321) | scripts/agent/conversation_state_manager.py | Phase 1 | AC-001 | test_memory_injection_recovery.py | Confirmed by repository evidence |
| REQ-002 | Required Changes 2 (degraded indicator re-show) | scripts/agent/conversation_state_manager.py | Phase 1 | AC-002 | test_memory_injection_recovery.py | Explicit in issue |
| REQ-003 | Constraints 1 (bounded, no spam); AI Implementation Instruction (transition logging) | scripts/agent/conversation_state_manager.py | Phase 1 | AC-003 | test_memory_injection_recovery.py | Explicit in issue |
| REQ-004 | Derived: field comment contradicts per-turn semantics (context.py L110-111) | scripts/agent/context.py | Phase 1 | AC-004 | N/A: comment verified by review | Derived from confirmed evidence |
| REQ-005 | Documentation Impact | docs/23_agent/agent_11_01_memory-overview-and-modes.md | Phase 3 | N/A: documentation check via check_doc_claims.py | N/A: documentation only | Explicit in issue |
| REQ-001..REQ-003 | Testing Expectations 1-2 | tests/agent/test_memory_injection_recovery.py | Phase 2 | AC-001..AC-003 | test_memory_injection_recovery.py | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-112613 -->