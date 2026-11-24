## Goal

Add one strict numeric accessor to the shared config helpers (REQ-008: reject NaN, infinity, negative, and `bool`-for-number) without changing `get_typed()`, and keep the single definition required by REQ-010.

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 1 is validated on its own)

## Assumptions

- `get_typed()` (`scripts/shared/config_utils.py:55-81`) keeps its current contract for all callers (Plan REQ-008, D-1); only the new accessor is added.
- `0` is accepted when the caller allows it, because the Plan defines `max_file_read_size_kb = 0` as "unlimited" (REQ-006).
- `scripts/mcp_servers/git/git_models.py`'s local `_optional_real()` (line 27) deliberately accepts negative values and is not touched (Reference File).

## Design decisions

- A separate accessor instead of extending `get_typed()`: extending it would change the parsing contract for the 15 production importers recorded in the Plan's Affected areas.
- The accessor returns the value or raises `ValueError`, matching `get_str()` and `get_typed()` — no logging, no return of a sentinel.

## Alternatives considered

- Adding a reject-negative flag to `get_typed()` — rejected by the Plan (D-1) as a contract change for existing callers.
- Keeping a GitHub-local strict parser — rejected by REQ-010 (one definition).

## Implementation
### Target file
`scripts/shared/config_utils.py`

### Procedure
1. Add `get_non_negative_number` (new) after `get_typed()`, with the same argument shape (`d`, `key`, `expected_type`, `type_label`, `default`) plus an explicit range step.
2. Leave `get_str()` and `get_typed()` unchanged, including the existing `bool`-for-numeric rejection.

### Method
- Range checks, in this order: type (same rule as `get_typed()`), then `bool`-for-numeric, then NaN and infinity (`math.isfinite`), then negative. Each rejection raises `ValueError` naming the key and the received value.
- `default` is returned only when the key is absent or its value is `None`, as `get_typed()` does.

### Details
- New import: `import math` (stdlib), consistent with the module's stdlib-only scope.
- Error text uses the same phrasing as `get_typed()` so existing config-error tests keep their message shape; only the range sentence is added.

### Companion test files
- `tests/shared/test_config_utils.py`
  - Procedure: add cases for `get_non_negative_number` (new) — NaN, infinity, negative, `bool`-for-number rejected; non-negative and an allowed `0` accepted; absent key and `None` return the default (REQ-008, REQ-010). Keep the existing `get_typed()` cases green.
  - Validation: `uv run pytest tests/shared/test_config_utils.py` (AC-8).

## Compatibility considerations

- Additive: the 15 production importers listed in the Plan's Affected areas are not affected (verified by `grep -rn --include="*.py" "from shared.config_utils import" scripts/`).
- No shipped config contains a negative numeric value (`grep -rn "= -[0-9]" config/*.toml` returns nothing), so no deployment changes.

## Security considerations

- A non-finite or negative size limit is a security control that can silently become "unlimited" or "deny everything"; rejecting it at parse time keeps the posture honest (REQ-008).

## Rollback considerations

- High: deleting the new accessor reverts to the current state with no config or data change.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/shared/config_utils.py` | Unit | `uv run pytest tests/shared/test_config_utils.py` | Rejections and acceptances as specified; existing `get_typed()` cases stay green |
| Same file | Quality gates | `uv run ruff check scripts/shared/config_utils.py`, `uv run mypy scripts/shared/config_utils.py`, `uv run bandit scripts/shared/config_utils.py` | No finding |

## Completion criteria

- One strict numeric accessor exists in `scripts/shared/`, and `github_models_config.py` uses it instead of defining its own (REQ-010).
- Existing `get_typed()` behavior is unchanged (AC-8).

## Out of Scope

- Changing `get_typed()` or any existing caller.
- Adoption by the GitHub config builder (its own target row) and by sibling items.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261124-142145 | 20261124-142145 | Added get_non_negative_number to scripts/shared/config_utils.py; get_str/get_typed unchanged |
| 2 | Add or update tests per Validation plan (companion `tests/shared/test_config_utils.py`) | Completed | — | 20261124-142145 | tests/shared/test_config_utils.py: 29 cases pass (15 new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-142145 | ruff, mypy, bandit -ll, check_module_size pass |

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
- **Requirement ID**: REQ-008 (strict numeric parsing), REQ-010 (single shared definition)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/shared/config_utils.py`, `tests/shared/test_config_utils.py`