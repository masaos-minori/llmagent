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

## 7. `retriever.py` — 検索（FTS5 + KNN + ハイブリッド）

| Class | Role |
|---|---|
| `FtsRetriever` | importance / pin / recency による再スコアリングを伴う FTS5 BM25 検索 |
| `VectorRetriever` | sqlite-vec による KNN 検索 |
| `HybridRetriever` | 主要な外部インターフェース。両方を RRF マージで組み合わせる |

**`HybridRetriever` の属性とメソッド:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, embedding: list[float] &#124; None = None, project="", repo="", branch="")` | `list[MemoryHit]` | 埋め込みがない場合は FTS のみ、埋め込みがある場合は RRF マージ。（生の文字列ではなく）`MemoryQuery` オブジェクトを受け取る。クエリテキストは内部で `query.query` から抽出される。戻り値に応じて `last_retrieval_mode` を設定する。 |
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | VectorRetriever に委譲する（ingestion の重複排除で使用） |
| `top_semantic(limit=5, min_importance=0.0, project="", repo="", branch="")` | `list[MemoryEntry]` | 直接 SQL を使用する。FTS は不要 |
| `embed_client` | `EmbeddingClient \| None` | 構築時に注入される。`/memory status` で使用される |
| `last_retrieval_mode` | `str` | `"hybrid"` / `"fts_only"` / `"unknown"` — `search()` の呼び出しごとに設定される |
| `fts_fallback_count` | `int` | ハイブリッド検索中の FTS フォールバックの回数（呼び出しごとに加算されるカウンタで、リセットされない） |

**コンストラクタ引数（`__init__`、いずれもキーワード専用）:**

| Parameter | Default | Description |
|---|---|---|
| `fts_limit` | `50`（`_FTS_CANDIDATE_LIMIT`） | `FtsRetriever` に渡す候補上限。KNN 側の `limit` としても再利用される（`self._fts.candidate_limit`） |
| `rrf_k` | `60`（`rrf.py` の `RRF_K`） | RRF マージの `k` 定数。`rrf_merge(..., k=self._rrf_k)` に渡される |
| `recency_days` | `7.0` | `FtsRetriever` の recency スコアリング窓 |
| `embed_client` | `None` | 未指定時は `embed_client` 属性が `None` のまま。呼び出し側が embedding 取得可否を判定する材料になる |

根拠: Explicit in code（`retriever.py` `HybridRetriever.__init__`）。

**`FtsRetriever` のメソッドと属性:**

| Method / Attribute | Returns | Description |
|---|---|---|
| `search(query: MemoryQuery, project="", repo="", branch="")` | `list[MemoryHit]` | 再スコアリングを伴う FTS5 BM25 検索。エラー時または空のクエリの場合は [] を返す。 |
| `candidate_limit` | `int` | FTS クエリからの候補結果の最大数 |

**`VectorRetriever` のメソッド:**

| Method | Returns | Description |
|---|---|---|
| `knn_search(embedding, memory_type, limit, branch="")` | `list[MemoryHit]` | KNN 検索。`MemoryHit.score` には `mv.distance` を符号反転した値（`-distance`）を格納する（コード上のコメントは “Negate distance” であり、距離指標がコサインか L2 かは `memories_vec` テーブル定義依存で本モジュールからは確認できない＝Needs confirmation）。クエリ結果が0件の場合は [] を返す。 |

**スコアリングの数式:**
```
score = -bm25_rank + importance_boost + pin_boost + recency_decay + context_match
```
- セマンティック: importance_weight=1.0, recency_weight=0.5
- エピソディック: importance_weight=0.5, recency_weight=1.0
- 定数（`scoring.py`）: `pin_boost=0.3`、`importance_boost` は `importance(0–1) × importance_weight × 0.5`、`recency_decay` は経過日数に応じて 0.0–0.2（`recency_days` 経過で 0）、`context_match` は branch 一致で 0.15、project/repo 一致で 0.1
- この数式は FTS リトリーバーのヒットフェッチ関数が FTS5 候補（最大 `candidate_limit` 件）に対して呼ぶ再スコアリングであり、KNN 側の `score`（`-distance`）には適用されない。RRF マージ後の最終 `score` はいずれの数式でもなく RRF スコアで上書きされる。

