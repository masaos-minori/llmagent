# Implementation Procedure: Add MemoryConfig validators to config_validators.py (Item 4)

## Goal
Move the four build-path-only `MemoryConfig` validations into new `config_validators.py` functions called from `MemoryConfig.__post_init__`.

## Scope
- Target files: 
  - `scripts/agent/services/config_validators.py` - add 4 new validator functions
  - `scripts/agent/config_dataclasses.py` - import and call validators in `MemoryConfig.__post_init__`
  - `scripts/agent/config_builders.py` - remove inline `ConfigReloadValidationError` raises in `_build_memory_config`

## Assumptions
- The four validations are: `memory_max_inject_semantic >= 0`, `memory_max_inject_episodic >= 0`, `memory_embed_timeout_sec > 0`, `memory_retention_days >= 1`
- Error messages must match exactly what's currently in `config_builders.py` (lines 336-361)
- Reload path must still raise `ConfigReloadValidationError` - wrap `MemoryConfig(...)` construction in try/except in `_build_memory_config` to convert `ValueError` -> `ConfigReloadValidationError`

## Design decisions
- Follow existing `validate_memory_fts_limit`/`validate_memory_rrf_k`/`validate_memory_recency_days` pattern
- Add validators: `validate_memory_max_inject_semantic`, `validate_memory_max_inject_episodic`, `validate_memory_embed_timeout_sec`, `validate_memory_retention_days`
- Keep build-path error handling by catching `ValueError` from `MemoryConfig(...)` and re-raising as `ConfigReloadValidationError`

## Implementation
### Target files
1. `scripts/agent/services/config_validators.py`
2. `scripts/agent/config_dataclasses.py`
3. `scripts/agent/config_builders.py`

### Procedure
1. Add 4 new validator functions to `config_validators.py`
2. Import and call them from `MemoryConfig.__post_init__` in `config_dataclasses.py`
3. Remove inline validation blocks from `_build_memory_config` in `config_builders.py`, add try/except wrapper

### Method
Direct code modifications using exact line matching

### Details

**1. Add to `scripts/agent/services/config_validators.py` (after line 180, before `validate_approval_risk_rules`):**
```python
def validate_memory_max_inject_semantic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_semantic is non-negative."""
    if cfg.memory_max_inject_semantic < 0:
        raise ValueError(
            f"memory_max_inject_semantic must be >= 0, got {cfg.memory_max_inject_semantic}"
        )


def validate_memory_max_inject_episodic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_episodic is non-negative."""
    if cfg.memory_max_inject_episodic < 0:
        raise ValueError(
            f"memory_max_inject_episodic must be >= 0, got {cfg.memory_max_inject_episodic}"
        )


def validate_memory_embed_timeout_sec(cfg: MemoryConfig) -> None:
    """Validate that memory_embed_timeout_sec is positive."""
    if cfg.memory_embed_timeout_sec <= 0:
        raise ValueError(
            f"memory_embed_timeout_sec must be > 0, got {cfg.memory_embed_timeout_sec}"
        )


def validate_memory_retention_days(cfg: MemoryConfig) -> None:
    """Validate that memory_retention_days is at least 1."""
    if cfg.memory_retention_days < 1:
        raise ValueError(
            f"memory_retention_days must be >= 1, got {cfg.memory_retention_days}"
        )
```

**2. Update `scripts/agent/config_dataclasses.py`:**
- Add imports (after line 64, before `validate_progress_stagnation_window`):
```python
from agent.services.config_validators import (
    validate_memory_fts_limit as _v_mem_fts,
)
from agent.services.config_validators import (
    validate_memory_max_inject_episodic as _v_mem_mie,
)
from agent.services.config_validators import (
    validate_memory_max_inject_semantic as _v_mem_mis,
)
from agent.services.config_validators import (
    validate_memory_embed_timeout_sec as _v_mem_met,
)
from agent.services.config_validators import (
    validate_memory_recency_days as _v_mem_rec,
)
from agent.services.config_validators import (
    validate_memory_retention_days as _v_mem_rtd,
)
from agent.services.config_validators import (
    validate_memory_rrf_k as _v_mem_rrf,
)
```
- Update `MemoryConfig.__post_init__` (lines 253-257):
```python
    def __post_init__(self) -> None:
        """Validate memory configuration fields after initialization."""
        _v_mem_fts(self)
        _v_mem_rrf(self)
        _v_mem_rec(self)
        _v_mem_mis(self)
        _v_mem_mie(self)
        _v_mem_met(self)
        _v_mem_rtd(self)
```

