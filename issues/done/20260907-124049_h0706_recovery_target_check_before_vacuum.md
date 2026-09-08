# Reject Workflow/EventBus recovery targets before running integrity check or VACUUM

## Priority
High

## Summary
`recover_corruption()` in `scripts/db/recovery.py` runs `_run_integrity_check(db_path, target)`
for every target — including `workflow`/`eventbus` — before checking whether automatic
recovery is even permitted for that target. The `workflow`/`eventbus` domain-policy rejection
(`action="no_recovery_allowed"`) only runs after the `CORRUPTION` branch is reached; if a
`workflow`/`eventbus` database is `HEALTHY`, `recover_corruption()` proceeds to call
`_vacuum_db(target)` — opening and running `VACUUM` against a database domain whose automatic
recovery/maintenance is supposed to be operator-controlled.

## Background
Confirmed by direct read of `scripts/db/recovery.py` lines 260-341 (`recover_corruption`): the
domain-policy check for `workflow`/`eventbus` (`if target in ("workflow", "eventbus")`, line
331) is reached only after the `HEALTHY` branch (lines 296-299) and the
`LOCK_CONTENTION`/`PERMISSION_FAILURE`/`INVALID_FORMAT` branch (lines 301-311) have both
already returned early — meaning it is control-flow-unreachable for any target whose database
is not in `CORRUPTION` or `UNKNOWN` state. `tests/db/test_db_recovery.py`'s
`test_recover_corrupt_workflow_prohibited`, `test_recover_workflow_uses_correct_db_path`, and
`test_recover_eventbus_uses_correct_db_path` all mock `_run_integrity_check` to return
`DbCondition.CORRUPTION` — none of them exercise the `HEALTHY` path for
`target="workflow"`/`"eventbus"`, so this gap is not caught by the existing test suite.

## Problem
ADR-008/ADR-011's decision (referenced at line 332, "ADR-011 Requirement #6") is that
automatic recovery is prohibited for `workflow`/`eventbus` — the current implementation only
enforces this for the `CORRUPTION` case. A healthy `workflow.sqlite`/`eventbus.sqlite` passed
to `recover_corruption(target="workflow")` (e.g. from a scheduled maintenance job or an
operator script that iterates all four targets uniformly) will have `VACUUM` executed against
it without any domain-policy check — `VACUUM` rewrites the entire database file and briefly
locks it, which is exactly the kind of prohibited automatic operation on workflow/eventbus that
ADR-008's decision is meant to prevent, per memo2.md's Issue H-07-06 requirement to "Reject
Workflow and EventBus... before opening, checking, vacuuming, copying, deleting, or replacing
any database."

## Reason for Change
An operator or scheduler that calls `recover_corruption()` uniformly across all four targets
(a plausible generic-maintenance usage pattern, since the function already accepts all four
target strings) will silently run `VACUUM` against `workflow`/`eventbus` whenever they happen
to be healthy, without any structured rejection — the domain-policy boundary that is enforced
for the corruption path is absent for the healthy path.

## Implementation Intent
Move the `target in ("workflow", "eventbus")` domain-policy check to the top of
`recover_corruption()`, before `_run_integrity_check()` is called at all — matching memo2.md's
H-07-06 requirement that rejection happen before any database access. Keep the existing
`unsupported_target` check (already correctly placed before any database access, per
`test_recover_unsupported_target`'s `mock_integrity.assert_not_called()`) as the pattern to
follow.

## Target Files or Areas
- `scripts/db/recovery.py` (`recover_corruption()`)
- `tests/db/test_db_recovery.py`

## Required Changes
- Move the `workflow`/`eventbus` domain-policy rejection (currently lines 330-338) to
  immediately after the existing `unsupported_target` check (currently lines 285-292), before
  `_run_integrity_check()` is called.
- Confirm `dry_run` mode also rejects `workflow`/`eventbus` before any database access
  (currently the dry-run `CORRUPTION` branch is unreachable for `workflow`/`eventbus` once the
  check moves earlier — verify no existing caller relies on dry-run behavior for these targets
  first).
- Add a test case: `target="workflow"`/`"eventbus"` returns `action="no_recovery_allowed"`
  when the underlying database is `HEALTHY`, with `_run_integrity_check` and `_vacuum_db` both
  asserted not-called (mirroring `test_recover_unsupported_target`'s
  `mock_integrity.assert_not_called()` pattern).

## Constraints
- Do not change the `unsupported_target` check's existing position or behavior (already
  correct).
- Do not change the `rag`/`session` code paths — this issue only reorders the
  `workflow`/`eventbus` rejection relative to `_run_integrity_check()`.
- Preserve the existing `action="no_recovery_allowed"` value and detail message wording — only
  its position in the control flow changes.

## Acceptance Criteria
- [ ] `recover_corruption(target="workflow")`/`"eventbus"` returns
      `action="no_recovery_allowed"` without calling `_run_integrity_check()`, for both
      healthy and corrupt underlying databases.
- [ ] `_vacuum_db()` is never called for `target="workflow"`/`"eventbus"`, regardless of the
      underlying database's actual state.
- [ ] New regression tests cover the `HEALTHY`-underlying-database case for both `workflow`
      and `eventbus`, asserting `_run_integrity_check`/`_vacuum_db` are not called.
- [ ] Existing `test_recover_corrupt_workflow_prohibited`, `test_recover_workflow_uses_correct_db_path`,
      `test_recover_eventbus_uses_correct_db_path` continue to pass unchanged (or are updated
      only to reflect the new assert-not-called expectation, without changing their asserted
      `action` value).

## Testing Expectations
`uv run pytest tests/db/test_db_recovery.py -v`; add the healthy-workflow/eventbus regression
tests described above.

## Documentation Impact
If a canonical recovery specification under `docs/` describes `recover_corruption()`'s control
flow or the `workflow`/`eventbus` prohibition, confirm it does not already claim rejection
happens before any database access — if it does, this issue is also a documentation/code
mismatch per `rules/coding.md`'s "Current behavior" classification ("Implementation fix
required").

## Out of Scope
- Do not implement Workflow/EventBus operator-runbook changes (already done, see
  `issues/done/20260903-110306_h0708_fix-workflow-eventbus-manual-recovery-runbook-to-use-backups.md`).
- Do not change the domain recovery policy itself (`workflow`/`eventbus` remain prohibited
  from automatic recovery either way).
- Do not add a generic fallback database or change `unsupported_target` handling.

## Dependencies
Depends on `issues/done/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md`
(H-07-01) and this batch's structured-classification issue (classification feeding into the
reordered control flow).

## Unresolved Questions
Whether any current caller of `recover_corruption(target="workflow"/"eventbus", dry_run=True)`
depends on the current (post-integrity-check) rejection point's behavior for dry-run mode —
confirm no caller relies on this before moving the check; if one does, adjust rather than
silently breaking it.

## AI Implementation Instruction
This is a control-flow reordering, not a new feature — do not add new `action` values or
change the `no_recovery_allowed` detail message. Search for all callers of
`recover_corruption(target="workflow"` / `target="eventbus"` before moving the check, to
confirm none depend on the current post-integrity-check timing (e.g. for logging side effects
from `_run_integrity_check` that would no longer run).
