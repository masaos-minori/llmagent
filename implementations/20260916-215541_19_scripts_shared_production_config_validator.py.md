## Goal

Import the canonical `ConfigValidationResult` from `config_validator.py` instead of defining its own; replace `_get_valid_production_keys()`'s mixed introspection-plus-manual-list body with one explicit canonical schema source.

## Scope

- Modify `scripts/shared/production_config_validator.py`: import canonical `ConfigValidationResult` and consolidate valid-key derivation.

## Assumptions

- The canonical `ConfigValidationResult` will be hosted in `scripts/shared/config_validator.py` (covered in previous row).
- `validate_unknown_tool_safety_tiers()` relies on `warnings`'s default factory (`ConfigValidationResult(errors=errors)` without `warnings=`).
- The valid-key set must remain identical to today's (T-7).

## Design decisions

- Import `ConfigValidationResult` from `shared.config_validator` instead of defining a duplicate.
- Create a named constant `_CANONICAL_SUB_CONFIG_CLASSES` in `scripts/agent/config_dataclasses.py` for the 9 sub-config classes.
- Consolidate manual additions into one named constant `_MANUAL_ADDITIONAL_KEYS` in `production_config_validator.py`.
- Combine the two sources in one place within `_get_valid_production_keys()`.

## Alternatives considered

- Keeping the duplicate definition and having `production_config_validator.py` inherit from the canonical class — rejected: over-engineers a simple unification.
- Moving the canonical definition to `config_errors.py` — rejected: `config_validator.py` is already the more natural home for validation-related types.

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

1. Replace the local `ConfigValidationResult` definition with an import from `config_validator.py`.
2. Replace `_get_valid_production_keys()`'s body with one that imports the canonical schema root from `config_dataclasses.py` and consolidates manual additions.

### Method

- **Step 1**: Replace the local `ConfigValidationResult` definition:

```python
# Before:
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

# After:
from shared.config_validator import ConfigValidationResult  # REQ-004
```

- **Step 2**: Replace `_get_valid_production_keys()`:

```python
# Before (lines ~50-80):
def _get_valid_production_keys(self) -> set[str]:
    """Derive the set of valid top-level keys from AgentConfig sub-dataclasses."""
    valid_keys: set[str] = set()
    for cls in [LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig,
                ApprovalConfig, ObservabilityConfig, DiagnosticsConfig, MessageRoleConfig]:
        for f in cls.__dataclass_fields__:
            valid_keys.add(f)
    # Manual additions
    valid_keys.add("agent_memory_max_startup_snippets")
    valid_keys.add("system_prompt_tool")
    valid_keys.add("security_profile")
    valid_keys.add("diagnostics")
    # DB/RAG subsystem path keys
    valid_keys.update(["embed_url", "chunk_size", ...])
    return valid_keys

# After:
# REQ-006: canonical schema root imported from config_dataclasses.py
from agent.config_dataclasses import _CANONICAL_SUB_CONFIG_CLASSES

# REQ-006: consolidated manual additions constant
_MANUAL_ADDITIONAL_KEYS: frozenset[str] = frozenset((
    "agent_memory_max_startup_snippets",
    "system_prompt_tool",
    "security_profile",
    "diagnostics",
    "embed_url",
    "chunk_size",
    # ... all 11 DB/RAG subsystem path keys
))

def _get_valid_production_keys(self) -> set[str]:
    """Derive the set of valid top-level keys from the canonical schema source.

    The valid-key set is derived from two sources:
    1. Field names of the canonical sub-config dataclasses (_CANONICAL_SUB_CONFIG_CLASSES).
    2. A named constant of manually-added keys (_MANUAL_ADDITIONAL_KEYS).

    This replaces the previous approach of mixing dataclass introspection with
    three separate inline manual-addition blocks.
    """
    valid_keys: set[str] = set()
    for cls in _CANONICAL_SUB_CONFIG_CLASSES:
        for f in cls.__dataclass_fields__:
            valid_keys.add(f)
    valid_keys.update(_MANUAL_ADDITIONAL_KEYS)
    return valid_keys
```

### Details

**Step 1 — Replace ConfigValidationResult:**

Replace lines ~5-15 in `scripts/shared/production_config_validator.py`:

```python
from shared.config_validator import ConfigValidationResult  # REQ-004
```

**Step 2 — Replace _get_valid_production_keys():**

After the imports section, add:

```python
# REQ-006: canonical schema root imported from config_dataclasses.py
from agent.config_dataclasses import _CANONICAL_SUB_CONFIG_CLASSES

# REQ-006: consolidated manual additions constant
_MANUAL_ADDITIONAL_KEYS: frozenset[str] = frozenset((
    "agent_memory_max_startup_snippets",
    "system_prompt_tool",
    "security_profile",
    "diagnostics",
    "embed_url",
    "chunk_size",
    # ... all 11 DB/RAG subsystem path keys
))
```

Replace the `_get_valid_production_keys()` method as shown above.

## Compatibility considerations

- Existing code using `ConfigValidationResult(errors=errors)` continues to work (default factory handles it).
- The valid-key set remains unchanged (T-7).
- No call site changes beyond the import.

## Security considerations

- No security impact. This is a structural consistency improvement.

## Rollback considerations

- Reverting restores the duplicate definition but does not break existing behavior.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_production_config_validator.py -v`
- Verify `ConfigValidationResult` identity test passes.
- Verify valid-key-set-unchanged test passes.
- Static analysis: `uv run ruff check scripts/shared/production_config_validator.py`, `uv run mypy scripts/shared/production_config_validator.py`.

## Completion criteria

- `ConfigValidationResult` imported from `config_validator.py`.
- Valid-key derivation uses canonical schema source + consolidated manual additions.
- All existing tests pass after updates.
- No new lint/type errors introduced.

## Out of scope

- Modifying `config_dataclasses.py` source code — covered in subsequent row (REQ-006).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import canonical ConfigValidationResult | Pending | — | — | |
| 2 | Replace _get_valid_production_keys() with canonical schema source | Pending | — | — | |
| 3 | Add valid-key-set-unchanged regression test | Pending | — | — | See next row |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-006
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/production_config_validator.py
