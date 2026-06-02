# sqlite-mcp — 読み取り専用 SQLite クエリ (ポート 8011)

## 1. 概要

`mcp/sqlite/server.py` / `mcp/sqlite/service.py` / `mcp/sqlite/models.py` で実装。エージェントが RAG データや会話履歴を直接 SQL で照会できる読み取り専用インターフェース。

| 項目 | 内容 |
|---|---|
| ポート | 8011 |
| ツール数 | 1 (`query_sqlite`) |
| 設定ファイル | `config/sqlite_mcp_server.toml` |
| 起動モード | `startup_mode = "subprocess"` (エージェント管理サブプロセス) |

---

## 2. セキュリティモデル

### 2.1 DB 許可リスト

`db_allowlist` に列挙された名前のみアクセス可能。リスト外の DB 名は即座にエラーを返す (fail-closed)。`db_allowlist` が空のとき全 DB リクエストを拒否。

```toml
db_allowlist = ["rag", "session"]
[db_paths]
rag     = "/opt/llm/db/rag.sqlite"
session = "/opt/llm/db/session.sqlite"
```

### 2.2 SELECT 専用

クエリ受信時に以下を検証する:

1. SQL コメント (`--` / `/* */`) を除去
2. 複数ステートメント (`;` が複数) を拒否
3. 最初のキーワードが `SELECT` でない場合を拒否

### 2.3 PRAGMA query_only=ON

コネクション確立直後に `PRAGMA query_only=ON` を実行し、SQLite エンジンレベルでの書き込みを防止。

### 2.4 行数上限

`max_rows` (デフォルト 100) を超えた行は返却せず `truncated=true` フラグを立てる。

---

## 3. ツール仕様

### query_sqlite

```json
{
  "name": "query_sqlite",
  "args": {
    "db": "rag",
    "sql": "SELECT COUNT(*) FROM chunks"
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `db` | `str` | DB 名 (`db_allowlist` に含まれる必要あり) |
| `sql` | `str` | SELECT 文 (複数ステートメント・SELECT 以外は拒否) |

**レスポンス (成功):**

```json
{
  "columns": ["COUNT(*)"],
  "rows": [[12345]],
  "row_count": 1,
  "truncated": false
}
```

**レスポンス (エラー):**

`is_error=true` で `{"result": "ERR: <message>", "is_error": true}` 形式が返る。

---

## 4. 対象 DB スキーマ

参照先は `rules/env.md` の「SQLite schema」セクションを参照。

| DB 名 | パス | 主なテーブル |
|---|---|---|
| `rag` | `/opt/llm/db/rag.sqlite` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` |
| `session` | `/opt/llm/db/session.sqlite` | `sessions`, `messages`, `notes`, `tool_results`, `memory_entries`, `memory_vec` |

---

## 5. 設定リファレンス (`config/sqlite_mcp_server.toml`)

| キー | デフォルト | 説明 |
|---|---|---|
| `db_allowlist` | `[]` | 許可 DB 名一覧 (空のとき全 DB を拒否) |
| `[db_paths]` | `{}` | DB 名 → 絶対パス マッピング |
| `max_rows` | 100 | クエリ結果の最大行数 |
| `audit_log_path` | `""` | クエリ監査ログパス |
| `auth_token` | `""` | Bearer トークン (`""` で認証無効) |
