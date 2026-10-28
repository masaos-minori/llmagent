# Plan: Give the background-failure pause a resume path (keep + success-based clear)

**Generated from**: `issues/20261026-225036_bgmonitor001_reset-background-failure-pause.md`
**Date**: 2026-10-27
**Task classification**: Path A — small bounded fix (one method branch, one test module,
one doc paragraph)

## Goal

Give the opt-in background-failure pause a resume path: a clean completion of a paused
task type clears that type's pause entry. Failure counting, threshold logging, the
blocking check, and the opt-in constructor wiring stay intact (owner decision: keep the
mechanism; no config wiring).

## Priority

Medium (inherited from the issue).

## Scope

**In scope:**

- REQ-1: `BgTaskMonitor.on_task_done`'s clean-completion branch clears the task type's
  pause entry in `_bg_pause_state`.
- REQ-2: preserve failure counting, threshold notification/logging, the
  `check_pause_state()` blocking check, and `pause_on_critical_failure` as a
  constructor-only opt-in.
- REQ-3: documentation updated to the resume semantics.
- REQ-4: regression tests for breach → paused → success → unpaused.

**Out of scope:**

- OUT-1: wiring `pause_on_critical_failure` or the threshold value through config /
  models-settings — explicitly declined by the owner; the issue's "if kept: wire config"
  branch is NOT taken.
- OUT-2: background task scheduling or health-check internals (issue Out of Scope).
- Removal of any part of the pause mechanism (removal branch not taken).

## Background

The issue (from a `python-code-review` pass, finding F-008) reports a dormant,
half-wired pause mechanism: `bg_task_monitor.py` sets pause state at a critical-failure
threshold, no code ever clears it, and `pause_on_critical_failure` is hardcoded False
with no config key.

Verification against current source:

- Current behavior — `bg_task_monitor.py` `on_task_done()` (L73-100): cancelled → counter
  0 (DR-002); clean completion → counter 0 (L90-91); failure → failure ladder.
  `_bg_pause_state` is set only at L168-169 (`_notify_threshold_breach`, gated by
  `_pause_on_critical_failure`) and cleared nowhere — repo-wide grep confirms
  `bg_pause_state` is referenced only in `bg_task_monitor.py` and `orchestrator.py` L158.
- Stale claim corrected: no pause check exists in `repl_input_loop.py` (zero grep
  matches). Blocking happens in `orchestrator.handle_turn` (L158-160 →
  `_on_pause_blocked` L197-205, which notifies the user). The issue describes neither
  the file nor the silent behavior correctly.
- Stale claim corrected: `config_validators.py` no longer accepts
  `critical_failure_threshold` / `critical_failure_window` — repo-wide grep
  (py/json/md, excluding `issues/`) finds zero references; that half-wiring was already
  removed. The threshold is the module constant `BG_FAILURE_THRESHOLD: int = 10`
  (`bg_task_monitor.py` L21).
- Documented behavior — `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`
  L91-94, L131: pause is opt-in, per-task-type, "held only in process memory and
  persists until the process restart".
- Existing tests: `tests/agent/test_orchestrator.py` L2490-2527 (pause set / pause
  disabled characterization), `tests/agent/test_orchestrator_bg_failure_threshold.py`.

## Problem

Once enabled, a threshold breach pauses that task type for the remainder of the process
with no resume path other than restart — a sticky pause (issue Problem section).

## Reason for Change

Latent operational hazard per the issue: the first user of the opt-in flag gets an
unrecoverable pause within the session. Owner decision recorded during this
issue-to-plan cycle (2026-10-27): keep the mechanism, add success-based clear, do not
add config wiring. This closes the issue's Unresolved Question.

## Implementation Intent

Keep-and-finish with the minimal resume: extend the existing clean-completion branch in
`on_task_done` (which already resets the failure counter) to also clear the pause entry
for the same task type. Cancellation keeps the pause (DR-002: cancellation is neither
success nor failure). No public API change, no config key, no orchestrator change.

## Requirements

