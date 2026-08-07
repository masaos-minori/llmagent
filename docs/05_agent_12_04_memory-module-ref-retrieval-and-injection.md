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
source:
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
---

# Memory Layer — Module Reference: Retrieval and Injection

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

メモリレイヤーの検索（FTS5 + KNN + ハイブリッド）、ライフサイクル注入、および抽出＋重複排除＋永続化の責務範囲を定義する。

## Design Intent

メモリレイヤーは optional であるため、すべての公開 API は `ctx.services.memory is None` の場合に安全にガードできる設計になっている。コア型は不変の DTO として定義され、JSONL と SQLite の両方のストレージ層と互換性がある。

## Responsibility Boundary

- メモリレイヤーが所有するもの: メモリエントリの永続化、検索、注入
- メモリレイヤーが所有しないもの: LLM コンテキスト生成、ツール実行、RAG ドキュメント検索

## Key Constraints

- `use_memory_layer = false` を設定すると、メモリサービスは構築されずすべてのメモリ操作が完全にバイパスされる
- `VectorRetriever.knn_search()` は `memories_vec` テーブルが存在しない場合に `OperationalError` を送出する（テーブル未初期化状態で埋め込みが有効な場合は例外が伝播する）
- `HybridRetriever.search()` は埋め込みがない場合は FTS のみ、埋め込みがある場合は RRF マージを行う
- `InjectionPolicy` のデフォルト: `max_semantic=5`, `max_episodic=3`, `min_importance=0.5`, `max_snippet_length=500`
- 埋め込み取得が失敗した場合も処理は継続し、埋め込みなしでエントリを保存する（`stat_embed_skip` カウンタが増加）
- 自動抽出（`on_session_stop`）は `DedupAction.SKIP_NEW` による重複排除を適用するが、手動書き込みは意図的にこの重複排除をバイパスする

## Operational Notes

- ブランチ認識: 空でない branch が指定された場合にハード SQL ブランチフィルタを適用する（`AND (? = '' OR m.branch = '' OR m.branch = ?)`）
- `branch=""`（グローバルメモリ）のエントリは、現在のブランチに関わらず常に含まれる
- `get_repo_info()` が失敗する、または HEAD が detached の場合、branch はデフォルトで `""` になる（安全な劣化動作）
- ingestion における重複排除の KNN は、ブランチをまたいだ重複検出を保証するために `branch=""`（グローバルスコープ）を使用する
- スニペットには PII フィルタリングと長さ制限が適用される（`snippet_filter.py` 連携）
- 1件のソースメッセージが複数チャンクに分割された場合、検索時にはそれぞれが独立したヒットとして現れる（フラグメンテーションの制限事項）

## Known Limitations

- 1件のソースメッセージが複数チャンクに分割された場合、検索時にはそれぞれが独立したヒットとして現れる（フラグメンテーション）
- `RETENTION_DAYS` の保持期間に基づくエクスプライズフィルタは現在到達不能（NC-007）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes-part1.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
