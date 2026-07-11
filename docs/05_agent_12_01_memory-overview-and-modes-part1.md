---
title: "Memory Layer - Overview and Modes (Part 1)"
category: agent
tags:
  - agent
  - memory
  - overview
  - memory-modes
  - production-checklist
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_01_memory-overview-and-modes-part1.md
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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes-part2.md`

## Keywords

persistent semantic memory
production checklist
purpose
memory modes
