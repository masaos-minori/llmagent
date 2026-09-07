# Fixed-duration settlement sleep in close_resources violates REQ-RSC002-3 (no shutdown-timing regression)

## Priority
Medium

## Summary
`issues/done/20260904-001051_rsc002_meaningless_sleep_timeout.md` required (REQ-RSC002-1) that the
shutdown timeout actually fire when operations don't settle, and (REQ-RSC002-3) that there be "no
regression in shutdown timing for healthy cases." Its implementation procedure
(`implementations/done/20260904-102208_01_scripts_agent_resource_shutdown_coordinator_py.md`)
replaced `asyncio.sleep(0)` with `asyncio.sleep(_GRACEFUL_TIMEOUT_S)` (confirmed present in the
current code at `scripts/agent/resource_shutdown_coordinator.py:145`), which satisfies
REQ-RSC002-1 but, by the procedure's own "Compatibility considerations" section, "increases
[shutdown latency] by approximately `_GRACEFUL_TIMEOUT_S` seconds (10s) on every shutdown" and "for
healthy shutdowns where all operations complete quickly, the sleep still waits the full duration"
— an unconditional regression the procedure documents but does not fix, while still marking its
own Step 1 `Completed`.

## Background
`Explicit in code`: `close_resources()` (`scripts/agent/resource_shutdown_coordinator.py:60`)
already gathers and awaits all `pending_tasks`' completion earlier in the same method (line 81,
`asyncio.gather(*pending_tasks, return_exceptions=True)`) before ever reaching the settlement
block at lines 144-147 (`await asyncio.wait_for(asyncio.sleep(_GRACEFUL_TIMEOUT_S),
timeout=_GRACEFUL_TIMEOUT_S)`). The implementation procedure's own "Adversarial Verification"
section already found this: "Plan proposal 'replace with asyncio.gather(*pending_tasks, ...)'
→ Invalidated: pending_tasks was already gathered in step 1 ..., then cancelled ...; re-gathering
would only yield CancelledError exceptions." Having ruled out re-gathering as redundant, the
procedure nonetheless introduced a second, unconditional 10-second sleep with no relationship to
whether anything is still pending — the settlement block waits `_GRACEFUL_TIMEOUT_S` seconds
regardless of whether cancellation already completed instantly at line 81.

## Problem
- Every shutdown — healthy or not — now unconditionally blocks for `_GRACEFUL_TIMEOUT_S` (10)
  seconds in the settlement block, even though the tasks it might be "waiting for" were already
  awaited to completion earlier in the same method. This directly violates REQ-RSC002-3 ("No
  regression in shutdown timing for healthy cases").
- The implementation procedure's own "Compatibility considerations" section names this exact
  regression and even proposes a fix ("Consider adding early-exit optimization: if no errors
  detected yet, skip the sleep") but the fix was never implemented — the section records it as a
  forward-looking suggestion, not applied work, while Step 1 is still marked `Completed`.
- REQ-RSC002-1 (timeout actually fires) is technically satisfiable now only in the pathological
  case where `asyncio.sleep(_GRACEFUL_TIMEOUT_S)` itself is somehow delayed past its own
  `timeout=_GRACEFUL_TIMEOUT_S` — an edge case that does not correspond to any real "operations
  not settling" scenario, since nothing in this block actually observes operation state.

## Reason for Change
An unconditional 10-second delay on every process shutdown is an operational cost (slower
restarts, slower deploys, slower test teardown wherever this path runs) introduced specifically to
fix a no-op timeout check — but the fix traded "timeout never fires" for "shutdown always takes
the full timeout," which the original issue's own acceptance criterion (REQ-RSC002-3) explicitly
prohibited.

## Implementation Intent
Remove the redundant unconditional sleep, or make the settlement wait conditional on genuinely
unresolved state (if any exists beyond what line 81's `gather()` already resolved). Since
`pending_tasks` are already fully awaited by that `gather()` call, the settlement block likely has
no remaining state to wait for at all — confirm this and, if so, remove the block (or reduce it to
purely defensive error handling with no artificial delay) rather than inventing a new condition to
gate it on.

## Target Files or Areas
- `scripts/agent/resource_shutdown_coordinator.py` (`close_resources()`, settlement block at
  lines 140-158)

## Required Changes
- Determine whether the settlement block (lines 140-158) has any remaining purpose given that
  `pending_tasks` are already awaited via `gather()` at line 81. If it has none, remove the
  unconditional `asyncio.sleep(_GRACEFUL_TIMEOUT_S)` call entirely.
- If some genuine post-cancellation settlement work remains unaccounted for (e.g. state outside
  `pending_tasks`), replace the fixed sleep with a check that waits only as long as needed for
  that specific state, up to `_GRACEFUL_TIMEOUT_S` as a ceiling — not as a fixed floor.
- Update the class docstring's "Settlement period" description to match whatever the resulting
  behavior actually is.

## Constraints
- Must not reintroduce the original no-op `asyncio.sleep(0)` defect — any change must still allow
  a genuine timeout to fire if something is actually still pending.
- Must not change `_GRACEFUL_TIMEOUT_S`'s value (10.0) — only how (or whether) the settlement
  block waits.
- Must preserve existing error-collection semantics (`errors` list, `logger.error` call) for the
  case a timeout genuinely does fire.

## Acceptance Criteria
- [ ] A healthy shutdown (all tasks already settled via the earlier `gather()`) completes without
      an unconditional additional `_GRACEFUL_TIMEOUT_S`-second wait.
- [ ] A shutdown where something is genuinely still unsettled still triggers the timeout error
      path and is collected in `errors`.
- [ ] `ResourceShutdownCoordinator`'s docstring accurately describes the resulting settlement
      behavior.
- [ ] No regression in existing `resource_shutdown_coordinator.py` tests.

## Testing Expectations
Add a test asserting shutdown completes promptly (well under `_GRACEFUL_TIMEOUT_S`) in the healthy
case; keep or add a test asserting the timeout path still fires and is recorded when something is
genuinely still pending. Run the full existing test suite for this module to confirm no
regression.

## Documentation Impact
Update `ResourceShutdownCoordinator`'s class docstring "Settlement period" section (added by the
prior procedure) to describe the corrected behavior.

## Out of Scope
- Re-verifying REQ-RSC001-2/the task-cancellation-ordering work tracked separately in this batch.
- Changing `_GRACEFUL_TIMEOUT_S`'s value.

## Dependencies
Follows `issues/done/20260904-001051_rsc002_meaningless_sleep_timeout.md` and its implementation
procedure — this issue re-opens only the REQ-RSC002-3 portion (shutdown-timing regression) that
procedure's own Compatibility considerations section flagged but did not fix.

## Unresolved Questions
Whether any state exists post-cancellation that genuinely needs a settlement wait beyond what
`gather()` at line 81 already resolves — if the implementer confirms none exists, removing the
block outright is the expected resolution; if some does exist, it was not identified by the prior
implementation procedure's own investigation and should be named explicitly before implementing a
conditional wait.

## AI Implementation Instruction
Re-read `scripts/agent/resource_shutdown_coordinator.py` in full before editing, and confirm
current line numbers via `rg -n "_GRACEFUL_TIMEOUT_S|asyncio.gather|asyncio.sleep"
scripts/agent/resource_shutdown_coordinator.py`. Do not simply shorten the sleep duration as a
workaround — either justify why a fixed wait is still needed after `gather()` already awaited
`pending_tasks`, or remove it. Do not touch the task-cancellation-ordering logic (lines 60-104),
which is tracked by a separate issue in this batch.
