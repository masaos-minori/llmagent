## Goal
Add regression test coverage proving (1) a `llm_visibility_base=False` tool stays
`enabled_for_llm=False` after `apply_policy()` even when the tool name is in
`allowed_tools`, and (2) the new warning log (added by this Plan's Row 1,
`scripts/shared/runtime_tool_registry.py`) fires in that scenario and does not fire
for a `llm_visibility_base=True` tool.

## Scope
In scope: two new test functions/methods in the existing `TestApplyPolicy`-equivalent
test class of `tests/shared/test_runtime_tool_registry.py` (the class containing
`test_apply_policy_*`, confirmed at lines 126-263).
Out of scope: modifying any existing test in this file; modifying
`scripts/shared/runtime_tool_registry.py` itself (covered by this Plan's Row 1, a
separate implementation procedure document) — REQ-001 of `plans/20260920-203022_plan.md`.

## Assumptions
- Row 1 (`scripts/shared/runtime_tool_registry.py`) is implemented before or alongside
  this row, since AC-2's warning-log test depends on the `logger.warning(...)` call
  Row 1 adds — if Row 1 has not landed yet when this row is implemented, the new
  warning-log test will fail until Row 1 lands; this is expected and not a defect in
  this row's test.
- `caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry")` is the
  correct fixture pattern, following the existing precedent in
  `tests/shared/test_tool_executor_routing.py` (lines 111-130) for the sibling
  `shared.tool_executor` logger.

## Design decisions
- Reuse the existing `_registry_with(tool)` helper (already used by every other test in
  this class, confirmed via Read) rather than introducing a new fixture — keeps the new
  tests consistent with the file's existing style.
- Construct the `llm_visibility_base=False` fixture via `build_runtime_tool(...,
  enabled_for_llm=True, llm_visibility_base=False)` — explicitly passing both
  parameters, since `build_runtime_tool()`'s defaulting rule
  (`scripts/shared/runtime_tool.py:111-112`) would otherwise set
  `llm_visibility_base` equal to `enabled_for_llm`. Using `enabled_for_llm=True` with
  `llm_visibility_base=False` explicitly is what makes the test meaningful: it proves
  the *base* wins over the tool's own initially-enabled state, not merely that a
  never-enabled tool stays disabled.

## Alternatives considered
- Testing atomicity/concurrency in this same file/row: rejected — that is
  `plans/20260920-203342_plan.md`'s (REQ-002's sibling Plan) own scope, a separate
  implementation procedure document; this row is scoped to REQ-001 only, per
  `rules/workflow-lifecycle.md` Evidence-Only vs. Target Files and this Plan's own Row
  boundaries.

## Implementation
### Target file
`tests/shared/test_runtime_tool_registry.py`

### Procedure
1. Add `import logging` to the test file's imports if not already present (confirm via
   Read before adding — avoid a duplicate import).
2. Add `test_apply_policy_keeps_hidden_tool_disabled_when_allowed` to the
   `TestApplyPolicy`-equivalent class (immediately after the existing
   `test_apply_policy_empty_allowed_tools_keeps_all_enabled` method, to group with the
   other `apply_policy`-behavior tests): construct a tool with `enabled_for_llm=True,
   llm_visibility_base=False`, call `apply_policy(tier_map={}, allowed_tools=[<tool
   name>])`, and assert `enabled_for_llm is False` on the result.
3. Add `test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled`
   immediately after it: same fixture setup, wrap the `apply_policy()` call in
   `caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry")`, and
   assert the tool's name appears in `caplog.text`.
4. Add a companion negative-case assertion (either as part of the same test or a
   separate `test_apply_policy_does_not_log_warning_for_visible_tool`) confirming no
   warning is logged when `llm_visibility_base=True` under the same `allowed_tools`
   call — proving the log is specific to the hidden-tool-would-be-re-enabled case, not
   emitted unconditionally.

### Method
Direct file edit (`Edit` tool) — append new test functions to an existing test class;
no change to any existing test or fixture helper.

### Details
Existing fixture pattern (confirmed via Read, lines 126-150):
```python
def test_apply_policy_updates_tier_and_llm_visibility(self) -> None:
    tool = build_runtime_tool(
        name="shell_run", server_key="s", enabled_for_llm=True
    )
    reg = _registry_with(tool)
    reg.apply_policy(tier_map={"shell_run": "ADMIN"}, allowed_tools=["shell_run"])
    updated = reg.get("shell_run")
    assert updated.agent_safety_tier == "ADMIN"
    assert updated.enabled_for_llm is True
```

