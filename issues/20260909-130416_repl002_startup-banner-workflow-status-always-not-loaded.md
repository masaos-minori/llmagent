# `StartupBanner._get_workflow_status()` always reports "not loaded" — reads a nonexistent `ctx._orchestrator`

## Priority
Medium

## Summary
`TestGetWorkflowStatus::test_returns_unknown_when_orchestrator_is_none` and
`::test_returns_enabled_when_tracking_enabled` (`tests/agent/test_repl.py`) fail,
expecting `"unknown"`/`"enabled"` but observing `"not loaded"` in both cases. Confirmed
genuine production defect: `StartupBanner._get_workflow_status()`
(`scripts/agent/startup_banner.py`) reads `self._ctx._orchestrator`, but `AgentContext`
(`scripts/agent/context.py`) has no `_orchestrator` attribute at all — the real
orchestrator reference lives only on `AgentREPL._orchestrator`, never passed to
`StartupBanner`. In production, this means the startup banner's displayed workflow
status is always wrong.

## Background
`StartupBanner` is constructed as `StartupBanner(self._ctx, self._view)` in
`scripts/agent/repl.py` — no orchestrator reference is passed. `_get_workflow_status()`
attempts to read workflow-tracking state via `self._ctx._orchestrator`, presumably
intending to check whether an `Orchestrator` instance is attached and what its
workflow-tracking state is. `AgentContext` never defines or sets `_orchestrator` as an
attribute anywhere in `scripts/agent/context.py`.

## Problem
In production, `self._ctx` is a real `AgentContext` instance (not a mock), so
`self._ctx._orchestrator` raises `AttributeError` in normal Python — **except this method
is never actually exercised this way outside tests**, since `_get_workflow_status()`'s
real call site presumably guards or handles this somehow (unconfirmed — see Unresolved
Questions). In the tests specifically, `ctx` is a `MagicMock()`, so
`ctx._orchestrator` never raises — it auto-creates a fresh, unconfigured child
`MagicMock` on every access, causing `_get_workflow_status()` to always fall through to
its `"not loaded"` default branch, regardless of what orchestrator/tracking state the
test actually configures. This is why the third test in the same class,
`test_returns_not_loaded_when_tracking_not_loaded`, passes — only by coincidence, since
it happens to assert the one value this defect always produces. This has been present
since the file's creation and untouched by its one later commit.

## Reason for Change
The startup banner is a user-visible, first-thing-you-see status display. If this
defect means the real workflow status is never correctly read in production either
(not just in these mock-based tests), operators see an always-wrong "not loaded"
workflow status regardless of whether workflow tracking is actually enabled — a
misleading operational signal. If production somehow avoids hitting this path (e.g. a
guard this issue hasn't yet located), the defect is at minimum dead/unreachable-as-intended
code plus 2 tests providing false coverage.

## Implementation Intent
Confirm how `StartupBanner` is meant to obtain orchestrator/workflow-tracking state in
production — either (a) `StartupBanner` should receive an orchestrator reference (or a
narrower workflow-status-only dependency) via its constructor, matching how other
banner/status components in this codebase receive their dependencies explicitly rather
than reading private attributes off `ctx`, or (b) `AgentContext` should actually expose
`_orchestrator` (set by whatever wires up the REPL/Orchestrator relationship) if that
was the original intent and it was simply never wired. Do not guess between these
without checking `scripts/agent/repl.py`'s construction order and
`scripts/agent/context.py`'s full attribute set first.

## Target Files or Areas
- `scripts/agent/startup_banner.py` (`StartupBanner._get_workflow_status()`)
- `scripts/agent/repl.py` (reference — confirms `StartupBanner(self._ctx, self._view)`
  construction call and whether `self._orchestrator` is available at that point to pass
  through)
- `scripts/agent/context.py` (reference — confirms `AgentContext`'s actual attribute set
  has no `_orchestrator`)
- `tests/agent/test_repl.py` (`TestGetWorkflowStatus`, all 3 tests — 2 failing, 1
  passing by coincidence)

## Required Changes
- Determine the correct dependency-passing mechanism for `StartupBanner` to obtain
  orchestrator/workflow-tracking state (constructor parameter vs. an `AgentContext`
  attribute actually being set somewhere).
- Wire it correctly so `_get_workflow_status()` reads a real, present value instead of
  an always-nonexistent `ctx._orchestrator`.
- Update `TestGetWorkflowStatus`'s 3 tests to match the corrected dependency-injection
  mechanism (their intent — verifying `"unknown"`/`"enabled"`/`"not loaded"` per
  orchestrator/tracking state — stays the same; only how they configure the test double
  changes).

## Constraints
Do not change the three status strings (`"unknown"`/`"enabled"`/`"not loaded"`) or their
meaning — only the mechanism by which `_get_workflow_status()` obtains the state it
classifies.

## Acceptance Criteria
- [ ] `StartupBanner._get_workflow_status()` reads orchestrator/workflow-tracking state
  from a real, present source (no attribute access that unconditionally fails/auto-mocks)
- [ ] `uv run pytest "tests/agent/test_repl.py::TestGetWorkflowStatus" -q` passes for
  all 3 cases with each genuinely exercising its intended orchestrator/tracking-state
  scenario (not coincidentally passing)
- [ ] Manually confirm (or add a targeted test) that the real, non-mocked
  `AgentContext`/`StartupBanner` construction path in `scripts/agent/repl.py` does not
  raise `AttributeError` when the banner is actually rendered at startup

## Testing Expectations
- `uv run pytest "tests/agent/test_repl.py::TestGetWorkflowStatus" -q` — all 3 cases
  pass meaningfully
- Manual or scripted startup smoke check confirming the banner renders a correct,
  non-"not loaded" workflow status when workflow tracking is actually enabled

## Documentation Impact
State whether documentation must be updated: N/A unless a doc under
`docs/05_agent_*` (per `docs/00_index.md`'s task-scope mapping) currently describes the
startup banner's workflow-status display as working correctly — if so, no change needed
once this is fixed (the doc would already be accurate); check before closing.

## Out of Scope
- `TestReplLoop::test_signal_mid_turn_exits_within_graceful_timeout` — tracked
  separately, see Dependencies.
- `TestPersistSessionDiagnostics`'s 2 failures — tracked separately as `repl003`.
- `TestRunSqliteErrorMessage`'s 2 failures — tracked separately as `repl004`.
- `TestSigtermHandlerTurnActiveGuard`'s 1 failure — tracked separately as `repl005`.

## Dependencies
N/A: none. Discovered while investigating `test_repl.py`'s post-`repl001`-fix remaining
failures — independent of that fix.

## Unresolved Questions
Whether production code ever actually calls `_get_workflow_status()` on a real
`AgentContext` (in which case this is a live `AttributeError` risk, not just a
mock-masked test defect) — trace `scripts/agent/repl.py`'s actual banner-rendering call
path to confirm before implementing, rather than assuming based on the tests alone.

## AI Implementation Instruction
Trace the real (non-test) call path to `_get_workflow_status()` first — confirm whether
this is a live `AttributeError` in production or something this method's caller
currently guards against — before deciding the fix mechanism. Do not change the three
status strings' meaning.
