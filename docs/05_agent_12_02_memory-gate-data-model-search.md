---
title: "Memory Layer - Activation Gate, Data Model, and Search"
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
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## アクティベーションゲート

メモリ層には、メモリ操作の実行タイミングを制御する3層のアクティベーションゲートがある。

**レイヤー1: config によるバイパス**
- `use_memory_layer` config フラグ（デフォルト: `False`）
- `False` の場合、メモリサービスは構築されず、`ctx.services.memory` は `None` になる
- すべての呼び出し元は `if ctx.services.memory is None: return` でガードする
- injection、ingestion、retrieval を完全にバイパスする

**レイヤー2: 埋め込みクライアントの有効化**
- 埋め込みクライアントの有効化フラグが HTTP と埋め込み呼び出しをゲートする
- `False` の場合: `fetch()` は即座に `EmbeddingResult(success=False, error_kind=DISABLED)` を返す
- 埋め込みが利用できない場合、`HybridRetriever.search()` は FTS5 のみにフォールバックする

**レイヤー3: サービスファサードの呼び出し**
- `MemoryServices` が単一のエントリポイントである（`on_session_start`、`on_user_prompt`、`on_session_stop`）
- すべてのメモリ操作はこのファサードを経由する。サブサービスへの直接アクセスはテスト専用である

### モジュール別の無効化時の動作

| Module | Disabled condition | Behavior |
|---|---|---|
| `services.py` | `use_memory_layer=False`（レイヤー1） | `ctx.services.memory` が `None` になる。呼び出し元はスキップする |
| `injection.py` | レイヤー1でバイパス | `MemoryInjectionService` は構築されず、スニペットは注入されない |
| `ingestion.py` | レイヤー1でバイパス | `MemoryIngestionService` は構築されず、エントリは書き込まれない |
| `embedding_client.py` | `enabled=False`（レイヤー2） | `fetch()` は HTTP 呼び出しを行わずに `EmbeddingResult(error_kind=DISABLED)` を返す |
| `retriever.py` | レイヤー2が無効 | `HybridRetriever.search()` は FTS5 のみを使用する。`knn_search()` は `[]` を返す |
| `jsonl_store.py` | レイヤー1でバイパス | `write()` は呼び出されず、ファイルは変更されない |
| `store.py` | レイヤー1でバイパス | `upsert()` は呼び出されず、SQLite インデックスは変更されない |
| `extract.py` | レイヤー1でバイパス | `extract_memories()` は呼び出されない |
| `mapper.py` | 該当なし（純粋なユーティリティ） | 常に利用可能 |
| `models.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `types.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `enums.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `exceptions.py` | 該当なし（純粋なデータ） | 常に利用可能 |

---

## データモデル

### MemoryEntry（JSONL + SQLite に保存）

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | UUID v4、主キー |
| `memory_type` | `MemoryType` | `"semantic"` \| `"episodic"` |
| `source_type` | `SourceType` | `"RULE"` \| `"CONVERSATION"` \| `"DECISION"` \| `"FAILURE"` |
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
{"memory_id": "uuid-here", "memory_type": "semantic", "source_type": "RULE", "session_id": 1, "turn_id": null, "project": "myproj", "repo": "myrepo", "branch": "main", "content": "Use orjson for JSON.", "summary": "orjson preference", "tags": [], "importance": 0.7, "pinned": false, "created_at": "2026-06-19T23:00:00Z", "updated_at": "2026-06-19T23:00:00Z"}
```

**特性:**
- 追記専用: ファイル内のエントリは変更・削除されない
- 1行に1エントリ。UTF-8 エンコード。各行は有効な JSON
- ファイルパスは `memory_jsonl_dir` config によって制御される（ファイル名: `memories.jsonl`）
- 正本データ: 必要に応じて SQLite インデックスは JSONL から再構築される

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
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

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
