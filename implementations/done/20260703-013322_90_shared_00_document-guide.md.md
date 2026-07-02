# Implementation: docs/90_shared_00_document-guide.md — Confirm absence of migration documentation references

**Plan source:** `plans/20260702-201024_plan.md` (Phase 6)
**Target file:** `docs/90_shared_00_document-guide.md`

---

## Goal

`docs/90_shared_00_document-guide.md` 内にマイグレーション関連の記述（`migrate_schema`、`ALTER TABLE`、後方互換追加）が残っていないことを確認し、あれば削除または書き換える。

---

## Scope

**In:**
- ファイル全体をスキャンして以下のキーワードを検索: `migrate_schema`、`ALTER TABLE`、`backward-compatible`、`backward compatible`、`_migrate`
- 見つかった場合: DBを再作成するポリシーに沿った内容に書き換え、またはその行を削除
- 変更がない場合: ファイルをそのまま保持しスキャン結果を記録

**Out:**
- ファイルの構造変更（セクション追加・削除）
- 他ドキュメントファイルへの変更

---

## Assumptions

1. プランの調査時点（フェーズ作成時）でファイル内にマイグレーション関連の記述は見つからなかった。実装時の確認は念のための検証である
2. ファイルへの変更が不要であっても、このドキュメントはスキャン実施の記録として有効である

---

## Implementation

### Target file

`docs/90_shared_00_document-guide.md`

### Procedure

1. `grep -n "migrate\|ALTER TABLE\|backward.compat" docs/90_shared_00_document-guide.md` を実行してマイグレーション関連の記述を検索する
2. ヒットがない場合: 変更不要と判断し、その旨を記録する
3. ヒットがある場合:
   a. 該当箇所を読み、文脈を把握する
   b. DBを再作成するポリシーに反する記述であれば削除または書き換える
   c. 例: マイグレーション関数への参照をDDL-only再作成の説明に置き換える

### Method

Bash tool（grep検索） → ヒットがある場合のみ Edit tool

### Details

検索パターン:
- `migrate_schema`
- `_migrate`
- `ALTER TABLE`
- `backward-compatible`
- `backward compatible`

期待される結果: 現行ファイルにはマイグレーション関連の記述がないため、変更不要となる見込み。

ファイルの「Canonical Source Rules」セクションや「Guidance for Safe AI Use」セクションにマイグレーション関連の記述がある場合は以下の方針で対処する:
- DB再作成ポリシーへの参照が存在しない場合: `90_shared_05` §8 の「corruption recovery」セクションが再作成手順を扱うため、そこへのリンクで代替

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| スキャン確認 | grep -n "migrate\|ALTER TABLE\|backward.compat" docs/90_shared_00_document-guide.md | 0件ヒット（変更不要を確認） |
| Lint | ruff check docs/ | N/A（Markdownファイルのためスキップ） |
| Tests | uv run pytest | all pass |
