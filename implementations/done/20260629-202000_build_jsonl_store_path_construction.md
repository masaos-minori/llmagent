# Implementation Design: Replace Hardcoded fstring Path in _build_jsonl_store

## Goal

Replace the hardcoded fstring path in `_build_jsonl_store` with a `Path`-based construction that respects `MemoryConfig.memory_jsonl_dir`.

## Scope

- **In-Scope**:
  - `scripts/agent/factory.py` — update `_build_jsonl_store` to use `Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl"`
  - `tests/test_agent_factory.py` — add test verifying `memory_jsonl_dir="/opt/llm/memory"` produces `/opt/llm/memory/memories.jsonl`
- **Out-of-Scope**:
  - `agent/config_dataclasses.py` (no changes needed; `memory_jsonl_dir` default is already correct)
  - `agent/config_builders.py` (no changes needed)
  - `agent/memory/jsonl_store.py` (constructor already accepts `str | Path`)
  - DB schema, public API, CLI interface

## Implementation Steps

### Phase 1: Core Logic Implementation

1. In `scripts/agent/factory.py`, update `_build_jsonl_store`:
   - Changed from `return jsonl_cls(f"{ctx.cfg.memory.memory_jsonl_dir}/memories.jsonl")`
   - To `return jsonl_cls(Path(ctx.cfg.memory.memory_jsonl_dir) / "memories.jsonl")`
   - `Path` is already imported at the top of the file (line 13)

2. In `tests/test_agent_factory.py`, added `TestBuildJsonlStore` class with three tests:
   - `test_uses_path_based_construction` — verifies Path-based construction with mock
   - `test_does_not_use_hardcoded_fstring` — asserts path does not start with `/memories.jsonl`
   - `test_path_join_with_trailing_slash` — verifies Path handles trailing slashes correctly

## Validation Results

- All 15 tests in `tests/test_agent_factory.py` pass (including 3 new tests)
- All 20 tests in `tests/test_memory_jsonl.py` pass — no regressions

## Acceptance Criteria

- [x] `_build_jsonl_store` uses Path-based construction instead of fstring
- [x] Test verifies `memory_jsonl_dir="/opt/llm/memory"` produces correct path
- [x] Test asserts no hardcoded root path `/memories.jsonl`
- [x] All existing tests pass
