# `agent.services.config_reload` has no `apply_config_changes` — test_config_reload_security_profile.py fails to collect

## Priority
High

## Summary
`tests/agent/services/test_config_reload_security_profile.py` imports `apply_config_changes`
from `agent.services.config_reload`, but that function does not exist in the current module.
Every test in the file fails at collection time, so security-profile-related config reload
behavior currently has zero test coverage.

## Reason for Change
The module docstring in `scripts/agent/services/config_reload.py` states the current public
entry point is `apply_config_dict()` ("update ctx.cfg fields from raw dict and sync services"),
with `_sync_services()` as a private helper. There is no `apply_config_changes` symbol anywhere
in the file. The test calls `await apply_config_changes(ctx, new_cfg)` in four places — this
looks like a stale reference to a function name from before a rename/refactor, since the
signature shape (`ctx`, `new_cfg`) closely matches what `apply_config_dict()` would need.

## Implementation Intent
Confirm `apply_config_dict()` is the intended current replacement and check its exact signature
(parameter names/types, especially whether it takes a raw dict vs. a config object — the test
currently passes `new_cfg` which may need to become a dict). Update the test's import and call
sites accordingly. Do not add a new `apply_config_changes` alias to production code — prefer
fixing the test to use the current API, per this project's refactoring conventions (no
backwards-compat shims without justification).

## Target Files or Areas
- `tests/agent/services/test_config_reload_security_profile.py`
- `scripts/agent/services/config_reload.py` (reference only, not expected to change)

## Required Changes
- Replace `from agent.services.config_reload import apply_config_changes` with
  `apply_config_dict` (pending signature confirmation).
- Update all four `await apply_config_changes(ctx, new_cfg)` call sites to match
  `apply_config_dict`'s actual parameter shape.
- Verify the security-profile assertions in the file still hold once the call sites compile.

## Acceptance Criteria
- `pytest tests/agent/services/test_config_reload_security_profile.py` collects without error.
- All tests in the file pass.
- No other test file's collection is affected.

## Testing Expectations
Unit tests only (the file itself). Run
`PYTHONPATH=scripts pytest tests/agent/services/test_config_reload_security_profile.py -v`
after the fix.

## Documentation Impact
None expected — this is a test/implementation naming mismatch, not a behavior or public API
change.

## Out of Scope
- Do not modify `scripts/agent/services/config_reload.py`'s public API.
- Do not touch other collection errors (`TurnContext`, `_ACTIVE_ISSUE_ALLOWLIST`) — those are
  filed as separate issues.

## AI Implementation Instruction
Read `scripts/agent/services/config_reload.py` fully, especially `apply_config_dict()`'s
signature and `ConfigReloadOutcome`'s return shape, before editing the test. Fix only the
import and call sites; do not rewrite assertions or add new test cases. Stop and report if
`apply_config_dict()` expects a raw dict rather than a config object, since that may require
restructuring how `new_cfg` is built earlier in the test file.
