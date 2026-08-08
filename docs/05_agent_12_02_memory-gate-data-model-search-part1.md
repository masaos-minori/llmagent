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

# Memory Layer — Activation Gate, Data Model, and Search (Part 1)

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

メモリ操作の実行タイミングを制御する3層のアクティベーションゲートと、各モジュールが無効化時にどのように振る舞うかを定義する。

## Design Intent

メモリ層は3つの独立したゲートで制御している。config フラグによる完全バイパス、埋め込みクライアントの有効化によるフェーズドフォールバック、およびファサード経由の単一エントリポイント。これはメモリレイヤーが optional であることを実装的に保証するため。

## Responsibility Boundary

- メモリレイヤーが所有するもの: メモリ操作のライフサイクル（セッション開始時注入、ユーザープロンプト応答、セッション終了時抽出）
- メモリレイヤーが所有しないもの: LLM コンテキスト生成、ツール実行、RAG ドキュメント検索

## Key Constraints

- `use_memory_layer = false` を設定すると、メモリサービスは構築されずすべてのメモリ操作が完全にバイパスされる
- 埋め込みエンドポイントが利用不可能な場合、`HybridRetriever.search()` は FTS5 のみにフォールバックする
- `VectorRetriever.knn_search()` は `memories_vec` テーブルが存在しない場合に `OperationalError` を送出する（テーブル未初期化状態で埋め込みが有効な場合は例外が伝播する）

## Operational Notes

- `/memory status` で現在のモードを確認できる
- 埋め込みが利用できない場合、システムは FTS のみにフォールバックする（手動操作不要）
- `DEDUP_THRESHOLDS` は source_type 別の重複判定しきい値として `ingestion.py` で実際に消費されている
- `RETENTION_DAYS` は定義されているが現在到達不能（死コード）。詳細は NC-007 を参照

## Known Limitations

- `RETENTION_DAYS` の保持期間に基づくエクスプライズフィルタは現在到達不能（NC-007）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_02_memory-gate-data-model-search-part2.md`