根拠: Explicit in code（`scoring.py` の `score()` / `context_boost()` / `recency_boost()`）。

**失敗モード:**
- `sqlite3.OperationalError` — vec テーブルが欠落している場合。`VectorRetriever.knn_search()` の docstring は "raises OperationalError when table missing" と明記しており、`retriever.py` 内・`HybridRetriever.search()` 内のいずれにも try/except による捕捉はない。したがって vec テーブル欠落時は例外がそのまま呼び出し元（`injection.py` / `ingestion.py`）まで伝播する。**旧記述「KNN は [] を返す」は実装と矛盾しており、正しくは「例外が送出される」である（矛盾を修正済み）。**
- `MemorySchemaError` — 無効な created_at タイムスタンプ（`scoring.py` の `recency_boost()` が送出）

根拠: Explicit in code（`retriever.py` の `VectorRetriever.knn_search()` docstring と実装、`services.py`/`injection.py`/`ingestion.py` に捕捉なし）。

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

**`rrf.py` — RRF マージの実装詳細:**

- `rrf_merge(hit_lists, k=RRF_K)`（`RRF_K=60`）は各リストで `1.0 / (k + rank + 1)` を `memory_id` ごとに加算し、複数リストに同じ `memory_id` が出現した場合はスコアが合算される。
- 同じ `memory_id` が複数リストに出現した場合、返却される `MemoryHit` オブジェクト自体は最後に処理したリスト（`HybridRetriever.search()` の呼び出し順では KNN 側）のものが採用される。エントリ内容（`entry`）はどちらのリスト由来でも実質同一だが、`score` フィールドは呼び出し前の値に関わらず必ず RRF スコアで上書きされる。
- 戻り値は RRF スコア降順でソート済みの重複排除済みリスト。

根拠: Explicit in code（`rrf.py` `rrf_merge()`）。

**フラグメンテーションの制限事項（複数チャンクへの分割時の挙動）:**

抽出時にチャンク分割ステージ（`05_agent_12_03_memory-module-ref-core-and-store.md`「チャンク分割ステージ」参照）で複数チャンクに分割された長いソースメッセージは、それぞれ独立した `memories` テーブルの行として保存され、各チャンクは個別の `memory_id` を持つ（`extract.py` の分割詳細は `05_agent_12_05_memory-module-ref-extraction-and-facade.md` を参照）。

`retriever.py`／`rrf.py` は各行を独立に扱い、チャンクと元ソースを紐づける親子関係やグルーピングはスキーマ上存在しない。そのため、1件の長いソースイベントが N 個のチャンクに分割された場合、`search()`／`top_semantic()` の結果には最大 N 件の独立したヒットとして現れうる。これは `rrf_merge` の同一 `memory_id` に対する重複排除（前述）とは別の事象であり、異なる `memory_id` を持つチャンク間には適用されない。

これは現行のチャンク分割方式（1チャンク1行、紐づけなし）における既知の許容された制限であり、バグではない。実運用上問題になる場合は、将来的に `chunk_index`／`parent_id` のスキーマ対応と検索側でのグルーピングを追加することが考えられる。

### 8. `injection.py` — ライフサイクル注入サービス

クラス `MemoryInjectionService(policy, retriever, embed_client, project="", repo="", branch="")`:

**ドキュメント修正:** 従来の記述にあった `enabled=False` 引数は実装の `__init__` シグネチャに存在しない（`injection.py` の `MemoryInjectionService.__init__` を確認）。有効/無効の制御はこのクラスの外側（呼び出し元が `MemoryInjectionService` を生成するかどうか、または `embed_client` 自体の `enabled` フラグ）で行われる。根拠: Explicit in code。

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
