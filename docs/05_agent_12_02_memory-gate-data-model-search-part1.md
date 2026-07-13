---
title: "Memory Layer - Activation Gate, Data Model, and Search (Part 1)"
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
| `retriever.py` | レイヤー2が無効 | `HybridRetriever.search()` は `embedding=None` の場合 FTS5 のみで結果を返す（`last_retrieval_mode="fts_only"`、`fts_fallback_count` を加算） |
| `jsonl_store.py` | レイヤー1でバイパス | `write()` は呼び出されず、ファイルは変更されない |
| `store.py` | レイヤー1でバイパス | `upsert()` は呼び出されず、SQLite インデックスは変更されない |
| `extract.py` | レイヤー1でバイパス | `extract_memories()` は呼び出されない |
| `mapper.py` | 該当なし（純粋なユーティリティ） | 常に利用可能 |
| `models.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `types.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `enums.py` | 該当なし（純粋なデータ） | 常に利用可能 |
| `exceptions.py` | 該当なし（純粋なデータ） | 常に利用可能 |

### 境界条件: `knn_search()` の空リスト判定と例外の違い

`HybridRetriever.search()` は、呼び出し時点で `embedding=None`（埋め込み無効・未取得）の
場合、または `VectorRetriever.knn_search()` が空リストを返した場合（KNN 結果 0 件）に
FTS のみへフォールバックする。一方、`VectorRetriever.knn_search()` 自体は
`memories_vec` テーブルが存在しない場合に `sqlite3.OperationalError` を送出する
（docstring 明記）。`HybridRetriever.search()` はこの例外を捕捉していないため、
テーブル未初期化状態で埋め込みが有効な場合は例外が呼び出し元まで伝播する。

根拠分類: Explicit in code（`retriever.py` `VectorRetriever.knn_search` docstring
「raises OperationalError when table missing」、`HybridRetriever.search()` に
`knn_search` 呼び出しへの try/except なし）。

### 実装上の補足: DedupPolicy と保持期間

`enums.py` は重複排除・保持関連の定数も定義する。

| 定数 | 内容 |
|---|---|
| `DedupPolicy` | `action: DedupAction = SKIP_NEW`, `threshold: float = 0.3`（`ingestion.py` のデフォルト重複排除ポリシー） |
| `DEDUP_THRESHOLDS` | source_type 別の重複判定しきい値: RULE=0.98, DECISION=0.98, FAILURE=0.90, CONVERSATION=0.85 |
| `RETENTION_DAYS` | source_type 別の保持日数: RULE=None（無期限）, DECISION=None（無期限）, FAILURE=180, CONVERSATION=90 |

`DEDUP_THRESHOLDS` は `ingestion.py` の `_get_dedup_threshold()` が
`entry.source_type` に応じて参照する。`RETENTION_DAYS` は `enums.py` に定義されているが、
本ドキュメント担当範囲のモジュール（`store.py` / `retriever.py` / `services.py` /
`ingestion.py`）内でこの値を参照する保持削除処理は確認できなかった
（`rebuild_ops.py` 等の未読モジュールで使用されている可能性がある）。

根拠分類: Explicit in code（`enums.py` の定数定義、`ingestion.py`
`_get_dedup_threshold`）／`RETENTION_DAYS` の利用箇所は Needs confirmation。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_02_memory-gate-data-model-search-part2.md`

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
