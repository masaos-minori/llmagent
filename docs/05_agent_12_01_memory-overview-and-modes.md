---
title: "Memory Layer - Overview and Modes"
category: agent
tags:
  - agent
  - memory
  - overview
  - memory-modes
  - production-checklist
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_02_memory-gate-data-model-search.md
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

## 永続的セマンティックメモリ — 概要

永続的セマンティックメモリは、エージェントのセッションをまたいで抽象的なルール、設計上の決定、失敗パターン、
および会話の Q&A を保存する。

**メモリの種類**:
- セマンティック: 長期にわたるルールと決定（セッション開始時の注入には importance ≥ 0.5 が必要）
- エピソディック: セッション固有の失敗と Q&A（最初のユーザープロンプトで注入される）

**ソースの種類**: RULE / DECISION / FAILURE / CONVERSATION

**ローカル限定保証**: `memory_local_only = true` を設定すると、埋め込み
エンドポイントがループバックアドレスであることを強制する。`embed_url` がローカルでない場合は起動が失敗する。

**自動的なコンテキスト復元**:
- セッション開始時: pinned および重要度が高いセマンティックメモリが注入される
- 最初のユーザープロンプト時: タスク固有のハイブリッド検索（セマンティック＋エピソディック）

## 本番運用チェックリスト

- [ ] データがマシン外に出てはならない場合は `memory_local_only = true`
- [ ] `embed_url` がローカルの埋め込みサービスを指している（例: `http://localhost:11434`）
- [ ] `/memory status` が `Hybrid mode`、`FTS-only`、`Degraded mode`、`disabled` のいずれかを表示する
- [ ] JSONL バックアップの復元後に `/memory rebuild` をテスト済み

---

## 目的

`scripts/agent/memory/` 配下のすべてのモジュールの API リファレンス。開発者は
ソースコードを読まずに各モジュールの責務、公開 API の範囲、および無効化時の動作を
理解できるようにする。

---

## 概要

| Module | Responsibility |
|---|---|
| `__init__.py` | 公開 API のバレル — すべての公開シンボルを再エクスポートする |
| `types.py` | コアランタイム型（MemoryEntry、MemoryQuery、MemoryHit、EmbeddingResult） |
| `enums.py` | ドメイン enum（MemoryType、DedupAction、RetrievalMode、ExtractionDecision） |
| `exceptions.py` | 例外階層 |
| `models.py` | 不変の DTO（HistoryMessage、JsonlRecord、MemorySnippet、ConsistencyReport） |
| `store.py` | memories / memories_fts / memories_vec テーブルの CRUD |
| `retriever.py` | FTS5 / KNN / ハイブリッド検索（FtsRetriever、VectorRetriever、HybridRetriever） |
| `injection.py` | MemoryInjectionService — スニペット注入のライフサイクルフック |
| `ingestion.py` | MemoryIngestionService — 抽出、重複排除、永続化 |
| `extract.py` | 会話履歴からのルールベース抽出 |
| `jsonl_store.py` | 追記専用の JSONL アーカイブ |
| `embedding_client.py` | リトライとサーキットブレーカーを備えた HTTP 埋め込みクライアント |
| `services.py` | injection、ingestion、store、retriever に対するファサードである MemoryServices |
| `mapper.py` | SQLite 行の変換、埋め込み blob のシリアライズ |

---

## メモリモード

メモリ層は4つの異なるモードで動作し、`/memory status` で確認できる。

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | 完全動作 — 埋め込みエンドポイントが利用可能で正常な状態 | ベクトル類似度と FTS 結果の RRF マージによるハイブリッド検索 |
| `Memory enabled, embedding disabled (FTS-only)` | 埋め込みエンドポイントは利用不可だが circuit は closed | FTS のみの検索。ベクトル類似度の要素はない |
| `Degraded mode (circuit open, FTS fallback)` | 繰り返しの失敗により埋め込みのサーキットブレーカーが作動した状態 | FTS のみの検索。上記と同じだが、埋め込みサービスに現在進行中の問題があることを示す |
| `Memory layer disabled` | メモリサブシステムが完全に無効化されている（`use_memory_layer = false`） | メモリ検索は一切行われない |

**各モードが適用される条件:**

- **Hybrid mode**: メモリが有効で、埋め込みエンドポイントに到達可能かつ有効な埋め込みを返している場合のデフォルト。
- **FTS-only**: 埋め込みエンドポイントが失敗した場合（ネットワークエラー、タイムアウト、無効な応答）、システムは FTS のみにフォールバックする。これは手動操作なしに自動的に発生する。
- **Degraded mode**: 継続的な失敗により埋め込みのサーキットブレーカーが開いた場合。サーキットブレーカーの閾値は `embedding_client.py` で設定可能。Degraded mode は上記と同じ FTS フォールバックを使用するが、埋め込みサービスに継続中の問題があることを示す。
- **Disabled**: `config/agent.toml` で `use_memory_layer = false` の場合。埋め込みの可用性に関わらずメモリ検索は行われない。

**モード間の遷移:**

- Hybrid → FTS-only: 埋め込み失敗時に自動的に遷移する
- FTS-only → Hybrid: 埋め込みが復旧した際に自動的に遷移する
- Degraded → Hybrid: 復旧期間後にサーキットブレーカーが閉じた際に自動的に遷移する
- いずれか → Disabled: 設定変更とエージェントの再起動が必要

```
session_start
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_start()
|                 |---> injection.on_session_start()
+--------+--------+
         |
         v
+-----------------+     +------------------+
| injection.py    |---->| retriever.py     |
| MemoryInject    |     | HybridRetriever  |
| Service         |     | top_semantic()   |
+--------+--------+     +------------------+
         |
         v
+-----------------+
| models.py       |  MemorySnippet[] -> injected into LLM context
| MemorySnippet   |
+-----------------+

user_prompt (during session)
    |
    v
+-----------------+     +-----------------+     +---------------------+
| services.py     |---->| injection.py    |---->| embedding_client.py |
| on_user_prompt  |     | on_user_prompt  |     | EmbeddingClient     |
+-----------------+     +--------+--------+     +---------------------+
                                 |
                                 v
                         +------------------+
                         | retriever.py     |
                         | HybridRetriever  |
                         | search() (RRF)   |
                         +--------+---------+
                                  |
                                  v
                         +-----------------+
                         | models.py       |
                         | MemorySnippet[] |
                         +-----------------+

session_stop
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_stop()
|                 |---> ingestion.on_session_stop()
+--------+--------+
         |
         v
+-----------------+     +------------------+     +-----------------------------+
| ingestion.py    |---->| extract.py       |---->| For each MemoryEntry:       |
| MemoryIngestion |     | extract_memories |     | 1. EmbeddingClient.fetch()  |
| Service         |     +------------------+     | 2. Dedup check (KNN)        |
+--------+--------+                              | 3. JsonlMemoryStore.write() |
         |                                       | 4. write_ops.upsert()       |
         v                                       +-----------------------------+
+-----------------+
| jsonl_store.py  |  Append-only archive
| JsonlMemoryStore|
+--------+--------+
         |
         v
+-----------------+     +------------------+
| store.py        |---->| retriever.py     |
| MemoryStore     |     | .fts_search()    |
| (SQLite index)  |     | .knn_search()    |
+-----------------+     +------------------+
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

persistent semantic memory
production checklist
purpose
memory modes
