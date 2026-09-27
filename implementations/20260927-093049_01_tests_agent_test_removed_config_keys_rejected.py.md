## Goal

Remove the obsolete `patch("agent.config_builders.sys.exit")` context manager wrapping each of `tests/agent/test_removed_config_keys_rejected.py`'s 4 tests' `pytest.raises(ValueError, ...)` assertion, since `config_builders.py` has no `sys` import and `build_agent_config` already raises `ValueError` directly (REQ-001).

## Scope

In scope: all 4 test functions' `with patch("agent.config_builders.sys.exit"):` wrapping in this file. Out of scope: `scripts/agent/config_builders.py` (confirmed already correct — no `sys` import, `build_agent_config` raises `ValueError` at line 180) and `scripts/shared/config_validator.py` (confirmed already correct — `_check_removed_semantic_cache_keys` is the source of the removed-key error message).

## Assumptions

- No other test in the file (or elsewhere) relies on `unittest.mock.patch` being imported for an unrelated reason — `patch` is used only in these 4 now-obsolete contexts (per the Plan's confirmed evidence).

## Design decisions

- Remove the `with patch(...):` line and unindent the `pytest.raises(ValueError, ...)` block in each of the 4 tests, rather than replacing it with a no-op patch or leaving it as dead code — the patch target genuinely no longer exists, so keeping any form of it would continue to break.

## Alternatives considered

- Adding a `sys` import to `config_builders.py` to satisfy the obsolete patch: rejected per the Plan — `config_builders.py`'s current rejection mechanism (raising `ValueError` directly) needs no `sys.exit` call; adding an unused import merely to satisfy a stale test would be backwards.

## Implementation

### Target file

`tests/agent/test_removed_config_keys_rejected.py`

### Procedure

1. Re-confirm each of the 4 tests' exact current structure via Read (lines ~50-61) — confirm each still wraps its `pytest.raises(ValueError, ...)` inside `with patch("agent.config_builders.sys.exit"):` (adversarial re-verification).
2. For each of the 4 tests (`test_individual_removed_key_rejected` parametrized x3, `test_all_three_removed_keys_rejected`), remove the `with patch("agent.config_builders.sys.exit"):` line and de-indent the nested `with pytest.raises(ValueError, ...): build_agent_config(merged)` block by one level.
3. Check whether `from unittest.mock import patch` becomes an unused import after all 4 removals (via `rg -n "patch\(" tests/agent/test_removed_config_keys_rejected.py` — if no remaining usage, remove the import too).

### Method

Direct removal of one context-manager layer per test (4 tests), plus a conditional import cleanup — no change to the actual `pytest.raises(ValueError, match=key)` assertions or their bodies.

### Details

- Before (per test):
  ```
  with patch("agent.config_builders.sys.exit"):
      with pytest.raises(ValueError, match=key):
          build_agent_config(merged)
  ```
- After:
  ```
  with pytest.raises(ValueError, match=key):
      build_agent_config(merged)
  ```
  (with the analogous change, minus `match=key`, for `test_all_three_removed_keys_rejected`, which uses a bare `pytest.raises(ValueError)`).

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the removed `with patch(...):` wrapping and the `unittest.mock` import if it was removed.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_removed_config_keys_rejected.py` | Unit | `uv run pytest tests/agent/test_removed_config_keys_rejected.py -q` | All 4 tests pass |

## Completion criteria

- `uv run pytest tests/agent/test_removed_config_keys_rejected.py -q` passes with no failures.
- Each test genuinely verifies `ValueError` is raised for its respective removed key(s), independent of the removed obsolete patch.

## Out of scope

- `scripts/agent/config_builders.py`, `scripts/shared/config_validator.py` (both confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 4 tests is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: remove the obsolete `sys.exit` patch from all 4 tests
- **Source issue**: issues/20260927-075253_agent003_agent.config_builders-missing-sys-attribute-breaks-removed-key-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084744_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093049
- **Related target files**: tests/agent/test_removed_config_keys_rejected.py
