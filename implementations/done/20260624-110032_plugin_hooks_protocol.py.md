# Implementation Procedure: scripts/shared/plugin_registry.py + docs

## Goal

`PipelineHook` typed Protocol を定義し、フックのコントラクトを明文化する。

## Scope

**In:**
- `scripts/shared/plugin_registry.py` — `PipelineHook` Protocol 定義; `run_pipeline_stages` のシグネチャ更新
- `docs/03_rag_03_query_pipeline.md` — フックコントラクトのドキュメント

**Out:** 新しいプラグインの実装、プラグインビジネスロジックの変更

## Implementation

### plugin_registry.py — PipelineHook Protocol

```python
from typing import Protocol, runtime_checkable
from rag.models_result import RagHit

@runtime_checkable
class PipelineHook(Protocol):
    """Post-rerank pipeline hook contract.

    Input:  list[RagHit] + query str
    Output: list[RagHit] (modified or filtered)
    strict=True:  exception propagates; pipeline fails
    strict=False: exception logged as WARNING; original hits returned
    """
    async def __call__(self, hits: list[RagHit], query: str) -> list[RagHit]: ...
```

### run_pipeline_stages シグネチャ更新

```python
# Before:
def run_pipeline_stages(hits: list[RagHit], query: str, strict: bool = False) -> list[RagHit]:

# After:
def run_pipeline_stages(
    hooks: list[PipelineHook], hits: list[RagHit], query: str, strict: bool = False
) -> list[RagHit]:
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Protocol 存在 | `grep -n "PipelineHook" scripts/shared/plugin_registry.py` | found |
| Lint | `uv run ruff check scripts/shared/plugin_registry.py` | 0 errors |
| Tests | `uv run pytest tests/ -k "plugin" -x -q` | all pass |
