# Implementation Procedure: deploy/init_db.sh + deploy/build_sqlite_vec.sh + docs/02_deployment.md

## Goal

デプロイ資産を統合し、`docs/02_deployment.md` を現在の実装に合わせる。

## Scope

**In:**
- `deploy/init_db.sh` — `db/rrf.sql` と `scripts/eventbus/schema.sql` の SQL をインライン化
- `deploy/build_sqlite_vec.sh` — sqlite-vec ビルド手順を docs から移植
- `docs/02_deployment.md` — 古いセクション削除・更新
- `docs/03_rag_04_data_model_and_interfaces.md` — スキーマ概要を受け取る
- 削除: `db/rrf.sql`, `scripts/eventbus/schema.sql`

**Out:** RAG スキーマ再設計、Event Bus ランタイム変更

## Procedure

### Phase 1: ソースファイルを読む

以下を順に読む:
1. `deploy/init_db.sh`
2. `db/rrf.sql`
3. `scripts/eventbus/schema.sql`
4. `deploy/deploy.sh`
5. `docs/02_deployment.md`

### Phase 2: init_db.sh 更新

- `db/rrf.sql` の SQL をインライン化 (`heredoc` または直接記述)
- `scripts/eventbus/schema.sql` の SQL をインライン化
- 外部ファイル参照を削除

### Phase 3: SQL ファイル削除

```bash
git rm db/rrf.sql
git rm scripts/eventbus/schema.sql
```

### Phase 4: docs/02_deployment.md 更新

- "deploy.sh が行う処理" を実際の `deploy.sh` に合わせる
- 削除: "1.4.1 量子化方式の比較 (参考)"
- 削除: "4. 動作確認" (重複セクション)
- N100 への言及を削除
- "1.4 LLM モデルの取得" を更新
- "1.5 sqlite-vec のビルド" を "2.1 デプロイ" に移動

### Phase 5: docs/03_rag_04... にスキーマ概要移動

## Validation plan

| Check | Command | Expected |
|---|---|---|
| rrf.sql 削除 | `ls db/rrf.sql` | no such file |
| schema.sql 削除 | `ls scripts/eventbus/schema.sql` | no such file |
| init_db.sh 自己完結 | `grep -n "source\|\.sql" deploy/init_db.sh` | 0 外部参照 |
| doc リンク無効なし | `grep -rn "rrf\.sql\|eventbus/schema\.sql" docs/` | 0 matches |