New tests to add (illustrative structure — write exact final code during
implementation):
```python
def test_apply_policy_keeps_hidden_tool_disabled_when_allowed(self) -> None:
    tool = build_runtime_tool(
        name="hidden_tool",
        server_key="s",
        enabled_for_llm=True,
        llm_visibility_base=False,
    )
    reg = _registry_with(tool)
    reg.apply_policy(tier_map={}, allowed_tools=["hidden_tool"])
    assert reg.get("hidden_tool").enabled_for_llm is False

def test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled(
    self, caplog: Any
) -> None:
    tool = build_runtime_tool(
        name="hidden_tool",
        server_key="s",
        enabled_for_llm=True,
        llm_visibility_base=False,
    )
    reg = _registry_with(tool)
    with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
        reg.apply_policy(tier_map={}, allowed_tools=["hidden_tool"])
    assert "hidden_tool" in caplog.text

def test_apply_policy_does_not_log_warning_for_visible_tool(
    self, caplog: Any
) -> None:
    tool = build_runtime_tool(
        name="visible_tool", server_key="s", enabled_for_llm=True
    )
    reg = _registry_with(tool)
    with caplog.at_level(logging.WARNING, logger="shared.runtime_tool_registry"):
        reg.apply_policy(tier_map={}, allowed_tools=["visible_tool"])
    assert "visible_tool" not in caplog.text
```
Confirm the exact logger name matches Row 1's actual `logging.getLogger(__name__)`
value (`shared.runtime_tool_registry`, the module's dotted import path) once Row 1 is
implemented — adjust the `caplog.at_level(..., logger=...)` argument if the actual
module path differs from this assumption.

## Compatibility considerations
Additive only — no existing test is modified, so no existing test's pass/fail outcome
changes. `Any` typing for the `caplog` fixture parameter matches the existing
precedent in `tests/shared/test_tool_executor_routing.py` (confirmed via Read) rather
than importing `pytest.LogCaptureFixture` if this file does not already use that
import style — confirm the file's existing typing convention for fixtures before
adding.

## Security considerations
N/A: test-only change, no production code path affected, no new external
dependency or credential.

## Rollback considerations
Trivially revertable: removing the added test functions (and the `import logging` if
it was newly added) leaves every existing test in this file unaffected.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — full file, confirming
  the 3 new tests pass and no existing test regresses (REQ-001, AC-1, AC-3, AC-5 of
  `plans/20260920-203022_plan.md`).
- `uv run ruff check tests/shared/test_runtime_tool_registry.py` /
  `uv run mypy tests/shared/test_runtime_tool_registry.py`.

## Completion criteria
- `test_apply_policy_keeps_hidden_tool_disabled_when_allowed` passes, proving AC-1.
- `test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled` passes
  once Row 1 is implemented, proving AC-2.
- `test_apply_policy_does_not_log_warning_for_visible_tool` passes, proving the log is
  scoped correctly (not unconditional).
- Every pre-existing test in this file (confirmed at lines 1-263 via the original
  Read) still passes unmodified, proving AC-3.

## Out of scope
- Implementing the `logger.warning(...)` call itself — covered by this Plan's Row 1
  (`scripts/shared/runtime_tool_registry.py`), a separate implementation procedure
  document.
- Updating `docs/00_governance_03_issue-and-uncertainty-management.md` — covered by
  this Plan's Row 3, a separate implementation procedure document.
- Any concurrency/atomicity test — out of scope for REQ-001; see
  `plans/20260920-203342_plan.md` (REQ-002's sibling Plan) for that coverage.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_apply_policy_keeps_hidden_tool_disabled_when_allowed` | Completed | 20260920-211035 | 20260920-211035 |  |
| 2 | Add `test_apply_policy_logs_warning_when_hidden_tool_would_otherwise_be_enabled` and `test_apply_policy_does_not_log_warning_for_visible_tool` | Completed | 20260920-211035 | 20260920-211035 |  |
| 3 | Run `uv run pytest tests/shared/test_runtime_tool_registry.py -v` (after Row 1 lands) and lint/type checks | Completed | 20260920-211035 | 20260920-211035 | 31/31 tests pass in test_runtime_tool_registry.py; 56/56 pass in test_config_reload.py regression check |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (regression coverage for `llm_visibility_base` immutability under config reload)
- **Source issue**: issues/20260920-190713_req001_enforce-immutability-of-llm_visibility_base-during-config-reload.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203022_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-205403
- **Related target files**: tests/shared/test_runtime_tool_registry.py