# Implementation Procedure: test_cmd_config_refactor.py

## Goal

Delete `tests/test_cmd_config_refactor.py` in full — its sole coverage target
(`_ConfigSetMixin._set_temperature`/`_set_max_tokens`/`_cmd_set`) is being removed
from the product.

## Scope

### In scope
- Delete the file `tests/test_cmd_config_refactor.py` (148 lines: `TestSetTemperature`,
  `TestSetMaxTokens`, `TestCmdSet` classes).

### Out of scope
- Any other test file's coverage of `llm_temperature`/`llm_max_tokens` field
  validation (e.g. config dataclass/loader tests) — those fields and their
  `/reload`-driven runtime application are unaffected by this plan; only the `/set`
  CLI override path is removed.

## Assumptions

- No test in this file exercises anything other than `_ConfigSetMixin` — verified
  by reading the full 148-line file: it only imports `agent.commands.cmd_config._ConfigMixin`
  and defines a local `_Config(_ConfigMixin)` test double solely to reach
  `_set_temperature`/`_set_max_tokens`/`_cmd_set`.
- No other test file imports fixtures or helpers defined in this file (private,
  self-contained module — `_Config`, `_make_ctx` are module-local, not exported/imported
  elsewhere; verified via `grep -rn "from tests.test_cmd_config_refactor\|test_cmd_config_refactor import" tests/`).

## Implementation

### Target file

`tests/test_cmd_config_refactor.py`

### Procedure

1. Confirm via `grep -rn "test_cmd_config_refactor" tests/` that no other test module
   imports from this file.
2. Delete the file: `git rm tests/test_cmd_config_refactor.py`.
3. Sequence this deletion in the same change-set as `cmd_config_set.py`'s deletion —
   otherwise this file's `from agent.commands.cmd_config import _ConfigMixin` import
   would still succeed (since `_ConfigMixin` itself survives), but every test method
   calling `cmd._set_temperature(...)`/`cmd._cmd_set(...)` would fail with
   `AttributeError` once `_ConfigSetMixin` is dropped from `_ConfigMixin`'s
   composition — so the whole file must go, not be left half-broken.

### Method

Whole-file deletion via `git rm`. No partial edit — every test in this file targets
functionality that no longer exists.

### Details

- This is a pure test-suite reduction; there is no equivalent behavior to preserve
  or migrate (unlike `test_agent_cmd_db.py`, which has session-scoped tests that
  must survive as `/session` equivalents). `/set` has no replacement command.

## Validation plan

- `uv run pytest tests/test_cmd_config_refactor.py` — file no longer exists, so this
  command itself becomes a no-op / collection error, confirming deletion.
- `uv run pytest tests/` — full suite has 148 fewer test-lines' worth of tests
  (roughly `TestSetTemperature` (6) + `TestSetMaxTokens` (5) + `TestCmdSet` (5) = 16
  test functions removed); no new failures elsewhere.
- `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`
  — confirm the removed file's deleted lines don't count against diff-coverage
  (deletions are not "changed lines added" in the diff-cover sense).
- `grep -rn "cmd_config_refactor" tests/ scripts/` returns no matches after deletion.
