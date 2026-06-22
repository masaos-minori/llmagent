# Implementation: test_rag_repository.py — chunks_* トリガー同時実行テスト追加

## Goal

`tests/test_rag_repository.py` に `TestFtsTriggerConcurrency` クラスを新設し、
`chunks_ai` / `chunks_ad` / `chunks_au` トリガーが `ThreadPoolExecutor` による
並行 INSERT / DELETE / UPDATE 下でも FTS インデックスの整合性を保つことをテストする。

## Scope

**In-Scope:**
- `tests/test_rag_repository.py` — `TestFtsTriggerConcurrency` クラスの新設

**Out-of-Scope:**
- `scripts/rag/` の実装変更
- 非 SQLite バックエンドの並行テスト

## Assumptions

1. SQLite WAL モードはライターを1つずつシリアライズする。真の同時書き込みは起きないが、
   Python スレッドから並行呼び出しした際に FTS インデックスが正しく更新されることを確認する。
2. `sqlite3.connect(":memory:", check_same_thread=False)` により複数スレッドから
   同一接続を使用できる。
3. GIL により Python レベルの競合は起きないが、SQLite ライブラリ内の操作は
   `check_same_thread=False` でスレッド間共有される。
4. `timeout=5` を `sqlite3.connect` に指定してロック待ちタイムアウトを設定する。

## Implementation

### Target File

- `tests/test_rag_repository.py` — 45件のテスト

### Procedure

Phase 1: 共通ヘルパーの追加 → **未完了**
Phase 2: TestFtsTriggerConcurrency クラスの追加 → **未完了**

### Method

既存テストは45件すべてパス。SQLite FTS トリガーの並行処理の整合性をテストする。

### Details

#### Phase 1: 共通ヘルパーの追加

- [ ] `_make_concurrent_db()` ヘルパーを追加:
  `check_same_thread=False, timeout=5` で `:memory:` DB を作成し、
  WAL + 完全な trigger スキーマを適用する

#### Phase 2: TestFtsTriggerConcurrency クラスの追加

- [ ] `test_concurrent_inserts_all_indexed`: `ThreadPoolExecutor(max_workers=4)` で10スレッドが同時に `INSERT INTO chunks`、完了後 FTS が全件を返す
- [ ] `test_concurrent_insert_delete_fts_consistent`: INSERT 10件後、5件を別スレッドグループで並行 DELETE、削除された chunk_id が FTS から消えていることを確認
- [ ] `test_concurrent_updates_fts_updated`: INSERT 後、別スレッドで content を更新、新しい content で FTS 検索が成功し旧 content では0件になることを確認

## Validation Plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| 追加テスト | Integration | `uv run pytest tests/test_rag_repository.py::TestFtsTriggerConcurrency -v` | all pass |
| 全テスト | Regression | `uv run pytest tests/test_rag_repository.py -v` | all pass |
| Lint | Static | `uv run ruff check tests/test_rag_repository.py` | 0 errors |
| Type check | Static | `uv run mypy tests/test_rag_repository.py` | no new errors |
| Pre-commit | Static | `uv run pre-commit run --files tests/test_rag_repository.py` | pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `ThreadPoolExecutor` + `:memory:` SQLite でロック競合が発生して `OperationalError` になる | low | `timeout=5` で待機、スレッド数を 4 に制限、GIL により実質シリアライズ |
| テストが環境依存で flaky になる | low | スレッド数・件数を少なく (10件、4スレッド) 設定し、`concurrent.futures.wait()` で完了を待つ |
| 旧 content が FTS に残る (`chunks_au` の削除フェーズ失敗) | medium | `test_concurrent_updates_fts_updated` で旧 content の 0 件確認を必須とする |
