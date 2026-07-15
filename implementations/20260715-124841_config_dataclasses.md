# Implementation Procedure: Normalize configuration schema — remove legacy Memory keys and GitOps security fields

## Goal

Remove deprecated Memory configuration keys (`use_memory_layer`, `memory_jsonl_dir`, `memory_embed_enabled`) and clarify/remove GitOps security fields (`gitops_force_push_blocked`, `gitops_protected_branches`). Add removed-key validation, include original exception messages in `ConfigLoadError`, and add reload preflight validation.

## Scope

### In scope
- `scripts/agent/config_dataclasses.py` — MemoryConfig fields, cross-field validation, AgentConfig docstring

### Out of scope
- `agent/memory/*` modules
- `agent/tool_policy.py`
- `agent/tool_approval.py`
- Documentation files

## Assumptions

1. `MemoryConfig` dataclass must have its fields aligned with `_build_memory_config()` parameters.
2. Cross-field validation methods `_validate_memory_jsonl_dir()` and `_validate_memory_embed_url()` should be removed along with their calls in `_validate_cross_field()`.
3. `AgentConfig` class docstring needs updating to reflect current sub-config count.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

#### Step 1: Remove Memory keys from MemoryConfig dataclass

Remove these fields from `MemoryConfig`:

```python
@dataclass
class MemoryConfig:
    """Persistent semantic memory layer settings."""

    # REMOVED: use_memory_layer (was bool = False)
    # REMOVED: memory_jsonl_dir (was "/opt/llm/memory")
    memory_max_inject_semantic: int = 5
    memory_max_inject_episodic: int = 3
    memory_min_importance: float = 0.3
    # REMOVED: memory_embed_enabled (was bool = False)
    memory_embed_dim: int = 384
    memory_dedup_threshold: float = 0.3
    memory_max_content_chars: int = 500
    memory_embed_timeout_sec: float = 5.0
    memory_retention_days: int = 90
    memory_fts_limit: int = 50
    memory_rrf_k: int = 60
    memory_recency_days: float = 7.0
    memory_local_only: bool = False
```

#### Step 2: Remove cross-field validation for Memory keys

Remove these methods from `AgentConfig`:

```python
# REMOVED: _validate_memory_jsonl_dir()
# REMOVED: _validate_memory_embed_url()

def _validate_cross_field(self) -> None:
    self._validate_semantic_cache_url()
    # REMOVED: self._validate_memory_jsonl_dir()
    # REMOVED: self._validate_memory_embed_url()
```

#### Step 3: Update AgentConfig docstring

Update the `AgentConfig` class docstring to reflect the current number of sub-configs (still 7 since we're removing fields, not entire configs).

### Method

- Use comment markers (`# REMOVED:`) to indicate removed lines for traceability
- Preserve all remaining field defaults exactly as they were
- Keep `_validate_semantic_cache_url()` call intact in `_validate_cross_field()`

### Details

**Type safety considerations:**
- All remaining fields maintain their original types (int, float, bool)
- Default values are preserved exactly as they were

**Import considerations:**
- No new imports required for this file

**Backward compatibility:**
- Removed fields will no longer be available on `MemoryConfig` instances
- Existing code referencing `use_memory_layer`, `memory_jsonl_dir`, or `memory_embed_enabled` will fail at runtime — intentional per acceptance criteria

## Validation plan

1. Verify `MemoryConfig` no longer contains `use_memory_layer`, `memory_jsonl_dir`, or `memory_embed_enabled` fields.
2. Verify `_validate_cross_field()` no longer references removed validation methods.
3. Verify `AgentConfig` docstring reflects correct sub-config count.
4. Run lint: `uv run ruff format scripts/ && uv run ruff check scripts/ --fix && uv run ruff check scripts/`
5. Run type check: `uv run mypy scripts/`
6. Run architecture check: `PYTHONPATH=scripts uv run lint-imports`
7. Run relevant tests: `uv run pytest -x -q`
8. Run pre-commit: `uv run pre-commit run --all-files`
