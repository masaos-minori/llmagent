# Implementation: Replace hardcoded fstring path with Path-based construction in _build_jsonl_store

## Goal

Replace the hardcoded fstring path in `_build_jsonl_store` with a `Path`-based construction that respects `MemoryConfig.memory_jsonl_dir`.

## Scope

- **In-Scope**:
  - `scripts/agent/factory.py` — update `_build_jsonl_store` to use `Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl"`
  - `tests/test_agent_factory.py` — add a test verifying that `memory_jsonl_dir="/opt/llm/memory"` produces `/opt/llm/memory/memories.jsonl`
- **Out-of-Scope**:
  - `agent/config_dataclasses.py` (no changes needed; `memory_jsonl_dir` default is already correct)
  - `agent/config_builders.py` (no changes needed)
  - `agent/memory/jsonl_store.py` (constructor already accepts a `Path`)
  - DB schema, public API, CLI interface

## Assumptions

- `JsonlMemoryStore.__init__` accepts both `str` and `Path` (confirmed: `path: str | Path` at line 52).
- `memory_jsonl_dir` is always a non-empty string when `use_memory_layer=True` (enforced by `_validate_memory_jsonl_dir`).
- The fstring and `Path`-join produce identical results for well-formed paths; the change is about type-safety and consistency, not behavior.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether `JsonlMemoryStore` constructor signature accepts `Path` or only `str` | Confirmed: `__init__(self, path: str | Path)` at line 52 — both accepted |

## Implementation

### Target file: `scripts/agent/factory.py`

#### Procedure

Update `_build_jsonl_store` to use `Path`-based construction instead of fstring.

#### Method

Direct file edit — replace line 286.

#### Details

**Replace line 286:**
```python
# Before:
return jsonl_cls(f"{ctx.cfg.memory.memory_jsonl_dir}/memories.jsonl")

# After:
return jsonl_cls(Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl")
```

### Target file: `tests/test_agent_factory.py`

#### Procedure

Add a test class `TestBuildJsonlStore` that verifies Path-based path construction.

#### Method

Direct file edit — append new test class after existing tests.

#### Details

**Append to `tests/test_agent_factory.py`:**
```python
class TestBuildJsonlStore:
    def test_jsonl_store_path_is_path_based(self) -> None:
        """Verify _build_jsonl_store uses Path-based construction, not fstring."""
        from agent.factory import _build_jsonl_store  # noqa: PLC0415

        class MockJsonlStore:
            def __init__(self, path):  # noqa: ANN001 — testing
                self.path = path

        ctx = MagicMock()
        ctx.cfg.memory.memory_jsonl_dir = "/opt/llm/memory"

        result = _build_jsonl_store(ctx, MockJsonlStore)  # type: ignore[arg-type]

        assert isinstance(result.path, Path)
        assert result.path == Path("/opt/llm/memory/memories.jsonl")
        # Verify it is NOT a plain string (fstring would produce str)
        assert not isinstance(result.path, str)

    def test_jsonl_store_path_uses_custom_dir(self) -> None:
        """Verify _build_jsonl_store respects custom memory_jsonl_dir."""
        from agent.factory import _build_jsonl_store  # noqa: PLC0415

        class MockJsonlStore:
            def __init__(self, path):  # noqa: ANN001 — testing
                self.path = path

        ctx = MagicMock()
        ctx.cfg.memory.memory_jsonl_dir = "/custom/path/memory"

        result = _build_jsonl_store(ctx, MockJsonlStore)  # type: ignore[arg-type]

        assert result.path == Path("/custom/path/memory/memories.jsonl")
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/factory.py` | Unit test: `_build_jsonl_store` called with mock cls | `uv run pytest tests/test_agent_factory.py -v` | Mock cls called with `Path("/opt/llm/memory/memories.jsonl")` |
| `tests/test_agent_factory.py` | New test: assert path argument equals `Path(dir) / "memories.jsonl"` | `uv run pytest tests/test_agent_factory.py::TestBuildJsonlStore -v` | All assertions pass |
| `scripts/agent/memory/jsonl_store.py` | Existing JSONL store tests unchanged | `uv run pytest tests/test_memory_jsonl.py -v` | All existing tests pass |

## Risks & Mitigations

- **Risk**: `JsonlMemoryStore` constructor expects `str`, not `Path`, causing a `TypeError` at runtime. → **Mitigation**: Verified constructor signature accepts `str | Path` — no risk.
- **Risk**: Test infrastructure for `_build_jsonl_store` (a private function) is fragile if internals change. → **Mitigation**: Import the private function directly in the test, consistent with the existing test pattern in `test_agent_factory.py`.
