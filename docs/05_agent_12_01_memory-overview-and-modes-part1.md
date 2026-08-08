---
title: "Memory Layer - Overview and Modes (Part 1)"
category: agent
tags:
  - agent
  - memory
  - overview
  - memory-modes
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

# Memory Layer — Overview and Modes (Part 1)

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## 目的

`scripts/agent/memory/` 配下のモジュールの責務と公開 API の範囲を、ソースコードを読まずに理解できるようにする。

## 設計意図

メモリレイヤーは **optional** である。RAG が既に検索機能を提供するため、メモリ層は補完的な役割に限定している。埋め込みエンドポイントが利用不可能な場合でも FTS5 にフォールバックし、セッションを中断しない。

セマンティックメモリ（長期ルール・決定）とエピソディックメモリ（セッション固有の失敗・Q&A）を分離している。これは注入タイミングと検索戦略の違いによる。セマンティックは重要性閾値でフィルタリングしてセッション開始時に注入し、エピソディックは最初のユーザープロンプトでハイブリッド検索して取得する。

## 責務境界

- メモリレイヤーが所有するもの: セッション横断のコンテキスト復元（ルール、決定、失敗パターン、会話の Q&A）
- メモリレイヤーが所有しないもの: RAG ドキュメント検索、LLM コンテキスト生成、ツール実行

## 主要な制約

- `memory_local_only = true` を設定すると、埋め込みエンドポイントがループバックアドレスであることを強制する。`embed_url` がローカルでない場合は起動が失敗する。
- セッション開始時のセマンティックメモリ注入には `importance >= 0.5` が必要。低い重要度のエントリは自動注入されない。
- pinned エントリはセッション開始ごとに必ず注入される（importance 閾値を超えなくても）。

## 運用上の注意

- データがマシン外に出てはならない場合は `memory_local_only = true` を設定する。
- `/memory status` で現在のモードを確認できる（Hybrid / FTS-only / Degraded / Disabled）。
- JSONL バックアップの復元後に `/memory rebuild` をテスト済みであることを確認する。

## 既知の制限 / 未解決事項

なし

## 関連資料

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search-part1.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes-part2.md`
