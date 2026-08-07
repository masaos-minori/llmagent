---
title: "Memory Layer - Module Reference: Core and Store"
category: agent
tags:
  - agent
  - memory
  - module-reference
  - types
  - store
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_01_memory-overview-and-modes-part1.md
  - 05_agent_12_02_memory-gate-data-model-search-part1.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_03_memory-module-ref-core-and-store.md
---

# Memory Layer — Module Reference: Core and Store

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

メモリレイヤーのコア型、データモデル、永続化ストアの責務範囲を定義する。

## Design Intent

メモリレイヤーは optional であるため、すべての公開 API は `ctx.services.memory is None` の場合に安全にガードできる設計になっている。コア型は不変の DTO として定義され、JSONL と SQLite の両方のストレージ層と互換性がある。

## Responsibility Boundary

- メモリレイヤーが所有するもの: メモリエントリの永続化、検索、注入
- メモリレイヤーが所有しないもの: LLM コンテキスト生成、ツール実行、RAG ドキュメント検索

## Key Constraints

- `use_memory_layer = false` を設定すると、メモリサービスは構築されずすべてのメモリ操作が完全にバイパスされる
- `VectorRetriever.knn_search()` は `memories_vec` テーブルが存在しない場合に `OperationalError` を送出する（テーブル未初期化状態で埋め込みが有効な場合は例外が伝播する）
- `MemoryStore.list_entries()` の branch フィルタ挙動: `branch = '' OR branch = ?` であり、branch が空文字列のエントリは指定した branch 値に関わらず常にマッチする
- `embed_dim` は `MemoryStore` 自体にはなく、呼び出し元 `agent/factory.py` が `AgentConfig.memory.memory_embed_dim`（既定値 384）として渡す

## Operational Notes

- 書き込み操作は `write_ops.py` にあり、読み取り操作は `store.py` にある
- チャンク分割ステージは `memory_max_content_chars`（既定値 500）を超えるコンテンツに対して発生する。これはチャンク単位の上限であり、総コンテンツ量に対する上限ではない
- 1件のソースメッセージが複数チャンクに分割された場合、検索時にはそれぞれが独立したヒットとして現れる（フラグメンテーションの制限事項）
- `RETENTION_DAYS` は定義されているが現在到達不能（死コード）。詳細は NC-007 を参照

## Known Limitations

- `RETENTION_DAYS` の保持期間に基づくエクスプライズフィルタは現在到達不能（NC-007）
- 1件のソースメッセージが複数チャンクに分割された場合、検索時にはそれぞれが独立したヒットとして現れる（フラグメンテーション）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
