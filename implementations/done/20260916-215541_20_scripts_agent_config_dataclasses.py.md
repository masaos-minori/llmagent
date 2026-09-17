## Goal

Expose one canonical, named collection of the 9 sub-config dataclasses (`LLMConfig`, `RAGConfig`, `ToolConfig`, `MemoryConfig`, `MCPConfig`, `ApprovalConfig`, `ObservabilityConfig`, `DiagnosticsConfig`, `MessageRoleConfig`) for `production_config_validator.py` to import and iterate over, replacing that file's own hardcoded inline list.

## Scope

- Modify `scripts/agent/config_dataclasses.py`: add a canonical tuple/list of the 9 sub-config classes.

## Assumptions

- The 9 sub-config classes are already defined or imported in `config_dataclasses.py`.
- The canonical collection should be a module-level constant named `_CANONICAL_SUB_CONFIG_CLASSES`.

## Design decisions

- Use a `frozenset` of class references for immutability and hashability.
- Name the constant `_CANONICAL_SUB_CONFIG_CLASSES` (prefixed with underscore to indicate internal use).

## Alternatives considered

- Using a tuple instead of frozenset — rejected: frozenset provides immutability and hashability guarantees.
- Creating a registry object — rejected: adds unnecessary complexity; a simple frozenset suffices.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Add `_CANONICAL_SUB_CONFIG_CLASSES` constant after the sub-config class definitions.

### Method

- **Step 1**: Add the canonical constant:

```python
# After the sub-config class definitions (e.g., after MessageRoleConfig):
_CANONICAL_SUB_CONFIG_CLASSES: frozenset[type[object]] = frozenset((
    LLMConfig,
    RAGConfig,
    ToolConfig,
    MemoryConfig,
    MCPConfig,
    ApprovalConfig,
    ObservabilityConfig,
    DiagnosticsConfig,
    MessageRoleConfig,
))
```

### Details

**Step 1 — Add the constant:**

After line ~50 (after the last sub-config class definition) in `scripts/agent/config_dataclasses.py`:

```python
_CANONICAL_SUB_CONFIG_CLASSES: frozenset[type[object]] = frozenset((
    LLMConfig,
    RAGConfig,
    ToolConfig,
    MemoryConfig,
    MCPConfig,
    ApprovalConfig,
    ObservabilityConfig,
    DiagnosticsConfig,
    MessageRoleConfig,
))
```

This constant replaces the hardcoded inline list in `production_config_validator.py`'s `_get_valid_production_keys()` method.

## Compatibility considerations

- No behavioral change. This is a structural consistency improvement.
- Existing code importing individual classes from this module is unaffected.

## Security considerations

- No security impact. This is a structural consistency improvement.

## Rollback considerations

- Reverting removes the constant but does not affect other functionality.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_production_config_validator.py -v`
- Verify valid-key-set-unchanged test passes.
- Static analysis: `uv run ruff check scripts/agent/config_dataclasses.py`, `uv run mypy scripts/agent/config_dataclasses.py`.

## Completion criteria

- `_CANONICAL_SUB_CONFIG_CLASSES` constant added.
- Contains all 9 sub-config classes.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying any sub-config class definition — out of scope.
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add _CANONICAL_SUB_CONFIG_CLASSES constant | Completed | 20260917-194816 | 20260917-194816 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-194816 | 20260917-194816 |  |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-194816 | 20260917-194816 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/agent/config_dataclasses.py