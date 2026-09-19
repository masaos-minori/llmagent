## Goal

Update `scripts/agent/config_dataclasses.py` to import default values from `constants.py` instead of defining inline literals, eliminating the two-sources-of-truth problem identified in REQ-001.

## Scope

- Modify only `scripts/agent/config_dataclasses.py` — no other file changes in this document
- Update six dataclass field defaults that currently use inline lambda-based literals
- Add import of `_DEFAULT_*` constants from `constants.py`
- Replace inline literal defaults with references to the imported constants

## Assumptions

- The six `_DEFAULT_*` tables in `config_builders.py` have identical values to their counterparts in `config_dataclasses.py` dataclass defaults (confirmed by adversarial verification — exact copies verified).
- `constants.py` is a leaf module — no other module imports from it except `config_dataclasses.py`.
- Moving defaults to `constants.py` will not change runtime behavior because dataclass defaults are evaluated at class definition time, not at import time. The dependency flows one direction (`config_dataclasses.py` → `constants.py`).
- Lambda-based defaults reference initialized state in `constants.py` — no circular import risk.

## Design decisions

- Use `default_factory=lambda: list(_DEFAULT_X)` pattern for list defaults to ensure each instance gets its own copy (mutable default argument avoidance).
- Use `default_factory=lambda: dict(_DEFAULT_X)` pattern for dict defaults similarly.
- This preserves the existing mutable-default-behavior: each instance gets an independent copy of the default value.

## Alternatives considered

- Using `field(default=_DEFAULT_X)` directly — rejected because mutable defaults would be shared across instances.
- Using `__post_init__` to set defaults — rejected because it adds complexity and delays default evaluation until after initialization.

## Implementation
### Target file

`scripts/agent/config_dataclasses.py` (modify)

### Procedure

#### Phase A: Add import

1. Add import statement near the top of the file, alongside existing imports:
   ```python
   from agent.constants import (
       _DEFAULT_APPROVAL_RISK_RULES,
       _DEFAULT_DRY_RUN_TOOLS,
       _DEFAULT_PLAN_BLOCKED_TOOLS,
       _DEFAULT_PROTECTED_PATHS,
       _DEFAULT_RESOURCE_KEYS,
       _DEFAULT_SHELL_SAFE_PREFIXES,
   )
   ```

#### Phase B: Update ToolConfig.plan_blocked_tools default

1. Find the current definition (lines 196-203):
   ```python
   plan_blocked_tools: list[str] = field(
       default_factory=lambda: [
           "write_file",
           "create_directory",
           "delete_file",
           "delete_directory",
       ],
   )
   ```

2. Replace with:
   ```python
   plan_blocked_tools: list[str] = field(
       default_factory=lambda: list(_DEFAULT_PLAN_BLOCKED_TOOLS),
   )
   ```

#### Phase C: Update ApprovalConfig defaults

1. **approval_risk_rules** (lines 293-312):
   - Current: `default_factory=lambda: {...}` with inline dict literal
   - Replace with: `default_factory=lambda: dict(_DEFAULT_APPROVAL_RISK_RULES)`

2. **approval_protected_paths** (lines 314-323):
   - Current: `default_factory=lambda: [...]` with inline list literal
   - Replace with: `default_factory=lambda: list(_DEFAULT_PROTECTED_PATHS)`

3. **approval_shell_safe_prefixes** (lines 330-344):
   - Current: `default_factory=lambda: [...]` with inline list literal
   - Replace with: `default_factory=lambda: list(_DEFAULT_SHELL_SAFE_PREFIXES)`

4. **approval_resource_keys** (lines 346-357):
   - Current: `default_factory=lambda: {...}` with inline dict literal
   - Replace with: `default_factory=lambda: dict(_DEFAULT_RESOURCE_KEYS)`

5. **approval_dry_run_tools** (lines 359-368):
   - Current: `default_factory=lambda: [...]` with inline list literal
   - Replace with: `default_factory=lambda: list(_DEFAULT_DRY_RUN_TOOLS)`

### Method

Use Edit tool to apply changes incrementally:
1. First edit: add import statement
2. Second edit: replace `ToolConfig.plan_blocked_tools` default
3. Third edit: replace all five `ApprovalConfig` defaults

## Details

- Line count target after refactor: ~480 lines (down from 486 — removing inline literals saves ~6 lines)
- AC-2: `scripts/agent/constants.py` exists and contains all `_DEFAULT_*` tables; `config_dataclasses.py` imports from it.
- Each `default_factory` lambda ensures independent copies per instance (mutable default avoidance).
- No validator functions need updating — they validate values, not sources.

## Compatibility considerations

- Dataclass consumers across `agent/` and `shared/` continue to work unchanged — the public API surface of these dataclasses is identical.
- Import compatibility verified against Reference Files:
  - `scripts/agent/diagnostic_store.py` — imports `DiagnosticsConfig`
  - `scripts/agent/repository_gateway.py` — imports `AgentConfig`
  - `scripts/agent/tool_policy.py` — imports `AgentConfig`
  - `scripts/agent/services/config_validators.py` — imports dataclass types
  - `scripts/shared/production_config_validator.py` — imports dataclass types
  - `scripts/shared/runtime_tool_registry.py` — references `ToolConfig.allowed_tools`

## Security considerations

- No security impact — this is a structural refactor only.
- The lambda-based `default_factory` pattern ensures mutable defaults are not shared across instances, preventing silent data corruption.

## Rollback considerations

- If the refactor introduces regressions, revert the edits to restore inline literals.
- The rollback path is straightforward: undo each Edit operation in reverse order.

## Validation plan

1. Unit test: `uv run pytest tests/agent/test_config_dataclasses.py -q` — verify zero failures.
2. Cross-reference test: verify that each dataclass default's value matches the corresponding constant in `constants.py` (e.g., `ToolConfig().plan_blocked_tools == _DEFAULT_PLAN_BLOCKED_TOOLS`).
3. Full suite regression: `uv run pytest tests/ -q` — verify zero failures.
4. Verify that mutable defaults work correctly: instantiate two `ToolConfig` objects and modify one's `plan_blocked_tools` — the other should retain the original default.

## Completion criteria

- [ ] Import of `_DEFAULT_*` constants from `constants.py` added
- [ ] `ToolConfig.plan_blocked_tools` default uses `list(_DEFAULT_PLAN_BLOCKED_TOOLS)`
- [ ] All five `ApprovalConfig` defaults use their corresponding `_DEFAULT_*` constant
- [ ] Each `default_factory` lambda returns an independent copy (not shared mutable object)
- [ ] All existing tests pass without modification
- [ ] No new import cycles introduced

## Out of scope

- Modifying `constants.py` (covered by seq=01 document)
- Modifying `config_builders.py` to remove constants (covered by seq=02 document)
- Adding new default values or changing existing ones
- Modifying validators or cross-field validation logic

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add import of _DEFAULT_* constants from constants.py | Pending | — | — | |
| 2 | Update ToolConfig.plan_blocked_tools default | Pending | — | — | |
| 3 | Update ApprovalConfig.approval_risk_rules default | Pending | — | — | |
| 4 | Update ApprovalConfig.approval_protected_paths default | Pending | — | — | |
| 5 | Update ApprovalConfig.approval_shell_safe_prefixes default | Pending | — | — | |
| 6 | Update ApprovalConfig.approval_resource_keys default | Pending | — | — | |
| 7 | Update ApprovalConfig.approval_dry_run_tools default | Pending | — | — | |

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
- **Related target files**: scripts/agent/config_dataclasses.py