| ID | Requirement | Issue Evidence | Reason It Solves It | Scope Decision | Basis |
|----|-------------|----------------|---------------------|----------------|-------|
| REQ-1 | A clean completion of a paused task type clears that type's pause entry | Problem: "one threshold breach silences all future turns ... no documented way to resume"; owner decision | Next success of the same type re-enables turns automatically | In | owner decision (issue Unresolved Question resolved: keep + success-based clear) |
| REQ-2 | Counting, threshold logging, blocking check, and opt-in wiring behaviorally unchanged | Constraints: "do not remove counting, only the pause behavior if removal is chosen" | Keeps documented notification/blocking semantics intact | In | Explicit in issue Constraints + owner decision |
| REQ-3 | Docs describe the resume semantics | Documentation Impact section | agent_03_01 L93/L131 "persists until the process restart" becomes false after REQ-1 | In | Explicit in issue |
| REQ-4 | Regression test: breach → paused → success → unpaused | Testing Expectations | Locks the resume path | In | Explicit in issue |
| OUT-1 | config wiring of `pause_on_critical_failure` / threshold | Implementation Intent "If kept: wire ... config" | Owner declined this branch explicitly | Out | owner decision |
| OUT-2 | scheduling / health-check internals | Out of Scope section | — | Out | Explicit in issue |

## Implementation Target Files

