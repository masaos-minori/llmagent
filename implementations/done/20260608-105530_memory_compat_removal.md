# Implementation: Memory Layer Backward-Compat Removal

## Goal

Remove backward-compat artifacts from `agent/memory/` and clarify public API boundaries.

## Scope

**In:**
- `types.py`: remove `SOURCE_TYPES` frozenset constant (internal use only; replace with inline list comprehension in error message)
- `ingestion.py`: update comments to clarify `DedupAction.LINK_ONLY` is functional, not compat-only

**Out:**
- `DedupAction.LINK_ONLY` removal (confirmed functional: used in behavior-lock tests)
- Large-scale refactors (store centralization, scoring unification) — deferred; need separate behavior-lock tests first

## Assumptions

- `SOURCE_TYPES` is referenced only inside `types.py` for the `MemoryEntry.__post_init__` error message
- `DedupAction.LINK_ONLY` is used in `test_memory_layer.py` and represents a distinct functional mode

## Implementation

### `scripts/agent/memory/types.py`

Remove module-level constant:
```python
# deleted:
SOURCE_TYPES: frozenset[str] = frozenset(v.value for v in SourceType)
```

Replace error message reference:
```python
# before:
f"Invalid source_type={self.source_type!r}; must be one of {SOURCE_TYPES}"
# after:
f"Invalid source_type={self.source_type!r}; must be one of {[v.value for v in SourceType]}"
```

### `scripts/agent/memory/ingestion.py`

Update docstring and `LINK_ONLY` comment to reflect actual behavior (not "backward-compatible default").

## Validation plan

```bash
uv run ruff check scripts/agent/memory/
uv run mypy scripts/
uv run pytest tests/test_memory_*.py -v
```
