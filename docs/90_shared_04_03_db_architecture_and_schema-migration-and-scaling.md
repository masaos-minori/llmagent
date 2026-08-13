---
title: "DB Architecture and Schema - Migration and Scaling"
category: shared
tags:
  - shared
  - db
  - migration
  - constraints
  - scaling-limits
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
  - 90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md
source:
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
---

# DB Architecture and Schema

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 8. スキーマ生成とマイグレーション方針

```python
# Initialize all schemas (rag + session + workflow + eventbus)
from db.create_schema import create_schema
create_schema()
```

- すべてのDDLは`IF NOT EXISTS`を使用する — べき等であり、何度実行しても安全
- **rag.sqlite/session.sqlite/eventbus.sqliteは互換マイグレーションに非対応。** これらのスキーマの変更にはDBの再作成が必要: アーカイブ → 削除 → `create_schema()`による再作成。完全な手順は[90_shared_05 §11](90_shared_05_04_db_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure)を参照。workflow.sqlite（§8a）とmdq.sqlite（§8c）はそれぞれ異なる方式のマイグレーション/自動スキーマ更新機構を持つ — 詳細は各節を参照。
- `embedding_dims`は実行時にconfigから動的に置換される（デフォルト384）

### 8a. workflow.sqlite限定の増分マイグレーション (Explicit in code)

上記の「rag/session/eventbusは互換マイグレーションに非対応」という原則は、この3つのDBに限定したものである。`workflow.sqlite`はその対象外であり、`db/schema_sql.py`が専用の増分マイグレーション機構を実装している。

- `db/schema_sql.py`が`list[tuple[str, str]]`形式のマイグレーションリスト（ID + SQL文ペア）を保持し、`apply_workflow_migrations()`で順次適用する
- `sqlite3.OperationalError`のうち`"duplicate column name"`を含むものだけを握り潰し（既に適用済みとみなす）、他は再送出する
- `create_workflow_schema()`はベーステーブル作成後、マイグレーション適用→バージョン記録を行う
- 新規DBではベーススキーマに既にカラムが含まれるためマイグレーションはno-op。既存DBに対してのみ増分カラム追加として機能する

rag.sqlite/session.sqlite/eventbus.sqliteにはこの種の増分マイグレーション機構は存在しない。

### 8b. RAG整合性検証 (Explicit in code)

`db/rag_consistency.py::check_rag_consistency()`は`chunks`/`chunks_fts`/`chunks_vec`の行数を比較し、`RagConsistencyReport`（`db/models.py`）を返す読み取り専用検証関数である。整合条件と不整合メッセージ生成ロジックの詳細はコード参照。

### 8c. mdq.sqlite限定の自動レガシースキーマ検出 (Explicit in code)

`scripts/mcp_servers/mdq/db_schema.py::create_production_tables()`は、MDQサービス起動時に自動実行される、rag/session/eventbusともworkflowとも異なる第三のスキーマ更新パターンである。

- **トリガー:** MDQサービス起動ごとに毎回呼び出される（明示的なマイグレーションコマンドは不要）
- **検出:** `PRAGMA table_info(chunks)`で旧スキーマかどうかを判定
- **アクション:** 旧スキーマ検出時、`chunks`/`chunks_fts`テーブルおよび関連トリガーを無条件に`DROP`し、現行スキーマで再作成
- **対比:** 8aのworkflow.sqliteのようなバージョン管理カラムや明示的なALTER TABLEマイグレーションリストは存在しない — 起動時に毎回スキーマ形状を検査し、古ければ黙って作り直すだけの機構である
- **データ損失に関する注意:** 旧スキーマ検出時の`DROP`は無条件であり、既存データは再作成後に失われる

rag.sqlite/session.sqlite/eventbus.sqliteの`chunks_vec`/`memories_vec`（`db/schema_sql.py`）はMDQのスキーマ/ハイブリッド検索クリーンアップ作業とは無関係であり、影響を受けない。

---

## 9. 制約一覧

SQLite 3.35+ required; sqlite-vec path /opt/llm/sqlite-vec/vec0.so (agent.toml::sqlite_vec_so); WAL mode on all connections (PRAGMA journal_mode=WAL); busy_timeout 30,000 ms default (agent.toml::sqlite_busy_timeout_ms); embedding dimension 384 default (agent.toml::embedding_dims); float format float32 little-endian BLOB; single-node only (no distributed/replica support); agent.toml included in ConfigLoader().load_all() at index 0 (see 90_shared_03 §2a).

---

## 9a. AIリファレンスガイド

rag.sqlite schema location: this doc §5; session.sqlite schema location: this doc §6; SQLiteHelper supports workflow.sqlite: yes (target="workflow", not documented in spec, see §4); embedding dimension set via agent.toml::embedding_dims (default 384); schema initializer: create_schema() — idempotent DDL-only initialization, not migration; DB triggers documented: chunks_fts auto-sync triggers (§5), memories_fts auto-sync triggers (§6).

