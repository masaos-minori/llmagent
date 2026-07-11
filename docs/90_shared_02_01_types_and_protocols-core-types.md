---
title: "Shared Types and Protocols - Core Types"
category: shared
tags:
  - shared
  - types
  - protocols
  - llmmessage
  - ragconfig
  - hit-types
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
  - 90_shared_02_03_types_and_protocols-reference.md
source:
  - 90_shared_02_01_types_and_protocols-core-types.md
---

# Shared Types and Protocols

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 1. 目的

`agent/`、`mcp/`、`rag/`、`db/` の各レイヤーで共通して使われる、`shared/` 内のすべての共通型・プロトコル・DTO・定数を定義する。

**要点:**
- `LLMMessage`、`RagConfig` は `shared/types.py` にある
- `LLMUsage`、`LLMResponse` は `shared/llm_types.py` にある(`LLMClient` なしでインポートできるよう分離)
- `ActionResult`、`ArtifactEvent`、`ShellPolicy` はそれぞれ `shared/action_result.py`、`shared/events.py`、`shared/protocols/shell.py` にある
- ツール定数のfrozensetは `shared/tool_constants.py` にある

---

## 2. 型定義の全体構造

| 型 | 種別 | ファイル | 利用レイヤー |
|---|---|---|---|
| `LLMMessage` | TypedDict | `shared/types.py` | All layers |
| `RagConfig` | Protocol | `shared/types.py` | `rag/`, `scripts/mcp_servers/rag_pipeline/` |
| `RagHit` / `RawHit` / `MergedHit` / `RankedHit` | dataclass / Union alias | `shared/types.py` | `rag/`, `agent/`, `shared/` |
| `LLMUsage` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `LLMResponse` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `ActionResult` | frozen dataclass | `shared/action_result.py` | `agent/` |
| `ArtifactEvent` | TypedDict | `shared/events.py` | `agent/`, `mcp/github/` |
| `ShellPolicy` | dataclass | `shared/protocols/shell.py` | `mcp/shell/` |
| `DbConfig` | dataclass | `db/config.py` | `db/`, `agent/` |
| `CallToolRequest` / `CallToolResponse` | Pydantic models | `mcp/models.py` | `mcp/` only |
| Tool frozensets | `frozenset[str]` | `shared/tool_constants.py` | `shared/`, `agent/`, `mcp/` |
| `ToolCallResult` | frozen dataclass | `shared/transport_dto.py` | `agent/`, `mcp/`, `shared/` |
| `TransportErrorInfo` | frozen dataclass | `shared/transport_dto.py` | `agent/`, `shared/` (audit logs) |
| `ToolSpec` | frozen dataclass | `shared/tool_spec.py` | `agent/` (DAG mode) |
| `CacheEntry` | frozen dataclass | `shared/tool_cache.py` | `shared/` (ToolExecutor cache) |
| `PluginFailure` | frozen dataclass | `shared/plugin_result.py` | `shared/`, `agent/` |
| `PluginLoadResult` | frozen dataclass | `shared/plugin_result.py` | `shared/`, `agent/` |
| `ToolDefinition` | frozen dataclass | `shared/tool_registry.py` | `shared/`, `mcp/` |

---

## 3. `LLMMessage` (`shared/types.py`)

```python
class LLMMessage(TypedDict, total=False):
    role: Literal["user", "assistant", "tool", "system"]  # always required in practice
    content: str | None   # None when message contains only tool_calls
    tool_calls: list[dict]   # assistant role only
    tool_call_id: str        # tool role only
    name: str               # tool role only
    importance: float       # message importance score for compression prioritization
    pinned: bool            # preserve during history compression
```

- `total=False` は技術的には全フィールドが省略可能を意味するが、`role` は常に必須
- 正典インポート: `from shared.types import LLMMessage`(agent/、rag/、shared/全体で20以上のモジュールから利用)

---

## 4. `RagConfig` (`shared/types.py`)

```python
@runtime_checkable
class RagConfig(Protocol):
    semantic_cache_max_size: int
    semantic_cache_threshold: float
    use_mqe: bool
    top_k_search: int
    use_rerank: bool
    rag_top_k: int
    max_chunks_per_doc: int
    top_k_rerank: int
    rag_min_score: float
    use_rrf: bool
    use_search: bool
    rag_service_url: str
    rag_auth_token: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
    use_semantic_cache: bool
```

- `@runtime_checkable` — `isinstance()` チェックが可能
- `RagPipeline`(`scripts/rag/pipeline.py`)で使用され、`scripts/mcp_servers/rag_pipeline/service.py` から利用される
- `agent/` は `RagConfig` を直接使用しない(インプロセスのRAGパイプラインを持たない)
- `SimpleNamespace` アダプタでこのプロトコルを満たすことができる

---

## 5. `RawHit`, `MergedHit`, `RankedHit`, `RagHit` (`shared/types.py`)

```python
@dataclasses.dataclass
class RawHit:
    """Raw search result from vector or FTS search."""
    chunk_id: int
    content: str
    url: str
    title: str
    distance: float | None = None
    bm25_score: float | None = None

@dataclasses.dataclass
class MergedHit:
    """RawHit after RRF merge; carries aggregated rrf_score."""
    chunk_id: int
    content: str
    url: str
    title: str
    rrf_score: float

@dataclasses.dataclass
class RankedHit:
    """MergedHit after cross-encoder rerank; carries rerank_score."""
    chunk_id: int
    content: str
    url: str
    title: str
    rrf_score: float
    rerank_score: float

RagHit = RawHit | MergedHit | RankedHit
```

- `shared/types.py` に正典として定義されており、パイプラインの各ステージでフィールドが段階的に追加される
- **インポート:** `from shared.types import RagHit, RawHit, MergedHit, RankedHit`
- `scripts/rag/types.py` はこれらの名前をもはや再エクスポートしない — 後方互換用の再エクスポートは削除済み。`shared.types` から直接インポートすること
- `rag/`、`agent/`、`shared/plugin_registry.py` から利用される

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
- `90_shared_02_03_types_and_protocols-reference.md`

## Keywords

types
protocols
LLMMessage
RagConfig
RawHit
MergedHit
RankedHit
RagHit
