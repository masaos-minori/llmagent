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
  - 05_agent_12_01_memory-overview-and-modes.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
source:
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
---

# Memory Layer — Module Reference: Ops and Scoring

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Purpose

メモリレイヤーの書き込み操作、スコアリング、RRFマージ、FTS5クエリビルダーの責務範囲を定義する。

## Design Intent

メモリレイヤーは optional であるため、すべての公開 API は `ctx.services.memory is None` の場合に安全にガードできる設計になっている。コア型は不変の DTO として定義され、JSONL と SQLite の両方のストレージ層と互換性がある。

## Responsibility Boundary

- メモリレイヤーが所有するもの: メモリエントリの永続化、検索、注入
- メモリレイヤーが所有しないもの: LLM コンテキスト生成、ツール実行、RAG ドキュメント検索

## Key Constraints

- `use_memory_layer = false` を設定すると、メモリサービスは構築されずすべてのメモリ操作が完全にバイパスされる
- `VectorRetriever.knn_search()` は `memories_vec` テーブルが存在しない場合に `OperationalError` を送出する（テーブル未初期化状態で埋め込みが有効な場合は例外が伝播する）
- `EmbeddingClient.enabled=False` の場合、`fetch()` は HTTP 呼び出しを行わずに即座に `EmbeddingResult(success=False, error_kind=DISABLED)` を返す
- 埋め込み取得が失敗した場合も処理は継続し、埋め込みなしでエントリを保存する（`stat_embed_skip` カウンタが増加）
- `JsonlMemoryStore` は追記専用アーカイブ。削除および pin/unpin の状態変更は再生されない
- 自動抽出（`on_session_stop`）は `DedupAction.SKIP_NEW` による重複排除を適用するが、手動書き込みは意図的にこの重複排除をバイパスする
- 埋め込み取得後、KNN 近傍5件を検索し、source_type ごとの閾値より距離が近い既存エントリがあれば新規エントリを破棄する（SKIP_NEW）
- 埋め込み取得が失敗した場合、埋め込みなしで SQLite/JSONL への保存を継続する（フェイルオープン）
- JSONL への書き込みが `OSError` で失敗した場合、警告ログを出して処理を継続する（SQLite が正本であるため致命的エラーとしない）
- `memory_links` への挿入が `sqlite3.OperationalError`/`IntegrityError` で失敗した場合も警告ログのみで処理を継続する

## Operational Notes

- `/memory status` で現在のモードを確認できる（Disabled / FTS-only / Degraded / Hybrid）
- `get_stats()` は以下のキーを持つ: total, semantic, episodic, by_source, embed_skip, last_retrieval_mode, fts_fallback_count
- 埋め込み取得が失敗した場合、`stat_embed_skip` カウンタが増加し、`on_session_stop()` のサマリーでログ出力される
- `import_from_jsonl()` は JSONL アーカイブから SQLite にエントリをインポートする。削除および pin/unpin の状態変更は再生されない
- FTS5 インデックスの再構築には `rebuild_fts()` を使用し、vec インデックスの再構築には `rebuild_vec()` を使用する

## Known Limitations

- 1件のソースメッセージが複数チャンクに分割された場合、検索時にはそれぞれが独立したヒットとして現れる（フラグメンテーション）
- `RETENTION_DAYS` の保持期間に基づくエクスプライズフィルタは現在到達不能（NC-007）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_12_01_memory-overview-and-modes.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