**3. Update `scripts/agent/config_builders.py` `_build_memory_config()` (lines 326-381):**
- Remove the four inline validation blocks (lines 335-361)
- Wrap `return MemoryConfig(...)` in try/except to convert `ValueError` -> `ConfigReloadValidationError`

```python
def _build_memory_config(cfg: dict[str, Any]) -> MemoryConfig:
    """Build MemoryConfig from a raw config dict."""
    use_memory_layer = _get_bool_or_default(cfg, "use_memory_layer", True)
    memory_jsonl_dir = _get_str(cfg, "memory_jsonl_dir") or "/opt/llm/memory"
    memory_max_inject_semantic = _get_int_or_default(
        cfg, "memory_max_inject_semantic", 5
    )
    memory_max_inject_episodic = _get_int_or_default(
        cfg, "memory_max_inject_episodic", 3
    )
    memory_min_importance = _get_float_or_default(cfg, "memory_min_importance", 0.3)
    memory_embed_enabled = _get_bool_or_default(cfg, "memory_embed_enabled", True)
    memory_dedup_threshold = _get_float_or_default(cfg, "memory_dedup_threshold", 0.3)
    memory_max_content_chars = _get_int_or_default(cfg, "memory_max_content_chars", 500)
    memory_embed_timeout_sec = _get_float_or_default(
        cfg, "memory_embed_timeout_sec", 5.0
    )
    memory_retention_days = _get_int_or_default(cfg, "memory_retention_days", 90)
    memory_fts_limit = _get_int_or_default(cfg, "memory_fts_limit", 50)
    memory_rrf_k = _get_int_or_default(cfg, "memory_rrf_k", 60)
    memory_recency_days = _get_float_or_default(cfg, "memory_recency_days", 7.0)
    memory_local_only = _get_bool_or_default(cfg, "memory_local_only", False)
    try:
        return MemoryConfig(
            use_memory_layer=use_memory_layer,
            memory_jsonl_dir=memory_jsonl_dir,
            memory_max_inject_semantic=memory_max_inject_semantic,
            memory_max_inject_episodic=memory_max_inject_episodic,
            memory_min_importance=memory_min_importance,
            memory_embed_enabled=memory_embed_enabled,
            memory_dedup_threshold=memory_dedup_threshold,
            memory_max_content_chars=memory_max_content_chars,
            memory_embed_timeout_sec=memory_embed_timeout_sec,
            memory_retention_days=memory_retention_days,
            memory_fts_limit=memory_fts_limit,
            memory_rrf_k=memory_rrf_k,
            memory_recency_days=memory_recency_days,
            memory_local_only=memory_local_only,
        )
    except ValueError as e:
        # Convert ValueError from MemoryConfig.__post_init__ validators
        # to ConfigReloadValidationError for reload path error handling
        raise ConfigReloadValidationError(str(e)) from e
```

## Compatibility considerations
- Error messages match exactly (preserves operator-facing messages)
- Reload path still raises `ConfigReloadValidationError` (error handling unchanged)
- Direct construction of `MemoryConfig` now self-validates (improves robustness)

## Security considerations
- None - validation logic only

## Rollback considerations
- Git revert of modified files if issues arise

## Validation plan
- Run `uv run pytest tests/agent/test_config_builders.py -v` - all pass
- Direct construction test: `MemoryConfig(memory_max_inject_semantic=-1)` raises `ValueError`
- Reload test: invalid toml value raises `ConfigReloadValidationError`

## Out of scope
- Tests (separate procedure)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-215146_require.md
- Source plan: plans/20260819-165438_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-125150
- Related target files: scripts/agent/services/config_validators.py, scripts/agent/config_dataclasses.py, scripts/agent/config_builders.py