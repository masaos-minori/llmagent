# Implementation Procedure: Add `TestCommandValidatorFilterEnv` unit tests

## Goal

Add unit tests for `CommandValidator.filter_env()` covering: inherited denylisted keys
(`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`) stripped even when absent from `cfg.env`
and with `cfg.env=None` (`T4`); preservation of benign inherited vars (`T5`); and
config-provided non-protected var merge plus protected-key override logging (`T6`).
Implements `REQ-007`.

Part 1 interpreter tests (`test_python3_prefix_allows_python3x` rewritten,
`test_python3_evil_rejected`, `test_interpreter_variants_accepted`) are **already present
and passing** — see the sibling document
`implementations/done/20261004-110940_02_tests_agent_test_http_lifecycle_command_validator.py.md`
(committed as `2637dbe5f`). This document covers **only** the not-yet-implemented remainder
(`TestCommandValidatorFilterEnv`). Do not re-add the Part 1 tests.

## Scope

Modify `tests/agent/test_http_lifecycle_command_validator.py` only: add a
`TestCommandValidatorFilterEnv` class after `TestCommandValidatorValidate`. No other file is
a modification target.

## Assumptions

- `pytest`, `unittest.mock.patch`, and `caplog` are available; `patch.dict(os.environ, ...)`
  controls the seeded parent environment deterministically.
- `filter_env()` seeds from `os.environ`, so tests must patch `os.environ` rather than pass
  it as an argument.
- The module logger is `logging.getLogger(__name__)`
  (`agent.http_lifecycle_command_validator`); `caplog` can capture its warnings.

## Design decisions

- Drive all cases through `patch.dict(os.environ, {...}, clear=False)` so the seeded
  inherited keys are known and deterministic regardless of the host environment.
- Use synthetic sentinel keys (e.g. `BENIGN_INHERITED`) for "benign preserved" assertions
  instead of depending on real host vars.
- Assert the exact protected-override warning substring emitted by
  `filter_env()`: `"Blocked protected env var override: <KEY>=<VALUE>"`.
- Keep positive assertions simple (`key in result` / equality).

## Alternatives considered

- Relying on the real host environment: rejected — non-deterministic across hosts;
  `patch.dict` makes the seeded keys explicit.
- One mega-test combining all cases: rejected — `T4` (strip), `T5` (preserve), and
  `T6` (merge + log) are distinct acceptance conditions and should be independently
  assertable and readable.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_command_validator.py`

### Procedure

1. Add `import logging` to the stdlib import group (top of file).
2. Append a new test class after `TestCommandValidatorValidate` (before end of file):
   ```python
   class TestCommandValidatorFilterEnv:
       """Tests for CommandValidator.filter_env()."""

       def test_inherited_denylist_keys_stripped_even_when_cfg_env_none(self):
           with patch.dict(
               os.environ,
               {"BENIGN_INHERITED": "kept", "LD_PRELOAD": "/x",
                "LD_LIBRARY_PATH": "/y", "PYTHONPATH": "/z"},
               clear=False,
           ):
               result = CommandValidator().filter_env(None)
           assert result is not None
           assert result.get("BENIGN_INHERITED") == "kept"
           assert "LD_PRELOAD" not in result
           assert "LD_LIBRARY_PATH" not in result
           assert "PYTHONPATH" not in result

       def test_benign_inherited_vars_preserved(self):
           with patch.dict(
               os.environ,
               {"BENIGN_A": "a", "BENIGN_B": "b"},
               clear=False,
           ):
               result = CommandValidator().filter_env(None)
           assert result.get("BENIGN_A") == "a"
           assert result.get("BENIGN_B") == "b"

       def test_config_non_protected_var_merges_and_protected_override_logged(self):
           with patch.dict(os.environ, {"BENIGN_INHERITED": "kept"}, clear=False):
               with caplog.at_level(logging.WARNING):
                   result = CommandValidator().filter_env(
                       {"MY_NEW_VAR": "value", "HOME": "hacked"}
                   )
           assert result.get("MY_NEW_VAR") == "value"
           assert "Blocked protected env var override: HOME=hacked" in caplog.text
   ```
3. Confirm no existing test is altered (the Part 1 tests above stay untouched).

### Method

- Locate the end of `TestCommandValidatorValidate` with
  `rg -n 'class TestCommandValidatorValidate' tests/agent/test_http_lifecycle_command_validator.py`
  (currently line 87); append the new class after its last method
  (`test_validate_realpath_resolves_symlinks`, ~line 244).
- Reuse the `patch.object`/`patch.dict` mocking style already in the file.

### Details

- `patch.dict(os.environ, ..., clear=False)` merges into the real environment rather than
  clearing it, so essential vars (e.g. `PATH`) are not removed.
- `caplog.at_level(logging.WARNING)` captures the module-logger warning; the protected
  key `HOME` is in `_protected_env_vars` (not in the runtime denylist), so its config
  override is logged and blocked, while `MY_NEW_VAR` (non-protected) merges in.
- Note: `LD_LIBRARY_PATH`/`PYTHONPATH` are both denylisted *and* protected — inherited
  instances are stripped by the denylist (`test_inherited_denylist_keys...`), while a
  config-supplied override would additionally be logged/blocked by the protected path.

## Compatibility considerations

- Existing tests unchanged; only a new class is appended. No changes to test fixtures or
  shared helpers.
- `import logging` addition is additive and harmless.

## Security considerations

- Locks the runtime defense-in-depth property: loader/interpreter env vars inherited from
  the parent process are stripped before config overrides apply, closing the
  shared-library/module-injection surface described in the source issue.

## Rollback considerations

- Remove the `TestCommandValidatorFilterEnv` class and the `import logging` addition to
  restore pre-change test state.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_http_lifecycle_command_validator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` | New `TestCommandValidatorFilterEnv` cases pass; regression suite passes (Part 1 tests still pass) |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- Inherited `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` removed even when `cfg.env=None`
  and absent from config (`T4` / `AC4`). ↔ `REQ-005`, `REQ-006`
- Benign inherited vars (`PATH`, `HOME`, `USER`, sentinels) remain after `filter_env()`
  (`T5` / `AC4`). ↔ `REQ-005`
- Config-provided non-protected vars merge in; a protected-key override is logged
  (`T6` / `AC4`). ↔ `REQ-005`, `REQ-007`
- Full suite passes with no new failures.

## Out of scope

- Changes to `scripts/agent/http_lifecycle_command_validator.py` (covered by the sibling
  implementation procedure for this Plan).
- Adding Part 1 interpreter tests (already present; sibling document).
- Changes to other test files or shared test infrastructure.
- Documentation updates (`docs/*.md`): N/A.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-111005 | 20261005-111005 | |
| 2 | Add or update tests per Validation plan | Completed | 20261005-111005 | 20261005-111005 | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-111005 | 20261005-111005 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-111005 | 20261005-111005 | N/A: no docs/*.md mapping |

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
- **Requirement ID**: `REQ-007` (unit tests for `filter_env()` denylist stripping/preserve/merge)
- **Source issue**: issues/20261004-065422_mcp002_filter_env-inherits-dangerous-loader-env-vars-from-parent-process-into-mcp-subprocess.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-123553_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-111005
- **Related target files**: tests/agent/test_http_lifecycle_command_validator.py
