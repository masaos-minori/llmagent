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
