# 共通仕様 (Shared Normalization)

`scripts/` に配置された共通モジュール群のインデックスと、複数モジュールが共有する型・プロトコル仕様の定義。

## モジュールインデックス

| ファイル | 収録モジュール |
|---|---|
| [`06_ref-infra.md`](06_ref-infra.md) | `shared/config_loader.py` / `rag/utils.py` / `shared/logger.py` / `shared/formatters.py` / `shared/otel_tracer.py` / `shared/git_helper.py` / `shared/tool_constants.py` / `shared/route_resolver.py` |
| [`06_ref-mcp.md`](06_ref-mcp.md) | `mcp/models.py` / `mcp/server.py` / `shared/tool_executor.py` |

---

## 共通プロトコル仕様

### MCP `/v1/call_tool` リクエスト / レスポンス

→ `04_mcp-protocol.md` §1 HTTP API フォーマット早見表 を参照 (`CallToolRequest` / `CallToolResponse` Pydantic モデルの定義は `06_ref-mcp.md` §mcp_models.py)。

### プラグイン / ローカルツールの戻り値規約

`@register_tool("tool_name")` で登録するローカル Python ツールのハンドラは必ず `tuple[str, bool]` を返す。

```python
async def fn(args: dict) -> tuple[str, bool]:
    # (result_text, is_error) — CallToolResponse の result / is_error と同一の意味
    return "結果テキスト", False
```

---

## 共通型定義

### RagHit TypedDict

`rag/types.py` で定義。検索・スコアリング結果を表す型。パイプライン各ステージで段階的にフィールドが追加される (`total=False` のため全フィールドオプション)。

```python
from rag.types import RagHit
```

| キー | 型 | 追加ステージ | 説明 |
|---|---|---|---|
| `chunk_id` | `int` | vector/fts search | チャンク ID |
| `content` | `str` | vector/fts search | チャンク本文 (原文) |
| `url` | `str` | vector/fts search | 元ドキュメント URL |
| `title` | `str` | vector/fts search | 元ドキュメントタイトル |
| `distance` | `float` | vector_search のみ | L2 距離 (小さいほど近い) |
| `bm25_score` | `float` | fts_search のみ | BM25 スコア (負値; 絶対値が大きいほど高関連) |
| `rrf_score` | `float` | rrf_merge 以降 | RRF スコア (大きいほど高関連) |
| `rerank_score` | `float` | rerank 以降 | Cross-Encoder の関連度スコア (大きいほど高関連) |

### LLMMessage TypedDict

`shared/types.py` で定義 (`TypedDict, total=False`)。LLM API メッセージを表す型。`AgentContext.history` の要素型として使用。`total=False` のため TypedDict としては全フィールドオプションだが、`role` は実質必須 (実装コメント: `role always required`)。`rag/types.py` から再エクスポートされているため、`rag` 層からは `from rag.types import LLMMessage` でも参照可能。

```python
from shared.types import LLMMessage
# または rag 層から
from rag.types import LLMMessage
```

| キー | 型 | 使用ロール | 説明 |
|---|---|---|---|
| `role` | `str` | 全ロール | `"user"` / `"assistant"` / `"tool"` / `"system"` |
| `content` | `str \| None` | 全ロール | テキストコンテンツ。tool_calls のみ含む assistant ロールでは `None` |
| `tool_calls` | `list[dict]` | assistant のみ | アシスタントが要求したツール呼び出しリスト |
| `tool_call_id` | `str` | tool のみ | ツール呼び出し応答の対応 ID |
| `name` | `str` | tool のみ | ツール名 |

### RagConfig Protocol

`shared/types.py` で定義 (`@runtime_checkable` な `typing.Protocol`)。`RagPipeline` (`rag/pipeline.py`) が消費する設定オブジェクトの構造プロトコル。利用先は `mcp/rag_pipeline/service.py` など RAG MCP サーバ側のみ。agent 本体 (`agent/`) は in-process RagPipeline を呼び出さないため、このプロトコルを直接使用しない。`SimpleNamespace` アダプターが満たす構造であれば `isinstance()` チェックが通る。`agent` パッケージをインポートせずに `rag` 層から利用できるよう分離されている。

```python
from shared.types import RagConfig
```

| フィールド | 型 | 説明 |
|---|---|---|
| `semantic_cache_max_size` | `int` | セマンティックキャッシュの最大エントリ数 |
| `semantic_cache_threshold` | `float` | セマンティックキャッシュのコサイン類似度しきい値 |
| `use_mqe` | `bool` | MQE (Multi-Query Expansion: 複数クエリ展開) を使用するか |
| `top_k_search` | `int` | ベクトル / FTS 検索で取得する上位件数 |
| `use_rerank` | `bool` | Cross-Encoder による再ランク付けを使用するか |
| `rag_top_k` | `int` | RAG 最終出力として LLM に渡すチャンク数 |
| `max_chunks_per_doc` | `int` | 同一ドキュメントから返す最大チャンク数 |
| `top_k_rerank` | `int` | 再ランク付け対象として渡す上位件数 |
| `rag_min_score` | `float` | 最終チャンクのスコアフィルタしきい値 |
| `use_rrf` | `bool` | RRF (Reciprocal Rank Fusion: 逆順位融合) によるスコア統合を使用するか |
| `use_search` | `bool` | RAG 検索ステップ自体を有効にするか |
| `rag_service_url` | `str` | RAG サービスのベース URL |
| `use_refiner` | `bool` | チャンク内容の精製 (Refiner) を使用するか |
| `refiner_max_tokens` | `int` | Refiner が出力する最大トークン数 |
| `refiner_max_chars_per_chunk` | `int` | Refiner に渡す 1 チャンクあたりの最大文字数 |
| `refiner_timeout` | `float` | Refiner の HTTP タイムアウト (秒) |
