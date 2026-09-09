# `test_tool_policy_comprehensive.py`'s `_cfg()` omits `tool_definitions_strict`/`routing_drift_strict`/`allowed_tools`, blocking a full pass even after the unknown-key fix

## Priority
Medium

## Summary
`tests/agent/test_tool_policy_comprehensive.py`'s shared `_cfg()` helper never sets
`tool_definitions_strict`, `routing_drift_strict`, or a non-empty `allowed_tools` in its
`defaults` dict. Each of these independently triggers its own
`ProductionConfigValidator` error and `SystemExit(1)` in `build_agent_config()`. This is
a distinct root cause from `plans/done/20260908-221312_plan.md` (cfgval001)'s
"Unknown config keys" regression — removing that plan's 12 obsolete legacy flat keys
alone will not make this file's tests pass; these 3 additional keys remain unset and
independently block every test that calls `_cfg()`.

## Background
Discovered while validating `plans/done/20260908-221312_plan.md` (cfgval001)'s
Implementation Target Files during a freeze-validation re-entry. Reproducing that
plan's target failure showed this file's traceback carries four distinct error lines
together: `tool_definitions_strict=false — strict mode is required in production`,
`routing_drift_strict=false — strict mode is required in production`,
`allowed_tools=[] (all tools allowed; use allowlist to restrict)`, and `Unknown config
keys: ...`. By contrast, `tests/agent/test_agent_negative_paths.py`'s own `_cfg()`
already sets `allowed_tools=["shell_execute"]`, `tool_definitions_strict=True`, and
`routing_drift_strict=True` — its traceback carries only the `Unknown config keys` line.
This confirms the 3 missing keys are a separate, pre-existing gap specific to
`test_tool_policy_comprehensive.py`.

## Problem
Every test in `tests/agent/test_tool_policy_comprehensive.py` that calls `_cfg()`
(directly or via `**overrides`) constructs an `AgentConfig` that fails
`ProductionConfigValidator.validate()` for 3 reasons unrelated to cfgval001's fix, in
addition to that fix's own 12 obsolete-key reason. Cfgval001's fix alone will leave this
file's tests still raising `SystemExit(1)`.

Reproduction (confirmed by direct execution):
```
uv run pytest tests/agent/test_tool_policy_comprehensive.py::TestEscalateForPath::test_no_matching_path_key_returns_none -q
# → 1 failed; SystemExit: 1; log shows all 4 error lines together (see Background)
```

## Reason for Change
Once cfgval001's fix lands, this file's 29 currently-failing tests would still fail with
a confusing residual `SystemExit(1)` (via the 3 unrelated strict-mode/allowlist checks),
which could be mistaken for an incomplete or broken cfgval001 fix rather than a distinct,
independent gap. Fixing it restores this file's actual test coverage of
`agent/tool_policy.py`'s risk-classification and pre-flight-check behavior.

## Implementation Intent
Add `tool_definitions_strict=True`, `routing_drift_strict=True`, and a non-empty
`allowed_tools` (e.g. a small representative list, matching the pattern already used by
`test_agent_negative_paths.py`'s `_cfg()`) to this file's `_cfg()` `defaults` dict.
Confirm no individual test relies on the current permissive defaults (e.g. a test
asserting behavior specific to `allowed_tools=[]` or `*_strict=False`) before changing
them uniformly.

## Target Files or Areas
- `tests/agent/test_tool_policy_comprehensive.py` (`_cfg()`'s `defaults` dict)

## Required Changes
- Add `tool_definitions_strict=True` to `_cfg()`'s `defaults` dict.
- Add `routing_drift_strict=True` to `_cfg()`'s `defaults` dict.
- Replace `allowed_tools=[]` with a non-empty representative list in `_cfg()`'s
  `defaults` dict.
- Confirm each of this file's individual tests still passes with these 3 values fixed
  (no test currently depends on the old permissive defaults) — adjust a test's own
  `overrides=` call if it specifically needs a different value for one of these 3 keys.

## Constraints
Do not weaken `ProductionConfigValidator`'s strict-mode/allowlist requirements — they
are confirmed intentional (see `plans/done/20260908-221312_plan.md` Background). Do not
combine this fix with cfgval001's own 12-key removal in the same change without also
covering both in the same review — they are independent root causes, but both target
the same file's `_cfg()` helper, so may be applied together if convenient.

## Acceptance Criteria
- [ ] `_cfg()`'s `defaults` dict sets `tool_definitions_strict=True`,
  `routing_drift_strict=True`, and a non-empty `allowed_tools`
- [ ] `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` shows no failure
  citing `tool_definitions_strict`, `routing_drift_strict`, or `allowed_tools=[]`
  (assuming cfgval001's own fix has also landed, this file should reach zero failures)

## Testing Expectations
- `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` — zero failures once
  combined with cfgval001's fix

## Documentation Impact
N/A: test-only fixture fix; no documented behavior change.

## Out of Scope
- `plans/done/20260908-221312_plan.md` (cfgval001)'s own 12 obsolete-flat-key removal —
  tracked separately; this issue covers only the 3 additional strict-mode/allowlist keys.
- Any change to `scripts/shared/production_config_validator.py`'s validation rules.

## Dependencies
Related to, but independent of, `plans/done/20260908-221312_plan.md` (cfgval001) — both
touch the same file's `_cfg()` helper; neither fix requires the other to be correct, but
a full zero-failure pass on this file requires both.

## Unresolved Questions
Whether this gap predates or postdates commit `9a7cdb40e` (cfgval001's regression
commit) — not confirmed; the strict-mode checks it triggers may have been added by a
separate, earlier hardening commit. Not required to resolve before implementing the fix.

## AI Implementation Instruction
Add the 3 missing keys to `_cfg()`'s `defaults` dict only. Verify each of this file's
existing tests still passes with the new defaults before considering this issue
resolved; adjust an individual test's `overrides=` argument if needed rather than
reverting the shared default.
