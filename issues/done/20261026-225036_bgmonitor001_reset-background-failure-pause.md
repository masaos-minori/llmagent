# Give the background-failure pause a resume path or remove the dormant mechanism

## Priority
Medium

## Summary
The background-task failure counter can set a `pause` flag that is never cleared
anywhere, and the enabling switch (`pause_on_critical_failure`) is hardcoded False
with no config key. Either make the pause resumable and configurable, or remove the
dormant mechanism.

## Background
From a python-code-review pass over the REPL turn path (finding F-008). Evidence
(Explicit in code):
- `scripts/agent/bg_task_monitor.py` sets `pause` when consecutive background
  failures cross the critical-failure threshold; a repo-wide search finds no code
  that ever clears it.
- `scripts/agent/repl_input_loop.py` checks the flag and silently skips turns while
  paused (and prints "Background tasks paused" at the prompt).
- `scripts/agent/orchestrator.py` and `bg_task_monitor.py` default
  `pause_on_critical_failure=False`; no config key feeds it, while
  `config_validators.py` accepts `critical_failure_threshold` /
  `critical_failure_window` as valid models-settings keys.

## Problem
If the mechanism is ever enabled, one threshold breach silences all future turns
for the rest of the session with no documented way to resume. Today it cannot be
enabled from config even though its threshold keys are accepted — a dormant,
half-wired feature that reads as if it were operational.

## Reason for Change
Dormant safety mechanisms that cannot be resumed are a latent operational hazard:
the first person to wire the flag on gets a sticky pause. Leaving half-configured
code in place also misleads future maintainers about what is active.

## Implementation Intent
Decide keep-or-remove first. If kept: clear `pause` when the user acknowledges it
or when a background task succeeds, wire `pause_on_critical_failure` through config
with the other models-settings keys, and document the resume path. If removed:
delete the flag, the threshold fields, and their validator entries together.

## Target Files or Areas
- `scripts/agent/bg_task_monitor.py`
- `scripts/agent/repl_input_loop.py` (pause check paths)
- `scripts/agent/orchestrator.py` (construction wiring)
- `scripts/agent/services/config_validators.py` and config section builders

## Required Changes
- Keep-or-remove decision recorded before code changes.
- If kept: resume path (acknowledgement command or success-based clear), config key
  for `pause_on_critical_failure`, docs.
- If removed: delete `pause`, `pause_on_critical_failure`,
  `critical_failure_threshold`/`critical_failure_window` config acceptance, and the
  REPL pause checks.

## Constraints
- The consecutive-failure counting itself is used for logging; do not remove
  counting, only the pause behavior if removal is chosen.
- Do not change unrelated background-task scheduling.

## Acceptance Criteria
- Either: a test showing the pause is cleared by the chosen resume path, and the
  flag is settable via config; or: no `pause` references remain in
  `scripts/agent/` (grep assertion).
- All pause-related tests updated accordingly; suite green.

## Testing Expectations
- If kept: unit test threshold breach → paused → resume trigger → unpaused.
- If removed: repo grep confirms no dangling `pause`/`critical_failure` references;
  validator tests updated.

## Documentation Impact
Either document the pause/resume semantics as an operational behavior, or remove
any doc/config references consistent with removal (Known Issues / operational notes).

## Out of Scope
- Background task scheduling or health-check internals.

## Dependencies
- N/A: none

## Unresolved Questions
- 不明: whether the pause mechanism is slated for activation (keep-and-finish) or
  is vestigial (remove) — confirm with the project owner before implementing.

## AI Implementation Instruction
Resolve the keep-or-remove question first; do not implement a resume path and a
removal in the same change. If keeping, wire config through the existing
models-settings validation path rather than a new section. Keep failure counting and
its logging intact.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-225036
- **Related target files**: `scripts/agent/bg_task_monitor.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/orchestrator.py`, `scripts/agent/services/config_validators.py`
