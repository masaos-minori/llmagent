## Goal

Become the canonical host of `ConfigValidationResult` (add `field(default_factory=list)` to both fields to remain compatible with `production_config_validator.py`'s existing single-argument construction); remove `_extract_rag_section()`'s nested `{"rag": {...}}` branch and correct its docstring.

## Scope

- Modify `scripts/shared/config_validator.py`: unify `ConfigValidationResult` and fix `_extract_rag_section()`.

## Assumptions

- The canonical `ConfigValidationResult` will remain in `scripts/shared/config_validator.py`.
- Both `errors` and `warnings` fields need `field(default_factory=list)` defaults.
- The `ok` property must be preserved.
- `_extract_rag_section()` always treats input as flat (no nested `{"rag": {...}}` branch).

## Design decisions

- Add `field(default_factory=list)` to both `errors` and `warnings` fields.
- Keep the `ok` property unchanged.
- Remove the nested `cfg["rag"] if "rag" in cfg else cfg` branch from `_extract_rag_section()`.
- Correct the docstring to describe only the flat shape.

## Alternatives considered

- Moving `ConfigValidationResult` to `production_config_validator.py` — rejected: `config_validator.py` is already the more natural home for RAG-related validation results.
- Keeping both definitions and having one import from the other — rejected: defeats the purpose of unification.

## Implementation

### Target file

`scripts/shared/config_validator.py`

### Procedure

1. Update `ConfigValidationResult` dataclass with default factories on both fields.
2. Remove the nested `{"rag": {...}}` branch from `_extract_rag_section()`.
3. Correct `_extract_rag_section()`'s docstring.

### Method

- **Step 1**: Update `ConfigValidationResult`:

```python
# Before:
@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool: ...

# After:
@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0
```

- **Step 2**: Remove the nested branch from `_extract_rag_section()`:

```python
# Before:
def _extract_rag_section(self, cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract the RAG configuration section from the given configuration dictionary.

    Normalizes both nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes.
    """
    rag_section = cfg.get("rag", {}) if "rag" in cfg else cfg
    # ... rest of method
    return rag_section

# After:
def _extract_rag_section(self, cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract the RAG configuration section from the given configuration dictionary.

    The input is expected to be a flat dictionary with top-level RAG keys
    (e.g., embed_url, chunk_size, etc.). No nested {"rag": {...}} shape
    is supported or tested in production.
    """
    # Input is always flat — all three production call sites pass flat dicts
    return cfg
```

### Details

**Step 1 — Update ConfigValidationResult:**

Replace the `ConfigValidationResult` dataclass definition in `scripts/shared/config_validator.py`:

```python
@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0
```

**Step 2 — Fix _extract_rag_section():**

Replace lines ~100-110 in `scripts/shared/config_validator.py`:

```python
def _extract_rag_section(self, cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract the RAG configuration section from the given configuration dictionary.

    The input is expected to be a flat dictionary with top-level RAG keys
    (e.g., embed_url, chunk_size, etc.). No nested {"rag": {...}} shape
    is supported or tested in production.
    """
    # Input is always flat — all three production call sites pass flat dicts
    return cfg
```

## Compatibility considerations

- Existing code constructing `ConfigValidationResult(errors=errors)` without `warnings=` continues to work (default factory handles it).
- The `ok` property remains available.
- `_extract_rag_section()` now always returns the input unchanged — callers relying on the nested branch behavior must be updated.

## Security considerations

- No security impact. This is a behavioral consistency improvement.

## Rollback considerations

- Reverting removes the default factories but does not break existing behavior.

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_config_validator.py -v`
- Verify `ConfigValidationResult` identity test passes.
- Verify flat-shape fixtures pass after rewrite.
- Static analysis: `uv run ruff check scripts/shared/config_validator.py`, `uv run mypy scripts/shared/config_validator.py`.

## Completion criteria

- `ConfigValidationResult` has `field(default_factory=list)` on both fields.
- `_extract_rag_section()` always treats input as flat.
- Docstring corrected to describe only the flat shape.
- All existing tests pass after updates.
- No new lint/type errors introduced.

## Out of scope

- Modifying `production_config_validator.py` source code — covered in subsequent row (REQ-004).
- Modifying `AgentContext.__init__` — covered in subsequent row (REQ-001).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update ConfigValidationResult with default factories | Completed | 20260917-192945 | 20260917-192945 |  |
| 2 | Remove nested branch from _extract_rag_section(); correct docstring | Completed | 20260917-192945 | 20260917-192945 |  |
| 3 | Rewrite TestRagConfigValidator fixtures to flat shape | Completed | 20260917-192945 | 20260917-192945 | See next row |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-192945 | 20260917-192945 |  |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-192945 | 20260917-192945 |  |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/shared/config_validator.py