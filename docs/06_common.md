# 共通仕様 (Shared Normalization)

`scripts/` に配置された共通モジュール群のインデックスと、複数モジュールが共有する型・プロトコル仕様の定義。

## モジュールインデックス

| ファイル | 収録モジュール |
|---|---|
| [`06_ref-sqlite.md`](06_ref-sqlite.md) | `sqlite_helper.py` |
| [`06_ref-infra.md`](06_ref-infra.md) | `config_loader.py` / `rag_utils.py` / `logger.py` / `formatters.py` |
| [`06_ref-mcp.md`](06_ref-mcp.md) | `mcp_models.py` / `mcp_server.py` / `tool_executor.py` |
| [`06_ref-rag.md`](06_ref-rag.md) | `agent_rag.py` |
| [`06_ref-agent.md`](06_ref-agent.md) | `agent_session.py` / `agent_repl.py` / `agent_config.py` / `agent_context.py` / `cli_view.py` / `agent_commands.py` / `llm_client.py` / `history_manager.py` |

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

`rag_types.py` で定義。検索・スコアリング結果を表す型。パイプライン各ステージで段階的にフィールドが追加される (`total=False` のため全フィールドオプション)。

```python
from rag_types import RagHit
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
| `rerank_score` | `float` | cross_encoder_rerank のみ | Cross-Encoder スコア 0〜10 (大きいほど高関連) |

### LLMMessage TypedDict

`rag_types.py` で定義。LLM API メッセージを表す型。`AgentContext.history` の要素型として使用 (`total=False` のため全フィールドオプション)。

```python
from rag_types import LLMMessage
```

| キー | 型 | 使用ロール | 説明 |
|---|---|---|---|
| `role` | `str` | 全ロール | `"user"` / `"assistant"` / `"tool"` / `"system"` |
| `content` | `str \| None` | 全ロール | テキストコンテンツ。tool_calls のみ含む assistant ロールでは `None` |
| `tool_calls` | `list[dict]` | assistant のみ | アシスタントが要求したツール呼び出しリスト |
| `tool_call_id` | `str` | tool のみ | ツール呼び出し応答の対応 ID |
| `name` | `str` | tool のみ | ツール名 |
