---
title: "Memory Layer - Activation Gate, Data Model, and Search (Part 2)"
category: agent
tags:
  - agent
  - memory
  - activation-gate
  - data-model
  - search-strategies
  - disabled-behavior
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## データモデル

### MemoryEntry（JSONL + SQLite に保存）

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | UUID v4、主キー |
| `memory_type` | `MemoryType` | `"semantic"` \| `"episodic"` |
| `source_type` | `SourceType` | `"rule"` \| `"conversation"` \| `"decision"` \| `"failure"`（`StrEnum` の実値は小文字。本表は従来カテゴリ名として大文字で提示していたが、実装値は小文字である点に注意 — 根拠分類: Explicit in code, `agent/memory/types.py`） |
| `session_id` | `int \| None` | 親セッションの ID |
| `turn_id` | `str \| None` | 発生元の会話ターンにリンクする UUID |
| `project` | `str` | コンテキストフィルタリング用のプロジェクト名 |
| `repo` | `str` | コンテキストフィルタリング用のリポジトリ名 |
| `branch` | `str` | コンテキストフィルタリング用の Git ブランチ |

> **現在の動作:** 空でない branch が指定された場合、検索は以下のみを含む
> ハード SQL フィルタを適用する。
> - `branch = ''` のメモリ（グローバルメモリ、常に含まれる）
> - `branch = <現在のブランチ>` のメモリ
>
> 他のブランチのメモリは完全に除外される（ランクが下がるだけではない）。
| `content` | `str` | メッセージの全文 |
| `summary` | `str` | 内容の短い要約 |
| `tags` | `list[str]` | 分類用のキーワードタグ |
| `importance` | `float` | 0.0～1.0。高いほど検索優先度が高い（デフォルト: 0.5） |
| `pinned` | `bool` | `True` の場合、セッション開始ごとに注入される |
| `created_at` | `str` | ISO 8601 UTC タイムスタンプ。`write_ops.add()` によって設定される |
| `updated_at` | `str` | ISO 8601 UTC タイムスタンプ |

**DB マッピング:** `memories` テーブル（SQLite）に保存され、JSONL ファイルには1エントリにつき1行が書き込まれる。FTS5 インデックスは `memories_fts` にある。ベクトルインデックスは `memories_vec` にある（埋め込みが有効な場合）。

### MemorySnippet（LLM コンテキストに注入される）

| Field | Type | Description |
|---|---|---|
| `text` | `str` | メモリタイプのプレフィックスを付けた整形済み文字列（例: `"[Semantic memory] ..."`） |
| `source` | `str` | `"semantic"` \| `"episodic"` |
| `score` | `float` | 検索による関連度スコア（RRF マージのランクまたは FTS5 のランク） |

---

## JSONL 形式

JSONL ストアの各行は、すべての `MemoryEntry` フィールドをシリアライズした単一の JSON オブジェクトである。

```json
{"memory_id": "uuid-here", "memory_type": "semantic", "source_type": "rule", "session_id": 1, "turn_id": null, "project": "myproj", "repo": "myrepo", "branch": "main", "content": "Use orjson for JSON.", "summary": "orjson preference", "tags": [], "importance": 0.7, "pinned": false, "created_at": "2026-06-19T23:00:00Z", "updated_at": "2026-06-19T23:00:00Z"}
```

**特性:**
- 追記専用: ファイル内のエントリは変更・削除されない（`agent/memory/jsonl_store.py` のモジュール docstring: 「JSONL does NOT record mutations (delete, pin, unpin); SQLite is the authoritative source of truth」）
- 1行に1エントリ。UTF-8 エンコード。各行は有効な JSON
- ファイルパスは `memory_jsonl_dir` config によって制御される（ファイル名: `memories.jsonl`）
- 正本データ: 必要に応じて SQLite インデックスは JSONL から再構築される

> **実装補足（Explicit in code）:** `jsonl_store.py` の docstring は SQLite（`MemoryStore` 経由）こそが正本状態（authoritative source of truth）であると明記しており、JSONL は追記専用アーカイブという位置付けである。`read_all()` は監査・エクスポート・初回インポート用と限定されており、"authoritative state の再構築に使うな。`MemoryStore` を直接使うか SQLite バックアップから復元せよ" と明示されている。`import_ops.import_from_jsonl()` を用いた再構築は **`memories` / `memories_fts` / `memories_vec` の全行を削除してから JSONL の内容で再挿入する**破壊的操作であり、削除・pin/unpin 済みの状態変更は再生されない（それらの履歴は JSONL 側に存在しないため）。整合性の部分修復（FTS/vec のみのズレ解消）が目的なら `rebuild_ops.rebuild_fts()` / `rebuild_vec()` を使うこと。

---

## 検索戦略

### FTS5（全文検索）

- **エンジン:** BM25 ランキングを用いた SQLite FTS5
- **インデックス:** `memories_fts` 内のトークン化された `content` カラム
- **フォールバック:** `EmbeddingClient.enabled=False` または埋め込みが返らない場合に使用される
- **強み:** 正確なキーワード一致、API 依存なし、小規模データセットで高速
- **弱み:** セマンティックな理解がない

### KNN（ベクトル検索）

- **エンジン:** コサイン類似度を用いた sqlite-vec 拡張
- **インデックス:** `memories_vec` 内の密な埋め込みベクトル
- **要件:** 有効な埋め込み API エンドポイントとともに `EmbeddingClient.enabled=True`
- **強み:** セマンティックな類似度マッチング、言語非依存
- **弱み:** 埋め込み API 呼び出しが必要、sqlite-vec 拡張のロードが必要

### ハイブリッド（RRF マージ）

- **エンジン:** Reciprocal Rank Fusion（RRF）を用いて FTS5 と KNN の結果を統合する
- **数式:** `rrf_score = 1.0 / (k + rank + 1)`。ここで `k=60`、`rank` は0始まり
- **結果:** 重複排除され、RRF スコアの降順でソートされる
- **強み:** クエリの種類を問わず両方の利点を得られる
- **弱み:** レイテンシが高い（2回の検索＋マージ）。埋め込み API が必要

---

## 無効化時の動作

モジュール別の詳細な内訳は、上記の[アクティベーションゲート](#アクティベーションゲート)のセクションと[モジュール別の無効化時の動作](#モジュール別の無効化時の動作)の表を参照。

概要:
- `use_memory_layer=False` → `ctx.services.memory` が `None` になり、すべてのメモリ操作がスキップされる
- `EmbeddingClient.enabled=False` → `fetch()` が `DISABLED` エラーを返し、検索は FTS5 のみにフォールバックする
- `cli_view.py` は起動時のバナーにメモリ層のステータスを反映する

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`

## Keywords

activation gate
disabled behavior by module
MemoryEntry
MemorySnippet
JSONL format
FTS5
KNN
hybrid RRF
disabled behavior
