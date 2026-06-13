# rag-pipeline-mcp — RAG パイプライン MCP サーバ仕様

## 1. 概要

`rag-pipeline-mcp` は 6 ステップの RAG パイプライン (MQE → Search → RRF → Rerank → Dedup → Augment) を HTTP MCP サーバとして公開するサービス。

- **ポート:** 8010
- **OpenRC サービス名:** `rag-pipeline-mcp`
- **関連スクリプト:**
  - `scripts/mcp/rag_pipeline/server.py` — FastAPI app + `RagPipelineMCPServer`
  - `scripts/mcp/rag_pipeline/service.py` — `RagPipelineMCPService` (サービス層)
  - `scripts/mcp/rag_pipeline/models.py` — Pydantic モデル + config adapter

### 依存方向

```
mcp/rag_pipeline/models → mcp/rag_pipeline/service → mcp/rag_pipeline/server
```

---

## 2. エンドポイント一覧

| Method | Path | 説明 |
|---|---|---|
| POST | `/rag_run_pipeline` | 通常パイプライン実行 |
| POST | `/rag_debug_pipeline` | 全中間出力付き実行 |
| POST | `/v1/search` | `RagPipeline.augment()` 向け後方互換エンドポイント |
| GET | `/v1/tools` | MCP ツール一覧 (最小互換形式) |
| POST | `/v1/call_tool` | MCP 標準ツール呼び出し |
| GET | `/health` | ヘルスチェック |

---

## 3. MCP ツール定義

### `rag_run_pipeline`

通常の RAG コンテキスト取得に使用する。

```json
{
  "name": "rag_run_pipeline",
  "description": "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated RAG pipeline.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":           { "type": "string" },
      "history_context": { "type": "array", "items": { "type": "string" } },
      "debug":           { "type": "boolean" }
    },
    "required": ["query"]
  }
}
```

**レスポンス (`RagRunResponse`):**

```json
{
  "query":          "string",
  "augmented_text": "string",
  "selected_hits":  [{ ... }]
}
```

### `rag_debug_pipeline`

`/rag search` 相当の観察・デバッグパス。全中間出力を返す。

```json
{
  "name": "rag_debug_pipeline",
  "description": "Run integrated RAG pipeline and return all intermediate stage outputs for debugging.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":           { "type": "string" },
      "history_context": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["query"]
  }
}
```

**レスポンス (`RagDebugResponse`):**

`RagRunResponse` の全フィールドに加え:

```json
{
  "queries":       ["string"],
  "merged_hits":   [{ ... }],
  "reranked_hits": [{ ... }],
  "elapsed":       { "mqe": 0.1, "search": 0.2, ... }
}
```

---

## 4. 後方互換エンドポイント: `/v1/search`

`rag/pipeline.py` の `augment()` メソッドが `rag_service_url` 設定時に呼び出す。

**リクエスト:**
```json
{ "query": "string", "history_context": "string" }
```

**レスポンス:**
```json
{ "context": "string", "selected_hits": [{ ... }] }
```

`selected_hits` は `rag/pipeline.py` が `self.last_reranked` に格納し、2 段階取得 (`use_two_stage_fetch`) に使用する。

---

## 5. 設定ファイル: `config/rag_pipeline_mcp_server.toml`

`config/agent.toml` / `config/common.toml` から独立したプロセス固有設定。

