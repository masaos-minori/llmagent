# RAG パイプラインモジュール

RAG (Retrieval-Augmented Generation) パイプライン全ステップを実装するモジュール。

| モジュール | 役割 |
|---|---|
| `rag/pipeline.py` | `RagPipeline` — MQE / KNN+BM25 検索 / RRF / Cross-Encoder 再ランクのオーケストレーション |

---

## 1. rag/pipeline.py

### 1.1 機能概要

RAG パイプラインの全ステップを実装するモジュール。`RagPipeline` クラスがパイプライン全体をオーケストレーションし、`agent/repl.py` は `ctx.rag.augment()` 経由で呼び出し。

パイプライン実行順:

```
[1] MQE     — RagLLM.expand_queries:         クエリを N 通りに言い換えて再現率を向上させる
[2] Search  — get_embedding /                 埋込ベクトルを生成し KNN + BM25 で検索する
              RagRepository.vector_search /
              RagRepository.fts_search
[3] RRF     — RagScorer.rrf_merge:            複数クエリの結果リストを RRF スコアで統合する
[4] Rerank  — RagLLM.cross_encoder_rerank:    LLM が候補チャンクを関連度スコアで再順位付けする
```

クラス層 (関心の分離):

| クラス | 責務 |
|---|---|
| `RagRepository` | すべての SQL をここに閉じ込める。`vector_search` / `fts_search` を提供し、呼び出しごとに `query` / `fts_query` / `top_k` / `elapsed_ms` をログ出力する |
| `RagScorer` | スコア融合 (RRF)。`rrf_merge` を静的メソッドとして提供する |
| `RagLLM` | LLM 呼び出し (MQE クエリ拡張 + クロスエンコーダ再ランク)。共通 `_call_llm()` に HTTP 処理を集約する |

モジュールレベル関数 (`expand_queries`, `vector_search`, `fts_search`, `rrf_merge`, `cross_encoder_rerank`) はクラス層への委譲ラッパで、`agent/repl.py` との後方互換 API を維持。

### 1.2 API

```python
import httpx
from rag.pipeline import (
    RagRepository, RagScorer, RagLLM, SemanticCache,  # クラス層
    vector_search, fts_search, rrf_merge,              # モジュールレベルラッパ
    fetch_full_document, deduplicate_chunks, cosine_sim,
)
```

クラス層 API:

| クラス | メソッド | シグネチャ | 説明 |
|---|---|---|---|
| `RagRepository(db)` | `vector_search` | `(embedding, top_k) -> list[RagHit]` | KNN 検索; `top_k`/`elapsed_ms` をログ出力 |
| | `fts_search` | `(query, top_k) -> list[RagHit]` | BM25 検索; `query`/`fts_query`/`top_k`/`elapsed_ms` をログ出力 |
| `RagScorer` | `rrf_merge` (static) | `(results_list, rrf_k=60) -> list[RagHit]` | RRF スコアで結果リストを統合 |
| `RagLLM(client, chat_url)` | `expand_queries` | `(query, context="") -> list[str]` | MQE クエリ拡張。失敗時は `[query]` を返す |
| | `cross_encoder_rerank` | `(query, candidates, top_k) -> list[RagHit]` | クロスエンコーダ再ランク |
| | `summarize_tool_result` | `(text, tool_name, args) -> str` | ツール結果を LLM で要約して返す |
| | `refine_context` | `(query, chunks) -> str` | Rerank 後チャンクをクエリ関連要点に圧縮して返す |

モジュールレベル関数:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]` | `RagRepository.vector_search` に委譲 |
| `fts_search` | `(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]` | `RagRepository.fts_search` に委譲。FTS5 構文エラー時は空リストを返す |
| `rrf_merge` | `(results_list: list[list[RagHit]]) -> list[RagHit]` | `RagScorer.rrf_merge` に委譲。`rrf_k` は `agent.json` から取得する |
| `fetch_full_document` | `(chunk_ids: list[int], db: SQLiteHelper, window: int) -> list[RagHit]` | 指定チャンクの周辺 `window` 件を展開して返す (二段階取得用) |
| `deduplicate_chunks` | `(hits: list[RagHit], max_per_doc: int) -> list[RagHit]` | URL をキーに同一ドキュメントのチャンクを `max_per_doc` 件に絞る |
| `cosine_sim` | `(a: list[float], b: list[float]) -> float` | 2 つの埋込ベクトルのコサイン類似度を返す (セマンティックキャッシュ用) |

`SemanticCache` クラス:

```python
from rag.pipeline import SemanticCache

