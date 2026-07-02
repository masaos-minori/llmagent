# Implementation: scripts/db/create_schema.py -- Update module-level docstring to clarify compatibility repair policy

**Plan source:** `plans/20260702-202750_plan.md` (Phase 1)
**Target file:** `scripts/db/create_schema.py`

---

## Goal

モジュールレベルdocstringに、create_schema()の非破壊的互換性修復ポリシーと各_migrate_*関数の役割を明記する。スキーマ作成の設計意図をコード読者に明確に伝える。

---

## Scope

**In:**
- create_schema()の動作方針を4点に整理してdocstringに追記
  1. IF NOT EXISTSによる冪等・非破壊的なスキーマ作成
  2. 限定的互換性修復（カラム追加・特定ローカルテーブル再構築）の適用条件
  3. 破壊的データマイグレーションは行わないこと
  4. 大規模スキーマ移行は明示的なメンテナンスタスクとして別途実施すること
- "Compatibility repairs:" サブセクションを追加し、既存4つの_migrate_*関数を一行説明付きでリスト化

**Out:**
- 実装コード（関数本体）の変更
- スキーマSQLや他ファイルの変更
- 新規テストの追加

---

## Assumptions

1. 現行docstringは日本語混在で記述されており、方針4点を英語または日本語で追記してよい
2. _migrate_*関数は現在4つ存在する: _migrate_rag_schema, _migrate_add_undone_column, _migrate_session_schema, _migrate_workflow_schema

---

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. scripts/db/create_schema.py のモジュールレベルdocstring（1-15行目付近）を読み込む
2. 既存のdocstringに以下を追記する
   - create_schema()の動作方針4点（Policy:セクション）
   - "Compatibility repairs:"サブセクションに_migrate_*関数4つと一行説明
3. ruff check scripts/db/create_schema.py を実行してlintエラーがないことを確認する

### Method

Edit tool でdocstringの`old_string`を特定して`new_string`に置換する

### Details

追記するdocstring内容の例:

```
Policy:
  (1) create_schema() creates current schema objects using IF NOT EXISTS — idempotent, non-destructive.
  (2) Limited compatibility repairs may add missing columns or rebuild specific local tables when safe.
  (3) Destructive data migrations are not performed.
  (4) Large schema transitions must be handled as explicit maintenance tasks.

Compatibility repairs:
  _migrate_rag_schema()         — chunks テーブルに chunk_type/source_file カラムを冪等追加
  _migrate_add_undone_column()  — tool_results テーブルに undone カラムを冪等追加
  _migrate_session_schema()     — tool_results テーブルを session_id FK制約付きで再構築
  _migrate_workflow_schema()    — tasks テーブルに workflow_id カラムを冪等追加
```

挿入位置: 既存のFunctions:セクションの前（または後）に配置する。既存docstringのスタイルと整合させること。

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | ruff check scripts/db/create_schema.py | 0 errors |
| Type check | mypy scripts/db/create_schema.py | no new errors |
| Tests | uv run pytest | all pass |