| キー | 説明 | デフォルト |
|---|---|---|
| `llm_url` | LLM エンドポイント (MQE・Rerank 用) | `http://127.0.0.1:8002/v1/chat/completions` |
| `embed_url` | 埋込 LLM エンドポイント | `http://127.0.0.1:8003/embedding` |
| `rag_db_path` | RAG SQLite DB パス | `/opt/llm/db/rag.sqlite` |
| `sqlite_vec_so` | sqlite-vec 拡張 (.so) パス | `/opt/llm/sqlite-vec/vec0.so` |
| `port` | HTTP Listen ポート | `8010` |
| `http_timeout` | 内部 HTTP タイムアウト (秒) | `120.0` |
| `use_mqe` | MQE 有効フラグ | `true` |
| `use_rrf` | RRF 有効フラグ | `true` |
| `use_rerank` | Rerank 有効フラグ | `true` |
| `use_refiner` | Refiner 有効フラグ | `false` |
| `rrf_k` | RRF スムージング定数 | `60` |
| `top_k_search` | KNN/FTS5 取得件数 | `10` |
| `top_k_rerank` | Rerank 候補数 | `10` |
| `rag_top_k` | Augment 最終選択数 | `5` |
| `rag_min_score` | Rerank 最低スコア閾値 | `0.0` |
| `max_chunks_per_doc` | 同一 Doc からの最大チャンク数 | `3` |
| `semantic_cache_max_size` | セマンティックキャッシュ最大エントリ数 | `128` |
| `semantic_cache_threshold` | キャッシュヒット閾値 | `0.92` |
| `refiner_max_tokens` | Refiner 最大トークン数 | `512` |
| `refiner_max_chars_per_chunk` | Refiner チャンク最大文字数 | `800` |
| `refiner_timeout` | Refiner HTTP タイムアウト (秒) | `30.0` |

---

## 6. クラス API

### `RagPipelineMCPService`

| メソッド | 説明 |
|---|---|
| `async start()` | 共有リソース初期化。FastAPI lifespan から呼び出す |
| `async stop()` | `AsyncClient` のクローズ |
| `async run_pipeline(req)` | 通常パイプライン実行。`RagRunResponse` を返す |
| `async run_debug_pipeline(req)` | デバッグ用全中間出力付き実行。`RagDebugResponse` を返す |
| `async run_search(req)` | `/v1/search` 後方互換ハンドラ。`RagSearchResponse` を返す |
| `async fmt_run_pipeline(args)` | LLM ツール結果用フォーマット (augmented_text を返す) |
| `async fmt_debug_pipeline(args)` | LLM ツール結果用 JSON サマリー |
| `get_dispatch_table()` | MCP ツール名 → ハンドラのマップを返す |

### `build_rag_cfg_adapter(cfg)`

`rag_pipeline_mcp_server.toml` の dict から `RagPipeline` が参照する `cfg.*` フィールドを持つ `SimpleNamespace` を構築する。

- `rag_service_url` は常に `""` (HTTP ループ防止)
- `use_search` は常に `True`

---

## 7. `agent.toml` との連携

```toml
rag_service_url = "http://127.0.0.1:8010"

[mcp_servers.rag_pipeline]
transport      = "http"
url            = "http://127.0.0.1:8010"
openrc_service = "rag-pipeline-mcp"

[tool_safety_tiers]
rag_run_pipeline   = "READ_ONLY"
rag_debug_pipeline = "READ_ONLY"
```

- `rag_service_url` が設定されると `RagPipeline.augment()` が HTTP モードに切り替わる
- `mcp_servers.rag_pipeline` でウォッチドッグ死活監視・起動時 `/v1/tools` diff チェックが有効になる
- `tool_definitions_strict=true` の場合は `tool_definitions` のツール名・description が `/v1/tools` レスポンスと完全一致する必要がある

---

## 8. 設計上の注意点

### モジュールレベル `_cfg` キャッシュの上書き

`RagPipelineMCPService.start()` は `rag/pipeline.py` のモジュールレベル `_cfg` を `rag_pipeline_mcp_server.toml` から読み込んだ値で上書きする。`rag/llm.py` はモジュールレベル `_cfg` を持たない (RagLLM はコンストラクタ経由で config を受け取る)。`db/helper.py` はインスタンス初期化時に設定を解決するためクラスレベルのキャッシュリセットは不要。各 MCP サーバは独立プロセスで動作するため、プロセス間汚染は発生しない。

### SQLiteHelper 設定の解決

`RagRepository` が `db.helper.SQLiteHelper` を経由して DB に接続する。`SQLiteHelper` はインスタンス初期化時に `rag_db_path` を設定ファイルから読み込むため、クラスレベルのキャッシュリセットは不要。

### `_service` モジュールレベルシングルトン

`_service` は `RagPipelineMCPService()` のインスタンス。モジュールロード時に即座に生成される。テスト時は `mcp.rag_pipeline.service._service` を直接操作する。