---

## 10. 正典（Source of Truth）

DDL source: db/schema_sql.py; schema initialization entry point: db/create_schema.py::create_schema(); deploy initialization entry point: deploy/init_db.sh; DB connection helper: db/helper.py::SQLiteHelper; DB files: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite; Event Bus schema (DDL only): scripts/eventbus/schema.sql; mdq.sqlite schema/auto-update source: scripts/mcp_servers/mdq/db_schema.py::create_production_tables() (see §8c); deleted entry point: db/workflow_schema.py — removed in plan 54.

**注記:** Event Busランタイム（publisher/subscriber/dispatcher/DLQワーカー）は本クリーンアップの対象外である。今後のEvent Bus書き込み処理はISO-8601 UTC Zサフィックス形式のタイムスタンプを使用しなければならない。

## 11. スケーリング限界とマイグレーションの兆候

現行のRAGアーキテクチャはシングルノードSQLiteを使用している。これはチーム規模の
デプロイで、コーパスサイズが中程度かつ同時書き込みが頻発しない場合に適している。
以下の兆候は、再評価が必要となりうるタイミングを示す。

### コーパスサイズ

- **`chunks`テーブルが約50万行を超える場合:** `chunks_vec`におけるKNNスキャン時間はコーパス
  サイズに対して線形に増加する。この規模になったら`/rag search`のレイテンシの監視を開始すること。
  *(要確認: 実際の閾値はハードウェアと埋め込み次元数に依存する。)*
- **DBファイルサイズが約10GBを超える場合:** VACUUM時間、バックアップ所要時間、WALチェックポイント
  のレイテンシがいずれも増加し、`/db vacuum`が秒単位ではなく分単位の時間を要する場合がある。
  *(要確認。)*

### 書き込み同時実行性

- 同一の`rag.sqlite`に対して複数の`RagIngester`プロセスが同時に書き込むと、WALレイヤーで
  シリアライズされる。取り込みスループットがボトルネックとなる場合、SQLiteの書き込み
  シリアライズが制約要因となりうる。
- **兆候:** WALファイルがチェックポイントによる縮小よりも速く増大する。`/db health`で監視すること。

### FTS5検索レイテンシ

- **兆候:** `/rag search`が一貫して500msを超える。FTS5のBM25はドキュメント数に応じて
  スケールするため、非常に大きなコーパスでは検索速度が低下する場合がある。
  *(要確認。)*

### 運用上の複雑性に関する兆候

- ファイルサイズの増大に伴い、バックアップとポイントインタイムリカバリが複雑化する
- 複数環境で同一DBファイルを共有することは非対応（SQLiteは単一ファイル方式のため）
- 規模が拡大するにつれ`/session rag-consistency`の問題の修復が難しくなる

### マイグレーション兆候チェックリスト

以下のうち2つ以上に該当する場合、アーキテクチャの見直しを検討すること:

- [ ] p95でのKNN検索レイテンシが1秒を超える
- [ ] DBファイルサイズが20GBを超える
- [ ] WALチェックポイントが一貫して30秒を超える
- [ ] 取り込みキューの深さが一貫して未処理チャンクファイル1万件を超える
- [ ] 複数のチームまたはプロセスが同時書き込みアクセスを必要とする

通常運用でこれらの兆候を監視するには`/db health`と`/session rag-consistency`を使用すること。

### 限界が近づいた際に評価すべき事項

- **ベクトル検索:** 専用のベクトルデータベース（近似最近傍探索、分散インデックス）は、
  ベクトル数が100万を超える規模で`sqlite-vec`を上回る性能を発揮する
- **全文検索:** 転置インデックス型の検索サービスは、より低いレイテンシで大規模コーパスを扱える
- **ハイブリッドストア:** リレーショナルDB + ベクトル拡張（例: `pgvector`互換）は、SQLセマンティクス
  を維持しながら書き込み同時実行性のスケーリングを可能にする

> **注記:** 上記の数値閾値はすべて計画上の見積もりであり、ベンチマークによって保証されたものではない。
> 実際の限界はハードウェア、埋め込み次元数、クエリパターン、コーパスの特性に依存する。
> いずれの閾値も確定的なものとして扱う前に、個別のデプロイ環境で検証すること。

## 12. スキーマ変更チェックリスト

スキーマを変更するタスクでは、以下すべてに回答すること:

- [ ] どのDBが影響を受けるか？（rag/session/workflow/eventbus/mdq）
- [ ] どのスキーマソースファイルが影響を受けるか？
- [ ] 新規インストール専用のDDL変更か？
- [ ] 既存DBに対するマイグレーションが必要か？
- [ ] マイグレーションを提供しない場合、DBの再作成が必要か？
- [ ] データ損失の可能性はあるか？
- [ ] スキーマの挙動を反映するようテストは更新されているか？
- [ ] RAG、session、workflow、eventbus、MDQのいずれに影響するか？


