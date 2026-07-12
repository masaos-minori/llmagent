---
title: "Memory Layer - Module Reference: Ops and Scoring"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - write-ops
  - scoring
  - rrf
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

### 14. `mapper.py` — 行変換ユーティリティ

| Function | Returns | Description |
|---|---|---|
| `row_to_entry(dict)` | `MemoryEntry` | SQLite の行を MemoryEntry に変換する |

float から BLOB への変換、タイムスタンプ付与、ISO 8601 タイムスタンプ生成のための内部ヘルパー関数。

### 15. `write_ops.py` — 書き込み操作

| Function | Returns | Description |
|---|---|---|
| `add(entry, embedding=None, embed_dim=None)` | `None` | 挿入＋FTS 同期。原子性のために BEGIN IMMEDIATE を使用する。`embedding` が提供された場合、memories_vec にも書き込む。 |
| `upsert(entry, embedding=None, embed_dim=None)` | `None` | 挿入または置換＋FTS 同期。`embedding` が提供された場合、memories_vec にも upsert する。 |
| `delete(memory_id)` | `bool` | ID によるエントリの削除 |
| `clear_by_session(session_id)` | `int` | 1セッション分の一括削除 |

### 16. `pin_ops.py` — pin/unpin 操作

| Function | Returns | Description |
|---|---|---|
| `pin(memory_id, conn=None)` | `bool` | pinned=1 を設定する。見つかった場合は True を返す。`conn` が提供された場合、その接続を使用する（呼び出し元がコミットする必要がある）。 |
| `unpin(memory_id, conn=None)` | `bool` | pinned=0 を設定する。見つかった場合は True を返す。`conn` が提供された場合、その接続を使用する（呼び出し元がコミットする必要がある）。 |

### 17. `count_ops.py` — 診断用カウント

| Function | Returns | Description |
|---|---|---|
| `count_entries()` | `int` | memories テーブルの行数（診断用） |
| `count_by_type()` | `dict[str, int]` | 全行に対する {memory_type: count}（診断用） |
| `count_by_source_type()` | `dict[str, int]` | 全行に対する {source_type: count}（診断用） |
| `count_vec()` | `int` | memories_vec の行数（利用不可の場合は OperationalError を発生させる） |
| `count_prunable(days)` | `int` | `days` 日より古いエントリの件数 |

### 18. `rebuild_ops.py` — 再構築操作

| Function | Returns | Description |
|---|---|---|
| `rebuild_fts()` | `int` | memories テーブルから FTS5 インデックスを再構築する。挿入された行数を返す |
| `rebuild_vec()` | `int` | memories テーブルから vec インデックスを再構築する。挿入された行数を返す |

### 19. `import_ops.py` — インポート操作

| Function | Returns | Description |
|---|---|---|
| `import_from_jsonl(jsonl_store, *, dry_run=False, embed_dim=None)` | `tuple[int, int]` | JSONL アーカイブから SQLite にエントリをインポートする。(jsonl_count, inserted_count) を返す。`dry_run=True` の場合、挿入せずに件数のみを返す。削除および pin/unpin の状態変更は再生しない。 |

### 20. `scoring.py` — ブーストを伴う BM25 スコアリング

**定数:**
- `_PIN_BOOST = 0.3` — pin されたエントリへの pin ブースト
- `_IMPORTANCE_BOOST_SCALE = 0.5` — importance のスケール係数（importance × 0.5）
- `_RECENCY_MAX_BOOST = 0.2` — 7日以内のエントリに対する recency ブーストの最大値
- `_CONTEXT_MATCH_BOOST = 0.1` — project/repo が一致した場合の基本のコンテキスト一致ブースト
- `_RECENCY_DAYS = 7.0` — recency のウィンドウ（日数）

| Function / Constant | Returns | Description |
|---|---|---|
| `score(bm25_rank, entry, project, repo[, recency_days, branch])` | `float` | 合成スコア: `-bm25_rank + importance_boost + pin_boost + recency_decay + context_match`。数式: `score = -bm25_rank + (importance_w × importance × 0.5) + (0.3 if pinned else 0) + (recency_w × recency_boost(created_at)) + context_boost(entry, project, repo, branch)` |
| `recency_boost(created_at[, recency_days])` | `float` | エントリの経過時間に反比例するブースト: `_RECENCY_MAX_BOOST × (1 - age_days / recency_days)`。経過日数が recency_days 以上の場合は 0.0 を返す |
| `context_boost(entry, project, repo[, branch])` | `float` | ブランチ一致: 0.15。project/repo 一致: 0.1。不一致: 0.0 |

### 21. `rrf.py` — Reciprocal Rank Fusion によるマージ

| Constant / Function | Returns | Description |
|---|---|---|
| `RRF_K` | `60` | Reciprocal rank fusion の定数 |
| `rrf_merge(hit_lists, k=60)` | `list[MemoryHit]` | RRF スコアリングを用いて複数のランク付き hit リストをランク位置ごとにマージする（各リストは 1.0 / (k + rank + 1) を寄与する） |

### 22. `fts_query.py` — FTS5 クエリビルダー

| Function / Constant | Returns | Description |
|---|---|---|
| `build_fts_query(text: str)` | `str` | トークンのクォート処理を伴う FTS5 MATCH クエリを構築する |

### 23. `sql_constants.py` — SQL 定数

内部ヘルパーモジュール。公開 API なし。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`

## Keywords

mapper.py
write_ops.py
pin_ops.py
count_ops.py
rebuild_ops.py
import_ops.py
scoring.py
rrf.py
fts_query.py
sql_constants.py
