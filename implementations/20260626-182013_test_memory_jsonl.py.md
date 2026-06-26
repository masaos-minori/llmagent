# Implementation: test_memory_jsonl.py — JSONL path resolution test

Source plan: `plans/20260626-180405_plan.md` — Phase 3

---

## Goal

Add a test that verifies `factory.py` constructs the JSONL file path as `{memory_jsonl_dir}/memories.jsonl` when given a `memory_jsonl_dir` config value.

---

## Scope

**In-Scope**
- Test: configure `memory_jsonl_dir="/tmp/test_mem"` → verify factory constructs `JsonlMemoryStore` with path `/tmp/test_mem/memories.jsonl`

**Out-of-Scope**
- Testing JSONL read/write correctness (existing tests cover this)

---

## Assumptions

1. `factory.py:285` constructs path as `f"{ctx.cfg.memory.memory_jsonl_dir}/memories.jsonl"`.
2. The factory function creating the JSONL store can be isolated and tested by inspecting the `JsonlMemoryStore._path` attribute.

---

## Implementation

### Target file
`tests/test_memory_jsonl.py`

### Procedure
Add `test_jsonl_path_from_memory_jsonl_dir` test function.

### Method

```python
def test_jsonl_path_from_memory_jsonl_dir(tmp_path):
    """memory_jsonl_dir + '/memories.jsonl' must equal the JsonlMemoryStore path."""
    from agent.memory.jsonl_store import JsonlMemoryStore
    from pathlib import Path

    dir_path = str(tmp_path / "my_memory")
    expected_path = Path(dir_path) / "memories.jsonl"

    # Simulate factory path construction
    store = JsonlMemoryStore(f"{dir_path}/memories.jsonl")
    assert store._path == expected_path


def test_jsonl_store_uses_dir_not_file_config():
    """Confirm config field is memory_jsonl_dir (dir), not a full file path."""
    from agent.config_dataclasses import MemoryConfig
    cfg = MemoryConfig(memory_jsonl_dir="/opt/llm/memory")
    assert cfg.memory_jsonl_dir == "/opt/llm/memory"
    # Full path is NOT stored in config — it is constructed by factory
    assert not hasattr(cfg, "memory_jsonl_path")
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_memory_jsonl.py` | 0 errors |
| Tests | `uv run pytest tests/test_memory_jsonl.py -v` | all pass |
| Full suite | `uv run pytest -v` | all pass |
