## Goal

Create `scripts/agent/constants.py` as a leaf module containing all six `_DEFAULT_*` constant tables moved from `config_builders.py`, eliminating the two-sources-of-truth problem identified in REQ-001.

## Scope

- Create a new Python module under `scripts/agent/` containing only constant definitions
- No imports from `config_dataclasses.py` or any other agent submodule
- Module docstring documenting its purpose and import relationship with `config_dataclasses.py`

## Assumptions

- The six `_DEFAULT_*` tables in `config_builders.py` have identical values to their counterparts in `config_dataclasses.py` dataclass defaults (confirmed by adversarial verification — exact copies verified).
- `constants.py` is a leaf module — no other module imports from it except `config_dataclasses.py`.
- Moving defaults to `constants.py` will not change runtime behavior because dataclass defaults are evaluated at class definition time, not at import time. The dependency flows one direction (`config_dataclasses.py` → `constants.py`).

## Design decisions

- Constants are exported as top-level module-level names (e.g., `_DEFAULT_PLAN_BLOCKED_TOOLS`) so they can be imported directly without qualification beyond the module name.
- No validation logic in this module — it contains only raw constant data.
- The module uses `list[...]` and `dict[str, ...]` type hints consistent with the existing codebase style.

## Alternatives considered

- Using `typing.Literal` types for the risk rules dictionary keys/values — rejected as over-engineering; the values are validated downstream by `validate_approval_risk_rules`.
- Using `enum.Enum` for the tool lists — rejected; these are plain data tables, not typed enums.

## Implementation
### Target file

`scripts/agent/constants.py` (new file)

### Procedure

1. Create the file with a module docstring explaining its purpose and the import relationship with `config_dataclasses.py`.
2. Copy all six `_DEFAULT_*` constant tables from `config_builders.py` (lines 71-127):
   - `_DEFAULT_PLAN_BLOCKED_TOOLS: list[str]`
   - `_DEFAULT_APPROVAL_RISK_RULES: dict[str, str]`
   - `_DEFAULT_PROTECTED_PATHS: list[str]`
   - `_DEFAULT_SHELL_SAFE_PREFIXES: list[str]`
   - `_DEFAULT_RESOURCE_KEYS: dict[str, list[str]]`
   - `_DEFAULT_DRY_RUN_TOOLS: list[str]`
3. Preserve the original variable names, type annotations, and values exactly.
4. Add a trailing newline at end of file (PEP 8 convention).

### Method

Write the complete file content using Write tool. The file structure:
```python
#!/usr/bin/env python3
"""Module docstring..."""

from typing import Any

_DEFAULT_PLAN_BLOCKED_TOOLS: list[str] = [...]
_DEFAULT_APPROVAL_RISK_RULES: dict[str, str] = {...}
_DEFAULT_PROTECTED_PATHS: list[str] = [...]
_DEFAULT_SHELL_SAFE_PREFIXES: list[str] = [...]
_DEFAULT_RESOURCE_KEYS: dict[str, list[str]] = {...}
_DEFAULT_DRY_RUN_TOOLS: list[str] = [...]
```

### Details

- Line count target: ~30-35 lines (6 constants + docstring + blank lines)
- Each constant retains its original type annotation from `config_builders.py`
- Values must match exactly — no reformatting of nested dicts/lists
- The module has zero imports from `config_dataclasses.py` or any agent submodule
- `from typing import Any` import added for consistency with existing codebase style (used in other modules)

## Compatibility considerations

- `config_dataclasses.py` will import from this module instead of defining inline literals. This creates a new dependency edge: `config_dataclasses.py` → `constants.py`.
- `config_builders.py` will import from this module for the dry-run tools table used by `_validate_dry_run_tools` (per UNK-01, keep `_validate_dry_run_tools` in `config_builders.py` since it references `_DEFAULT_DRY_RUN_TOOLS`).
- No backward-compatibility shim needed — the public API surface (`build_agent_config`, `load_config`, `ConfigLoadError`) is unchanged.

## Security considerations

- No security impact — constants contain configuration defaults, not secrets or credentials.
- The constants themselves are validated downstream by `ProductionConfigValidator` and per-field validators.

## Rollback considerations

- If the refactor introduces regressions, revert the three modified files (`constants.py`, `config_builders.py`, `config_dataclasses.py`) to their pre-refactor state.
- The rollback path is straightforward: delete `constants.py`, restore the six `_DEFAULT_*` tables in `config_builders.py`, and restore inline literals in `config_dataclasses.py`.

## Validation plan

1. Import test: `python -c "from agent.constants import _DEFAULT_PLAN_BLOCKED_TOOLS; assert len(_DEFAULT_PLAN_BLOCKED_TOOLS) == 4"` — verifies the module is importable and values match originals.
2. Cross-reference test: verify that each constant's value matches the corresponding dataclass default in `config_dataclasses.py` (e.g., `ToolConfig.plan_blocked_tools` default_factory lambda).
3. Run unit tests: `uv run pytest tests/agent/test_config_builders.py -q` — verify zero failures after subsequent refactor steps.
4. Run dataclass tests: `uv run pytest tests/agent/test_config_dataclasses.py -q` — verify zero failures after dataclass modifications.

## Completion criteria

- [ ] `scripts/agent/constants.py` exists and is importable via `from agent.constants import _DEFAULT_*`
- [ ] All six `_DEFAULT_*` constants are defined with correct type annotations
- [ ] Constant values match the originals in `config_builders.py` exactly
- [ ] Module docstring documents its purpose and the import relationship with `config_dataclasses.py`
- [ ] No imports from `config_dataclasses.py` or any agent submodule within `constants.py`
- [ ] `python -c "from agent.constants import _DEFAULT_PLAN_BLOCKED_TOOLS; assert len(_DEFAULT_PLAN_BLOCKED_TOOLS) == 4"` succeeds

## Out of scope

- Modifying `config_builders.py` to remove the constants (Phase 3)
- Modifying `config_dataclasses.py` to import from `constants.py` (Phase 2)
- Adding validation logic to `constants.py`
- Changing the constant values themselves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create constants.py with all 6 _DEFAULT_* tables | Completed | 20260920-074845 | 20260920-074845 |  |
| 2 | Add module docstring | Completed | 20260920-074845 | 20260920-074845 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260919-223836_refactor_config_builders_split_and_consolidate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-071804_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-073924
- **Related target files**: scripts/agent/constants.py