**Freeze status**: Frozen (`issue-to-plan` Step 8 Implementation Target Files
Validation passed — structure check exit 0, all three target paths verified against
source and docs registry, overlap check reports no finding for this Plan.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
implementation skill — including file paths inside inline code snippets — MUST reference
exactly these paths and no others. When a discovered need does not map onto any row, it
is an unresolved question that reopens the Plan — not something the skill may resolve by
inventing a file.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/bg_task_monitor.py | `on_task_done` clean-completion branch also clears `_bg_pause_state[task_name]`; cancelled branch and failure ladder unchanged | `_bg_pause_state` is set only at L168-169 and cleared nowhere (repo grep); clean completion already resets the counter at L90-91 | REQ-1, REQ-2 | Read: `on_task_done` L73-100, `_notify_threshold_breach` L151-171, DR-002 docstring L76-78 | tests/agent/test_orchestrator_bg_failure_threshold.py | Verified |
| tests/agent/test_orchestrator_bg_failure_threshold.py | Add resume-path cases: same-type clean success clears pause; cancellation does not; other-type success does not | Existing tests cover breach-set/disable only (test_orchestrator.py L2490-2527) | REQ-1, REQ-2, REQ-4 | Read: pause characterization tests present; no resume test exists | this file | Verified |

Deferred target row (not touched during `python-implementation`; executed in the
workflow's Step 10 docs phase per the docs row rule):

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/23_agent/agent_03_01_turn-processing-flow-overview.md | Replace "persists until the process restart" with success-based resume semantics | L93/L131 become stale after REQ-1 | REQ-3 | Read: L91-94, L131 | N/A: documentation only | Verified |

## Reference Files

These files are read-only for context and MUST NOT be modified; any change to them
requires reopening the Plan with an explicit decision recorded under Assumptions.

| Path | How to use it | Requirements |
|------|---------------|------------|
| `scripts/agent/orchestrator.py` | L158-160 `check_pause_state()` gate and `_on_pause_blocked` (L197-205): the consumer contract the cleared state must satisfy; unchanged | REQ-1, REQ-2 |
| `tests/agent/test_orchestrator.py` | L2490-2527 existing pause characterization tests define the breach-set behavior that must stay green | REQ-2 |
| `scripts/agent/bg_task_monitor.py` | L35-36 docstring (DR-002 cancellation semantics), L21 threshold constant | REQ-2 |

## Acceptance Criteria

- REQ-1: after a breach pauses a task type, a clean completion of the same task name
  clears `bg_pause_state` so `check_pause_state()` returns `(False, [])`.
- REQ-2: existing pause characterization tests stay green unchanged
  (`test_threshold_reached_with_pause_enabled_sets_pause_state`,
  `test_threshold_reached_with_pause_disabled_leaves_pause_state_empty`); no config key
  added.
- REQ-3: no "persists until the process restart" claim remains for pause state in
  `agent_03_01_turn-processing-flow-overview.md`.
- REQ-4: new tests for success-clear, cancellation-no-clear, and other-type-success-no-clear
  are green.

## Tests

| Test target | Tool | What it proves | Requirements |
|-------------|------|----------------|------------|
| `tests/agent/test_orchestrator_bg_failure_threshold.py` (new cases) | pytest | same-type clean success resumes; cancellation does not; other-type success does not | REQ-1, REQ-2, REQ-4 |
| `tests/agent/test_orchestrator.py -k pause` (existing) | pytest | breach-set / disabled behaviors unchanged | REQ-2 |
| full suite (`uv run pytest`) | pytest | no collateral regression | REQ-1, REQ-2 |

## Documentation Impact

- `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`: pause persistence
  statements (L93, L131) updated to success-based resume (REQ-3).
- `docs/00_index.md`: no mapping change.

## Assumptions

- Owner decision (2026-10-27, this cycle): keep + success-based clear + no config wiring.
- Cancellation must not resume (DR-002 cited in `bg_task_monitor.py` docstring L76-78).
- `orchestrator.py` and `repl_input_loop.py` need no change (verified by grep and read).

## Unknowns

- None open. The issue's keep-or-remove question was resolved by the owner before
  drafting.

## Affected areas

| Area | Change | Blast radius | Requirements |
|------|--------|--------------|------------|
| background failure monitoring | clean completion also clears pause | `on_task_done` branch only | REQ-1 |
| turn blocking semantics | unchanged logic; state now clearable | none (read path untouched) | REQ-2 |
| docs | resume semantics paragraph | one doc | REQ-3 |

## Design

`on_task_done` already treats clean completion as "reset the streak" (L90-91, `count = 0`).
The resume is the same event clearing the same task type's pause entry — symmetric with
the counter reset, requiring no new state, API, or config surface. The issue's alternative
"acknowledgement command" resume is not needed: success-based clear is the owner-chosen
path and requires no REPL surface change. Removal was rejected: the mechanism is
documented (agent_03_01), tested, and opt-in.

## Implementation steps

1. `scripts/agent/bg_task_monitor.py` (REQ-1, REQ-2): in `on_task_done`'s clean-completion
   branch, clear this task name's pause entry (`self._bg_pause_state.pop(task_name, None)`)
   alongside `count = 0`. Cancelled and failure branches unchanged.
2. `tests/agent/test_orchestrator_bg_failure_threshold.py` (REQ-1, REQ-2, REQ-4): add (a)
   same-type clean success after a breach clears pause and `check_pause_state()` returns
   `(False, [])`; (b) cancelled task after a breach keeps the pause; (c) a different task
   name's success does not clear another type's pause.
3. Step 10 docs phase (REQ-3): update `agent_03_01_turn-processing-flow-overview.md` L93/L131.

Step 1 → Step 2 (tests exercise the new branch); Step 3 is deferred to the docs phase.

## Validation plan

| Check | Command | Expected | Requirements |
|-------|---------|----------|------------|
| targeted tests | `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py tests/agent/test_orchestrator.py -k "pause or threshold or failure"` | all green | REQ-1, REQ-2, REQ-4 |
| full suite | `uv run pytest` | green | REQ-1, REQ-2 |
| config-boundary grep | `grep -rn "pause_on_critical_failure" configs/ scripts/agent/services/` | no config wiring appears | OUT-1 boundary |
| lint/type/security | `uv run ruff check . && uv run ruff format --check . && uv run mypy scripts/ && uv run bandit -c bandit.yaml -r scripts/ -q` | clean | REQ-1 |

## Risks

| Risk | Likelihood | Impact | Mitigation | Affected requirements |
|------|------------|--------|------------|-----------------------|
| A single lucky success masks a systemic fault (pause clears "too eagerly") | Medium | Medium | Clear is same-task-type only and only on clean completion — exactly the event that already resets the failure counter; semantics stay symmetric | REQ-1 |
| Docs contradict code between Step 1 and Step 3 | Medium | Low | Known interim window; Step 10 docs phase closes it (flagged in Assumptions/Documentation Impact) | REQ-3 |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `scripts/agent/bg_task_monitor.py` clean-completion pause clear (REQ-1, REQ-2) | Completed | — | 20261028-123236 | P1: resume path |
| 2 | `tests/agent/test_orchestrator_bg_failure_threshold.py` resume-path regression cases (REQ-1, REQ-2, REQ-4) | Completed | — | 20261028-123236 | P2: regression tests |
| 3 | Step 10 docs phase: `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` L93/L131 (REQ-3) | Completed | — | 20261028-123236 | P3: deferred docs phase |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-235926_01_scripts_agent_bg_task_monitor.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261027-235926_02_tests_agent_test_orchestrator_bg_failure_threshold.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-235926_03_docs_23_agent_agent_03_01_turn-processing-flow-overview.md.md | 3 | Procedure | Pending | — | — |

## Traceability

- **Workflow phase**: `issue-to-plan`
- **Source issue**: `issues/20261026-225036_bgmonitor001_reset-background-failure-pause.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the plan
- **Source implementation procedure**: N/A: not yet generated
- **Generated at**: 20261027-085246
- **Related target files**: `scripts/agent/bg_task_monitor.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`, `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-235926 -->