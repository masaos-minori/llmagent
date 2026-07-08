# Implementation: M-1 — Remove forbidden config keys from test_tool_policy_comprehensive.py's _cfg()

## Goal

Remove `use_tool_summarize`/`tool_summarize_threshold` from `_cfg()`'s `defaults` dict. Mandatory
fix: `_cfg()` calls `build_agent_config(defaults)`, and once these keys are added to
`_FORBIDDEN_KEYS` (per `config_builders.py`'s M-1 doc), every test in this file would fail with
`ConfigLoadError`.

## Scope

**Target**: `tests/test_tool_policy_comprehensive.py` — the `_cfg()` helper's `defaults` dict
only (lines ~41-42).

**Depends on / must land together with**: `implementations/20260708-171134_config_builders.py.md`.

## Assumptions

1. `_cfg()`'s `defaults` dict is the shared fixture builder for every test in this file.

## Implementation

### Target file

`tests/test_tool_policy_comprehensive.py`

### Procedure

#### Step 1: Confirm the current lines

```bash
grep -n "use_tool_summarize\|tool_summarize_threshold" tests/test_tool_policy_comprehensive.py
```

Expected: two matches inside `_cfg()`'s `defaults` dict.

#### Step 2: Remove both keys

Remove the two lines:

```python
        "use_tool_summarize": False,
        "tool_summarize_threshold": 3000,
```

from the `defaults` dict, leaving adjacent keys unaffected.

### Method

- Two-key removal from a shared fixture dict.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_tool_policy_comprehensive.py` | 0 errors |
| Grep (keys removed) | `grep -n "use_tool_summarize\|tool_summarize_threshold" tests/test_tool_policy_comprehensive.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_tool_policy_comprehensive.py -v` | all tests pass once every M-1 companion doc lands together |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- HIGH PRIORITY: without this fix, every test in this file breaks once `_FORBIDDEN_KEYS` lands.
