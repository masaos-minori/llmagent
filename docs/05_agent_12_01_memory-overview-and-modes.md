
title: "Memory Layer - Overview and Modes (Part 1)"
category: agent
tags:
  - agent
  - memory
  - overview
  - memory-modes
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_01_memory-overview-and-modes.md


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
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`

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
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`



# Memory Layer — Overview and Modes (Part 2)

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## メモリモード

メモリ層は4つの異なるモードで動作し、`/memory status` で確認できる。

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | 完全動作 — 埋め込みエンドポイントが利用可能で正常な埋め込みを返している状態 | ベクトル類似度と FTS 結果の RRF マージによるハイブリッド検索 |
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

### 実装上の補足: `on_session_stop` の永続化順序と失敗時の扱い

セッション終了時の埋め込み付きエントリ永続化は SQLite への `upsert` を先に実行し、その後に JSONL への書き込みを行う。JSONL 書き込みが `OSError` で失敗しても例外は再送出されず、警告ログを出して処理を継続する（エントリは SQLite にのみ保存された状態になる）。

埋め込み取得が失敗した場合も処理は継続し、埋め込みなしでエントリを保存する（`stat_embed_skip` をインクリメントし `memory.embed_skip` を info ログに出力）。

埋め込みが成功した場合のみ、重複リンク探索が KNN 近傍探索を行い、`DedupPolicy.threshold`（デフォルト 0.3）未満の距離のエントリ間に `memory_links` テーブルへ関連リンクを記録する。挿入失敗（`OperationalError` / `IntegrityError`）は警告ログのみで無視される。

自動抽出（`on_session_stop`）は `DedupAction.SKIP_NEW` による重複排除を適用するが、セマンティック書き込み / エピソディック書き込み（手動書き込み）は意図的にこの重複排除をバイパスする。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`

# Memory Layer — Overview and Modes (Part 2)

- 運用と可観測性 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- 設定 → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## メモリモード

メモリ層は4つの異なるモードで動作し、`/memory status` で確認できる。

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | 完全動作 — 埋め込みエンドポイントが利用可能で正常な埋め込みを返している状態 | ベクトル類似度と FTS 結果の RRF マージによるハイブリッド検索 |
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

### 実装上の補足: `on_session_stop` の永続化順序と失敗時の扱い

セッション終了時の埋め込み付きエントリ永続化は SQLite への `upsert` を先に実行し、その後に JSONL への書き込みを行う。JSONL 書き込みが `OSError` で失敗しても例外は再送出されず、警告ログを出して処理を継続する（エントリは SQLite にのみ保存された状態になる）。

埋め込み取得が失敗した場合も処理は継続し、埋め込みなしでエントリを保存する（`stat_embed_skip` をインクリメントし `memory.embed_skip` を info ログに出力）。

埋め込みが成功した場合のみ、重複リンク探索が KNN 近傍探索を行い、`DedupPolicy.threshold`（デフォルト 0.3）未満の距離のエントリ間に `memory_links` テーブルへ関連リンクを記録する。挿入失敗（`OperationalError` / `IntegrityError`）は警告ログのみで無視される。

自動抽出（`on_session_stop`）は `DedupAction.SKIP_NEW` による重複排除を適用するが、セマンティック書き込み / エピソディック書き込み（手動書き込み）は意図的にこの重複排除をバイパスする。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`
- `05_agent_12_01_memory-overview-and-modes.md`

