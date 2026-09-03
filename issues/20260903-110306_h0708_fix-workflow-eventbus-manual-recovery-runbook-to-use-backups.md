# Fix the workflow.sqlite / eventbus.sqlite manual recovery runbook to use existing backups

## Priority
Medium

## Summary
Replace the current "Manual Recovery: workflow.sqlite / eventbus.sqlite" runbook, which discards the corrupted database and rebuilds an empty one via `.dump`/`.sql`, with a runbook that uses the backups `rotate_all_dbs()` already takes for these two domains. Keep automatic restoration prohibited and require explicit operator decisions.

## Background
The current approved policy treats Workflow and EventBus physical recovery as an operator-controlled process (ADR-008 Decision Details #20 / INV-18, `recover_corruption(target="workflow"|"eventbus")` returns `action="no_recovery_allowed"`). A runbook section titled "Manual Recovery: workflow.sqlite / eventbus.sqlite" already exists at `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` (confirmed by direct read, lines 87-107), produced by `plans/done/20260901-070239_plan.md`.

## Problem
The existing runbook's procedure does not use a backup at all: it copies the corrupted file aside as `*.corrupted`, attempts `sqlite3 ... ".dump"` on the *corrupted* file itself, and if that fails, creates an empty database via `touch` (confirmed by direct read, lines 92-104). This contradicts the runbook's own originating Plan, whose `REQ-001` confirmed `rotate_all_dbs()` already archives all four databases including workflow/eventbus (`scripts/db/rotation.py`, confirmed lines 76-77) and whose `REQ-003` required the runbook to cover locating available backups, validating a candidate, and applying it manually. Separately, `docs/90_shared_90_inconsistencies_and_known_issues.md`'s SHARED-003 entry still states "a documented step-by-step operator recovery runbook for these two domains does not yet exist" (confirmed by direct read) — this is itself stale, since the runbook section does exist; it is incomplete/incorrect, not absent (tracked for correction by `H-07-09`, filed alongside this issue).

## Reason for Change
A documented recovery procedure that ignores an existing, already-taken backup and instead attempts to dump a possibly-corrupted file (or silently discards all data via `touch`) can cause avoidable data loss precisely in the scenario the runbook exists to handle.

## Implementation Intent
Rewrite the runbook to describe the manual recovery procedure using the backups `rotate_all_dbs()` already produces for `workflow.sqlite` and `eventbus.sqlite`, covering what backup exists, how to validate a candidate, how to manually apply it, and what to do if no valid backup exists — retaining the `.dump`-based reconstruction attempt only as a documented last resort when no valid backup is available, not as the primary procedure.

## Target Files or Areas
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` (the existing "Manual Recovery: workflow.sqlite / eventbus.sqlite" section, lines 87-107)
- `docs/90_shared_90_inconsistencies_and_known_issues.md` (SHARED-003's stale "runbook does not exist" claim — cross-reference only; full reconciliation is `H-07-09`'s scope)
- `scripts/db/rotation.py` (`rotate_all_dbs()`, to confirm current backup path/retention/naming convention for workflow/eventbus before rewriting the runbook)
- `docs/adr/ADR-008-sqlite-4db-separation.md` (Related Documents cross-reference, if the runbook's location or structure changes)

## Required Changes
- Confirm the exact backup location, naming convention, and retention policy `rotate_all_dbs()` produces for `workflow.sqlite`/`eventbus.sqlite` before rewriting the runbook.
- Rewrite the runbook's primary procedure to: locate the most recent valid backup, validate it is a well-formed SQLite file for the correct domain, stop the agent process, apply the backup to the live path, and restart.
- Retain the current `.dump`-based reconstruction as an explicitly labeled last-resort fallback, used only when no valid backup exists — not as the default path.
- State explicitly what data loss the operator should expect (the delta between the backup's timestamp and the failure time) for both the backup-based path and the fallback path.
- Cross-reference (do not restate) `H-07-09`'s planned correction to SHARED-003's stale "runbook does not exist" claim.

## Constraints
- Do not implement any new automatic backup or recovery code — this issue is documentation-only.
- Do not contradict ADR-008's decision that automatic restoration is prohibited for these two domains.
- Do not remove the `.dump`-based fallback entirely — retain it as the documented last-resort path for when no valid backup exists.

## Acceptance Criteria
- [ ] The runbook's primary procedure locates, validates, and manually applies an existing backup for `workflow.sqlite`/`eventbus.sqlite`.
- [ ] The `.dump`-based reconstruction remains documented, but only as an explicit last resort when no valid backup exists.
- [ ] The runbook states the expected data-loss window for both paths.
- [ ] ADR-008's Related Documents still references the runbook section (verify no cross-reference was broken by the rewrite).
- [ ] `uv run python tools/check_docs_quality.py` shows no new issues for the affected document.

## Testing Expectations
Not required — documentation-only change.

## Documentation Impact
This issue is itself the documentation gap it closes — the runbook already exists but does not reflect the correct backup-based procedure.

## Out of Scope
- Implementing or changing `rotate_all_dbs()`'s backup coverage or retention policy.
- Changing ADR-008's recovery policy itself.
- Reconciling SHARED-003's full text or NC-021 (see `H-07-09`, filed alongside this issue).

## Dependencies
Depends on `H-07-01` (filed alongside this issue, defines the persistence-domain terminology this runbook's procedure is classified under — `operator-restore` for the backup-based path, a last-resort fallback for the `.dump`-based path).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm the actual current backup coverage, path, and naming convention for `workflow.sqlite`/`eventbus.sqlite` in `scripts/db/rotation.py` before rewriting the runbook — do not assume the backup location without reading the code. Read the existing runbook section in full (`docs/05_agent_10_01_operations-and-observability-startup-and-health.md` lines 87-107) before editing it, and preserve its warning about pending-approval/workflow-state loss. Do not delete the `.dump`-based fallback; relabel it as the last-resort path instead.
