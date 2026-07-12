---
title: "Memory Layer - Module Reference: Retrieval and Injection"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - retriever
  - injection
  - ingestion
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 7. `retriever.py` — 検索（FTS5 + KNN + ハイブリッド）

| Class | Role |
|---|---|
| `FtsRetriever` | importance / pin / recency による再スコアリングを伴う FTS5 BM25 検索 |
| `VectorRetriever` | sqlite-vec による KNN 検索 |
| `HybridRetriever` | 主要な外部インターフェース。両方を RRF マージで組み合わせる |

**`HybridRetriever` の属性とメソッド:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, embedding: list[float] | None = None, project="", repo="", branch="")` | `list[MemoryHit]` | 埋め込みがない場合は FTS のみ、埋め込みがある場合は RRF マージ。（生の文字列ではなく）`MemoryQuery` オブジェクトを受け取る。クエリテキストは内部で `query.query` から抽出される。戻り値に応じて `last_retrieval_mode` を設定する。 |
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | VectorRetriever に委譲する（ingestion の重複排除で使用） |
| `top_semantic(limit=5, min_importance=0.0, project="", repo="", branch="")` | `list[MemoryEntry]` | 直接 SQL を使用する。FTS は不要 |
| `embed_client` | `EmbeddingClient \| None` | 構築時に注入される。`/memory status` で使用される |
| `last_retrieval_mode` | `str` | `"hybrid"` / `"fts_only"` / `"unknown"` — `search()` の呼び出しごとに設定される |
| `fts_fallback_count` | `int` | ハイブリッド検索中の FTS フォールバックの回数 |

**`FtsRetriever` のメソッドと属性:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, project="", repo="", branch="")` | `list[MemoryHit]` | 再スコアリングを伴う FTS5 BM25 検索。エラー時または空のクエリの場合は [] を返す。 |
| `candidate_limit` | `int` | FTS クエリからの候補結果の最大数 |

**`VectorRetriever` のメソッド:**

| Method | Returns | Description |
|---|---|---|
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | KNN 検索。score はコサイン類似度（値が高いほど良い）。埋め込みが無効な場合は [] を返す。 |

**スコアリングの数式:**
```
score = -bm25_rank + importance_boost + pin_boost + recency_decay + context_match
```
- セマンティック: importance_weight=1.0, recency_weight=0.5
- エピソディック: importance_weight=0.5, recency_weight=1.0

**失敗モード:**
- `sqlite3.OperationalError` — vec テーブルが欠落している場合 → KNN は [] を返す
- `MemorySchemaError` — 無効な created_at タイムスタンプ

**ブランチ認識:**

すべての検索パスは、空でない branch が指定された場合にハード SQL ブランチフィルタを適用する。

```sql
AND (? = '' OR m.branch = '' OR m.branch = ?)
```

- ブランチは `factory.py` の `shared.git_helper.get_repo_info()` を介して起動時に一度だけ解決される。
- `branch=""`（グローバルメモリ）のエントリは、現在のブランチに関わらず常に含まれる。
- `get_repo_info()` が失敗する、または HEAD が detached の場合、branch はデフォルトで `""` になる。フィルタは適用されない（安全な劣化動作）。
- injection サービスは、解決済みの branch の値をすべての `retriever.search()` 呼び出しに渡す。
- ingestion における重複排除の KNN は、ブランチをまたいだ重複検出を保証するために `branch=""`（グローバルスコープ）を使用する。

### 8. `injection.py` — ライフサイクル注入サービス

クラス `MemoryInjectionService(policy, retriever, embed_client, project="", repo="", branch="", enabled=False)`:

| Method | Returns | Description |
|---|---|---|
| `on_session_start()` | `list[MemorySnippet]` | importance 順の上位セマンティックエントリ（同期） |
| `on_user_prompt(query, session_id)` | `list[MemorySnippet]` | 埋め込みを用いたセマンティック＋エピソディック検索（非同期） |

`InjectionPolicy(max_semantic=5, max_episodic=3, min_importance=0.5)` を使用する。

**失敗モード:** クエリが空の場合に `InjectionValidationError`。

| Attribute / Method | Type / Returns | Default | Description |
|---|---|---|---|
| `max_semantic` | `int` | `5` | 注入するセマンティックスニペットの最大数 |
| `max_episodic` | `int` | `3` | 注入するエピソディックスニペットの最大数 |
| `min_importance` | `float` | `0.5` | 検索対象とする importance の最小閾値 |
| `format_prefix_semantic` | `str` | `"[Semantic memory]"` | セマンティックスニペットのプレフィックス |
| `format_prefix_episodic` | `str` | `"[Episodic memory]"` | エピソディックスニペットのプレフィックス |

**失敗モード:** クエリが空の場合に `InjectionValidationError`。

### 9. `ingestion.py` — 抽出＋重複排除＋永続化

クラス `MemoryIngestionService(store, jsonl, retriever, embed_client=None, *, dedup_policy=None, project="", repo="", branch="", max_content_chars=500)`:

| Method / Attribute | Returns | Description |
|---|---|---|
| `on_session_stop(session_id, history, turn_id=None)` | `None` | 会話履歴からの抽出、重複排除、永続化 |
| `write_semantic(session_id, content)` | `None` | 手動での永続化（重複排除なし） |
| `write_episodic(session_id, content)` | `None` | 手動での永続化（重複排除なし） |
| `stat_embed_skip` | `int` | エラーによりスキップされた埋め込みのカウンタ |

重複排除: KNN による準重複検出を伴う `DedupPolicy(action=SKIP_NEW, threshold=...)` を使用する。

**失敗モード:** memory_links への挿入時の `sqlite3.OperationalError`（警告として握り潰される）。

**埋め込み失敗の追跡:** 書き込み操作が埋め込みなしでエントリを保存するたびに（埋め込みが失敗した場合）、`stat_embed_skip` カウンタが増加する。`on_session_stop()` のサマリーでログ出力される: `"MemoryIngestionService.on_session_stop: persisted %d entries; %d embed_skipped"`。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

retriever.py
injection.py
ingestion.py
