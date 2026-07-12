---
title: "MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp"
category: mcp
tags:
  - mcp
  - server-catalog
  - file-write
  - file-delete
  - shell
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_03_rag-pipeline-and-cicd.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_04_05_git.md
---

# MCP Server Catalog: file-write-mcp / file-delete-mcp / shell-mcp

## file-write-mcp（ポート 8007）

**目的:** ローカルファイルシステムへの書き込み操作。全ツールが `dry_run=True` をサポート。
**起動モード:** persistent（HTTP）
**設定:** `config/file_write_mcp_server.toml`

**ツール（4個）:** `write_file`, `edit_file`, `create_directory`, `move_file`

全ツールとも config を必要としない（`requires_config: false`）。

**設定フィールド:** `allowed_dirs`, `max_write_bytes`（デフォルト: 1,000,000）

| ツール | 入力 | dry_run の挙動 |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | diff のみ返す; 書き込みなし |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | diff を返す; 書き込みなし |
| `create_directory` | `{path, dry_run?}` | ディレクトリ情報を返す（存在するか/作成予定か）; 作成なし |
| `move_file` | `{source, destination, dry_run?}` | 移動可能かどうかを返す |

**ヘルス:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**設定:** `max_write_bytes`（デフォルト 1 MB; Pydantic により UTF-8 バイト数として強制）
**エラーコード:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**ログ:** `/opt/llm/logs/file-write-mcp.log`

---

## file-delete-mcp（ポート 8008）

**目的:** ローカルファイルシステムの削除。全ツールが `dry_run=True` をサポート。
**起動モード:** persistent（HTTP）
**設定:** `config/file_delete_mcp_server.toml`

**ツール（2個）:** `delete_file`, `delete_directory`

全ツールとも config を必要としない（`requires_config: false`）。

**設定フィールド:** `allowed_dirs`, `audit_log_path`

| ツール | 入力 | dry_run の挙動 |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | ファイル情報を返す; 削除なし |
| `delete_directory` | `{path, recursive?, dry_run?}` | 内容をスキャン（最大1000ファイル）; 削除なし |

**ヘルス:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**削除 audit ログ:** `/opt/llm/logs/delete_audit.log`（ISO8601 UTC + op + path + user）
**エラーコード:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**ログ:** `/opt/llm/logs/file-delete-mcp.log`

---

## shell-mcp（ポート 8009）

**目的:** `command_allowlist` 内でのサンドボックス化されたシェルコマンド実行。
**起動モード:** persistent（HTTP）
**設定:** `config/shell_mcp_server.toml`

**ツール（1個）:** `shell_run`

| キー | デフォルト | 説明 |
|---|---|---|
| `command_allowlist` | `[]` | 許可されるコマンド名（`argv[0]` のベース名） |
| `shell_cwd_allowed_dirs` | `[]` | 許可される CWD パス（空 = 全て拒否） |
| `max_timeout_sec` | `300` | タイムアウトの上限 |
| `max_output_kb` | `4096` | 出力の上限 |
| `max_memory_mb` | `512` | メモリ制限（`RLIMIT_AS`） |
| `shell_sandbox_backend` | `"none"` | `"firejail"` または `"none"`（下記サンドボックス表を参照） |
| `audit_log_path` | `"/opt/llm/logs/shell_audit.log"` | Audit ログ |
| `default_cwd` | `"/opt/llm/storage"` | リクエストで cwd が指定されない場合の作業ディレクトリ |
| `shell_path` | `"/opt/llm/venv/bin:/usr/bin:/bin"` | 子プロセスの PATH 環境変数 |
| `env_allowlist` | `[]` | req.env で許可される環境変数キー（空の場合は env_denylist を使用） |
| `env_denylist` | `["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]` | req.env から除去される環境変数キーの glob パターン |
| `execution_user` | `""` | setuid でコマンドを実行する OS ユーザー（CAP_SETUID が必要） |
| `kill_policy` | `"sigterm_then_sigkill"` | タイムアウトしたプロセスに対する SIGTERM+SIGKILL、または `"sigkill_only"` |
| `kill_grace_sec` | `2.0` | SIGTERM 後、SIGKILL に切り替えるまでの待機秒数 |

**ヘルス:** sh が見つかる場合は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"sandbox_backend":"firejail"/"none"}}`; 見つからない場合は `"status":"degraded","ready":false,"dependencies":{"shell":"sh not found in PATH"/"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**ログ:** `/opt/llm/logs/shell-mcp.log`

| sandbox_backend | 意味 | 使用場面 |
|---|---|---|
| `"none"` | プロセス分離なし; `RLIMIT_*` の制限のみ適用 | ローカル開発専用 |
| `"firejail"` | firejail によるプロセス分離（`--private --net=none --noroot`） | 本番環境推奨 |

> **セキュリティ注記 — サンドボックスはデフォルトで無効:** `sandbox_backend` のデフォルトは `"none"` である。
> シェルコマンドはエージェントプロセスの OS ユーザーと権限で実行される — コンテナや namespace 分離はない。
> サンドボックスを有効化するには、firejail をインストールし、
> `config/shell_mcp_server.toml` で `sandbox_backend = "firejail"` を設定する。有効なバックエンドは `/health` レスポンスの
> `details.sandbox_backend`（`"none"` または `"firejail"`）で確認できる。
> **本番環境での強制:** 本番モード（`agent.toml` の `security_profile = "production"`）では、
> `sandbox_backend = "none"` は許可されない。この組み合わせが検出された場合、エージェントは起動時に `RuntimeError` を発生させる。
> 本番環境では `sandbox_backend = "firejail"` を設定するか、shell-mcp を無効化すること。

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_04_03_rag-pipeline-and-cicd.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`

## Keywords

mcp
server-catalog
file-write-mcp, file-delete-mcp, shell-mcp, port 8007, port 8008, port 8009