cache = SemanticCache(max_size=100, threshold=0.92)
```

| メソッド | 説明 |
|---|---|
| `lookup(embedding) -> str \| None` | コサイン類似度 >= `threshold` のエントリを探してコンテキスト文字列を返す。なければ `None` |
| `put(embedding, context_str) -> None` | エントリを格納。`prune()` で `max_size` 上限管理 |
| `prune() -> None` | `max_size` 超のエントリを古い順に削除 (FIFO) |
| `size() -> int` | 現在のエントリ数を返す |

### 1.3 エクスポートされる TypedDict

#### RagHit

各関数の戻り値リストの要素は `RagHit` TypedDict (`total=False`) で定義されており、パイプライン各ステージで段階的にフィールドが追加:

| キー | 型 | 説明 |
|---|---|---|
| `chunk_id` | `int` | チャンク ID |
| `content` | `str` | チャンク本文 |
| `url` | `str` | 元ドキュメント URL |
| `title` | `str` | 元ドキュメントタイトル |
| `distance` | `float` | L2 距離 (`vector_search` のみ; 小さいほど近い) |
| `bm25_score` | `float` | BM25 スコア (`fts_search` のみ; 負値、絶対値が大きいほど高関連) |
| `rrf_score` | `float` | RRF スコア (`rrf_merge` 以降; 大きいほど高関連) |
| `rerank_score` | `float` | Cross-Encoder スコア 0〜10 (`cross_encoder_rerank` のみ; 大きいほど高関連) |

#### LLMMessage

LLM API メッセージを表す `LLMMessage` TypedDict (`total=False`)。`AgentREPL._history` の要素型および `RagLLM._call_llm()` の引数型として使用。

```python
from rag.pipeline import LLMMessage
```

| キー | 型 | 説明 |
|---|---|---|
| `role` | `str` | メッセージロール (`"user"` / `"assistant"` / `"tool"` / `"system"`) |
| `content` | `str \| None` | テキストコンテンツ。tool_calls のみ含むメッセージでは `None` になる |
| `tool_calls` | `list[dict]` | アシスタントが要求したツール呼び出しリスト (assistant ロールのみ) |
| `tool_call_id` | `str` | ツール呼び出し応答の対応 ID (tool ロールのみ) |
| `name` | `str` | ツール名 (tool ロールのみ) |

`total=False` のため全フィールドはオプション。各ロールで実際に使うキーのみを設定。

### 1.4 設定項目

`config/common.toml` と `config/agent.toml` から初回アクセス時に遅延ロードする (`_get_cfg()`)。

| パラメータ | 設定ファイル | デフォルト | 説明 |
|---|---|---|---|
| `chat_url` | `config/agent.toml` | `http://127.0.0.1:8002/v1/chat/completions` | MQE / Rerank 用 LLM エンドポイント (`RagLLM` が使用) |
| `embed_url` | `config/common.toml` | `http://127.0.0.1:8003/embedding` | 埋込 API エンドポイント (`get_embedding` が使用) |
| `mqe_n_queries` | `config/agent.toml` | `3` | MQE で生成するクエリ言い換え数 |
| `rrf_k` | `config/agent.toml` | `60` | RRF の平滑化定数 (`RagScorer.rrf_merge` に渡す) |
| `mqe_prompt_template` | `config/agent.toml` | (既定テキスト) | MQE クエリ言い換えプロンプトテンプレート。`{n_queries}` と `{query}` をプレースホルダとして使用 |
| `rerank_prompt_template` | `config/agent.toml` | (既定テキスト) | Cross-Encoder 再ランクスコアリングプロンプトテンプレート。`{query}` と `{items_text}` をプレースホルダとして使用 |

### 1.5 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `ctx.rag = RagPipeline(...)` を `run()` で生成。`_handle_user_message()` が `ctx.rag.augment()` を呼び出す |
| `agent/commands/registry.py` | `_cmd_rag` が `ctx.rag.run()` をドライランで使用する |

---

