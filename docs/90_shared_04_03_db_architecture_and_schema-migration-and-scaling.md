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
- **互換マイグレーションは非対応。** スキーマ変更にはDBの再作成が必要: アーカイブ → 削除 → `create_schema()`による再作成。完全な手順は[90_shared_05 §11](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md#11-db-recreation-procedure)を参照。
- `embedding_dims`は実行時にconfigから動的に置換される（デフォルト384）

---

## 9. 制約一覧

| Constraint | Value |
|---|---|
| SQLite version | 3.35+ required |
| sqlite-vec path | `/opt/llm/sqlite-vec/vec0.so` (from `agent.toml::sqlite_vec_so`) |
| WAL mode | All connections; `PRAGMA journal_mode=WAL` |
| busy_timeout | 30,000 ms default (`agent.toml::sqlite_busy_timeout_ms`) |
| Embedding dimension | 384 default (`agent.toml::embedding_dims`) |
| Float format | float32 little-endian BLOB |
| Single-node only | No distributed/replica support |
| `agent.toml` loading | Included in `ConfigLoader().load_all()` at index 0 — see [90_shared_03](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2a Config Ownership for ownership table |

---

## 9a. AIリファレンスガイド

| 質問 | 回答 |
|---|---|
| rag.sqliteのスキーマはどこにあるか？ | 本ドキュメント§5 |
| session.sqliteのスキーマはどこにあるか？ | 本ドキュメント§6 |
| `SQLiteHelper`はworkflow.sqliteをサポートしているか？ | サポートしている — `target="workflow"`（仕様書には未記載、§4参照） |
| 埋め込み次元数はどのように設定されるか？ | `agent.toml::embedding_dims`（デフォルト384） |
| スキーマを初期化するものは何か？ | `create_schema()` — べき等なDDLのみの初期化であり、マイグレーションではない |
| DBトリガーは文書化されているか？ | されている — chunks_fts自動同期トリガー（§5）、memories_fts自動同期トリガー（§6） |

---

## 10. 正典（Source of Truth）

| カテゴリ | ソース |
|---|---|
| DDLソース | `db/schema_sql.py` |
| スキーマ初期化エントリポイント | `db/create_schema.py::create_schema()` |
| デプロイ初期化エントリポイント | `deploy/init_db.sh` |
| DB接続ヘルパー | `db/helper.py::SQLiteHelper` |
| DBファイル | `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite` |
| Event Busスキーマ（DDLのみ） | `scripts/eventbus/schema.sql` |
| 削除済みエントリポイント | `db/workflow_schema.py` — plan 54で削除 |

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
- 規模が拡大するにつれ`/db consistency`の問題の修復が難しくなる

### マイグレーション兆候チェックリスト

以下のうち2つ以上に該当する場合、アーキテクチャの見直しを検討すること:

- [ ] p95でのKNN検索レイテンシが1秒を超える
- [ ] DBファイルサイズが20GBを超える
- [ ] WALチェックポイントが一貫して30秒を超える
- [ ] 取り込みキューの深さが一貫して未処理チャンクファイル1万件を超える
- [ ] 複数のチームまたはプロセスが同時書き込みアクセスを必要とする

通常運用でこれらの兆候を監視するには`/db health`と`/db consistency`を使用すること。

### 限界が近づいた際に評価すべき事項

- **ベクトル検索:** 専用のベクトルデータベース（近似最近傍探索、分散インデックス）は、
  ベクトル数が100万を超える規模で`sqlite-vec`を上回る性能を発揮する
- **全文検索:** 転置インデックス型の検索サービスは、より低いレイテンシで大規模コーパスを扱える
- **ハイブリッドストア:** リレーショナルDB + ベクトル拡張（例: `pgvector`互換）は、SQLセマンティクス
  を維持しながら書き込み同時実行性のスケーリングを可能にする

> **注記:** 上記の数値閾値はすべて計画上の見積もりであり、ベンチマークによって保証されたものではない。
> 実際の限界はハードウェア、埋め込み次元数、クエリパターン、コーパスの特性に依存する。
> いずれの閾値も確定的なものとして扱う前に、個別のデプロイ環境で検証すること。

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
- `90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`

## Keywords

schema generation
migration approach
constraint list
source of truth
scaling limits
