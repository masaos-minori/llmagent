# Implementation Procedure: scripts/rag/models_result.py + pipeline_service.py + pipeline.py

## Goal

`SearchDiagnostics` にリモート HTTP モード用フィールドを追加する。

## Scope

**In:**
- `scripts/rag/models_result.py` — `ResultSource`, `HttpResultKind` enum + `SearchDiagnostics` 拡張
- `scripts/rag/pipeline_service.py` — 新フィールドを populate
- `scripts/rag/pipeline.py` — `result_source` の割り当て

**Out:** リモートリトライポリシーの再設計

## Implementation

### models_result.py — enum + SearchDiagnostics 拡張

```python
import enum

class ResultSource(str, enum.Enum):
    REMOTE = "remote"
    LOCAL = "local"
    FALLBACK = "fallback"

class HttpResultKind(str, enum.Enum):
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    NOT_USED = "not_used"

@dataclass(frozen=True)
class SearchDiagnostics:
    embed_ok: int = 0
    embed_failed: int = 0
    fts_errors: int = 0
    # Remote mode fields (new):
    result_source: ResultSource = ResultSource.LOCAL
    http_result_kind: HttpResultKind = HttpResultKind.NOT_USED
    remote_status_code: int | None = None
    remote_latency_ms: float | None = None
    fallback_reason: str | None = None
```

### pipeline_service.py — 新フィールド populate

```python
# call_rag_service() の戻り値に status_code と latency_ms を含める
# 成功時: http_result_kind=SUCCESS, result_source=REMOTE
# 失敗時: http_result_kind=ERROR, result_source=FALLBACK, fallback_reason=...
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| フィールド存在 | `grep -n "result_source\|http_result_kind" scripts/rag/models_result.py` | found |
| Tests | `uv run pytest tests/ -k "pipeline" -x -q` | all pass |
