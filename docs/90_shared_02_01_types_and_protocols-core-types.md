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

`agent/`、`mcp_servers/`、`rag/`、`db/` の各レイヤーで共通して使われる、`shared/` 内のすべての共通型・プロトコル・DTO・定数を定義する。

**要点:**
- `LLMMessage`、`RagConfig` は `shared/types.py` にある
- `LLMUsage`、`LLMResponse` は `shared/llm_types.py` にある(`LLMClient` なしでインポートできるよう分離)
- `ActionResult`、`ArtifactEvent`、`ShellPolicy` はそれぞれ `shared/action_result.py`、`shared/events.py`、`shared/protocols/shell.py` にある
- ツール定数のfrozensetは `shared/tool_constants.py` にある

---

## 2. 型定義の全体構造

主要な共通型一覧（詳細はコード参照）:

- `LLMMessage` (TypedDict) — `shared/types.py` — 全レイヤーで利用
- `RagConfig` (Protocol) — `shared/types.py` — `rag/`, `scripts/mcp_servers/rag_pipeline/`
- `RagHit` / `RawHit` / `MergedHit` / `RankedHit` (dataclass / Union alias) — `shared/types.py` — `rag/`, `agent/`, `shared/`
- `LLMUsage` / `LLMResponse` (frozen dataclass) — `shared/llm_types.py` — `agent/`, `shared/`
- `ActionResult` (frozen dataclass) — `shared/action_result.py` — `agent/`
- `ArtifactEvent` (TypedDict) — `shared/events.py` — `agent/`, `mcp_servers/github/`
- `ShellPolicy` (dataclass) — `shared/protocols/shell.py` — `mcp_servers/shell/`
- `DbConfig` (dataclass) — `db/config.py` — `db/`, `agent/`
- `CallToolRequest` / `CallToolResponse` (Pydantic) — `mcp_servers/models.py` — `mcp_servers/` 専用
- Tool frozensets — `shared/tool_constants.py` — `shared/`, `agent/`, `mcp_servers/`
- `ToolCallResult` / `TransportErrorInfo` (frozen dataclass) — `shared/transport_dto.py`
- `ToolSpec` (frozen dataclass) — `shared/tool_spec.py` — `agent/` (DAG mode)
- `CacheEntry` (frozen dataclass) — `shared/tool_cache.py` — `shared/` (ToolExecutor cache)
- `ToolDefinition` (frozen dataclass) — `shared/tool_registry.py` — `shared/`, `mcp_servers/`

---

## 3. `LLMMessage` (`shared/types.py`)

`role` (required), `content`/`tool_calls` (roleに応じて条件付き), `importance`/`pinned` (圧縮), `_ephemeral`/_`skill_ephemeral`/_`memory_injected` (ライフサイクル), `source` (検証) のフィールドカテゴリを持つ TypedDict。正典インポートは `from shared.types import LLMMessage`。`_LLMMessageRequired(TypedDict)` を継承して `role` を必須フィールドとして分離定義している。(Explicit in code)

ストリーミング時のツール呼び出し差分表現のための補助 TypedDict (`ToolCallFunctionDelta`, `ToolCallDelta`, `AccumulatedToolCall` など) も定義されている。(Explicit in code: `scripts/shared/types.py`)

---

## 4. `RagConfig` (`shared/types.py`)

セマンティックキャッシュ設定、検索パラメータ (`top_k_search`, `rag_top_k`)、リランクパラメータ (`use_rerank`, `top_k_rerank`, `rag_min_score`, `use_rrf`, `rrf_k`)、リファイナ設定 (`max_tokens`, `max_chars_per_chunk`, `timeout`)、サービスURL/認証。`@runtime_checkable` で `isinstance()` チェックが可能。`SimpleNamespace` アダプタでプロトコルを満たせる。ファイル形式のDTOではない。設定ファイル用DTOは別: `mcp_servers.rag_pipeline.rag_pipeline_models.RagPipelineConfig`(MCP TOML)、`rag.models_config.*`(ingestion TOML)。MCPアダプタは `build_rag_cfg_adapter()` を参照。(Explicit in code)

---

## 5. `RawHit`, `MergedHit`, `RankedHit`, `RagHit` (`shared/types.py`)

`RawHit` (base: `chunk_id`, `content`, `url`, `title`, `distance`, `bm25_score`) → `MergedHit` が `rrf_score` を追加 → `RankedHit` が `rerank_score | None` を追加。`shared/types.py` に正典として定義され、パイプラインの各ステージでフィールドが段階的に追加される。(Explicit in code: `scripts/shared/types.py`)

**実装上の補足:** `MergedHit` / `RankedHit` も `distance` / `bm25_score` を保持し続け、すべてのフィールドにデフォルト値があるため `chunk_id` と `content` 以外は省略可能。`rerank_score` のみ `None` を許容する。

**インポート:** `from shared.types import RagHit, RawHit, MergedHit, RankedHit`。`scripts/rag/types.py` はこれらの名前を再エクスポートしない — `shared.types` から直接インポートすること。

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
- `90_shared_02_03_types_and_protocols-reference.md`
