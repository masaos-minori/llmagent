# Make retry-suppression and empty-result defaults observable

## Priority
Medium

## Summary
`ToolLoopGuard` retry suppression and empty-result repeat detection are silently
disabled when their config values are `<= 0`. Empty-result detection defaults to
`0` (off) with no operator signal, and neither guard surfaces its enabled/disabled
state. Make the effective state observable (startup log/warn) and document the
semantics so the configuration is unambiguous.

## Background
`scripts/agent/tool_loop_guard.py` gates two per-turn guards on their config:

```python
def record_tool_result(self, tool_name, result):
    if ctx.cfg.tool.tool_empty_result_max_repeats <= 0:
        return   # empty-result detection OFF
    ...

def check_empty_result_repeat(self, message):
    if ctx.cfg.tool.tool_empty_result_max_repeats <= 0:
        return None
    ...

def check_retry_suppression(...):
    if ctx.cfg.tool.tool_error_retry_max <= 0:
        return None   # retry suppression OFF
    ...
```

Defaults (`config_dataclasses.py`): `tool_error_retry_max = 1` (on),
`tool_empty_result_max_repeats = 0` (off).
`docs/23_agent/agent_03_02_...llm-tool-loop.md` Known Limitations lists:
"Retry suppression is only effective if `tool_error_retry_max > 0`. Empty result
repeat detection is only effective if `tool_empty_result_max_repeats > 0`."

## Problem
Both guards are effectively invisible to operators: when disabled there is no
startup indication, so an operator cannot tell whether cycle/retry/empty-result
protection is active. Empty-result detection being off by default with no signal
means a loop of empty results can spin undetected unless explicitly enabled. The
config semantics (`> 0` enables, `<= 0` disables) are also undocumented beyond the
Known Limitations bullet.

## Reason for Change
Ambiguous, silent configuration behavior makes it easy to ship without the
intended protection and hard to diagnose why a guard did not fire. Making the
effective state observable and documenting the semantics reduces misconfiguration
and improves debuggability.

## Implementation Intent
Add a startup-time diagnostic that reports the effective state of these guards
(e.g. a single info/warn log line summarizing retry-suppression and
empty-result-detection on/off based on the resolved config values). Document the
`> 0` / `<= 0` semantics in the config schema/doc. Do NOT change the defaults or
the gating logic (that would alter runtime behavior); the change is observability
plus documentation. Name the boundary: only add reporting + docs, no behavior
change.

## Target Files or Areas
- `scripts/agent/tool_loop_guard.py` (`check_all` / startup wiring, where a startup diagnostic could be emitted)
- `scripts/agent/config_dataclasses.py` (`ToolConfig.tool_error_retry_max`, `tool_empty_result_max_repeats` — docstrings)
- The agent startup/diagnostic reporting path (confirm where a one-time startup log belongs)

## Required Changes
- Emit a startup diagnostic reporting whether retry suppression and
  empty-result detection are enabled given the resolved config.
- Document the `> 0` enables / `<= 0` disables semantics near the config fields.
- Do not change default values or gating thresholds.

## Constraints
- No change to runtime guard behavior or defaults.
- The startup diagnostic must not fail startup when logging is unavailable.
- Keep it a single concise report line to avoid log noise.

## Acceptance Criteria
- On startup, the effective on/off state of both guards is logged.
- Defaults are unchanged (`tool_error_retry_max=1`, `tool_empty_result_max_repeats=0`).
- Config field docs describe the `> 0` / `<= 0` semantics.

## Testing Expectations
- Test that the startup diagnostic reflects the configured state for both on and
  off cases.
- Regression test confirming default values are unchanged.
- Doc-consistency check passes.

## Documentation Impact
Update the Known Limitations bullet in
`docs/23_agent/agent_03_02_...llm-tool-loop.md` to reference the new startup
diagnostic, and document the config semantics in the config field docstring.

## Out of Scope
- Changing the default values or enabling empty-result detection by default.
- Modifying the guard gating logic or cycle-detection algorithm.
- Other guards not mentioned here.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether empty-result detection should be enabled by default (behavior change)
  versus left off with observability — this issue proposes observability only;
  the default-value decision is separate.
- Where exactly the one-time startup diagnostic should be emitted in the startup
  sequence.

## AI Implementation Instruction
Do NOT change defaults or the `<= 0` gating in
`scripts/agent/tool_loop_guard.py`. Only add a concise startup diagnostic that
logs whether retry suppression and empty-result detection are enabled for the
resolved config, and document the `> 0`/`<= 0` semantics on the config fields.
Confirm the correct startup emission point first. Do not enable empty-result
detection by default.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123510
- **Related target files**: `scripts/agent/tool_loop_guard.py`, `scripts/agent/config_dataclasses.py`
