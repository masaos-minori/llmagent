# shell-mcp — サンドボックスシェル実行 (ポート 8009)

## 1. 概要

`mcp/shell/server.py` / `mcp/shell/service.py` / `mcp/shell/models.py` で実装。サンドボックス化されたシェルコマンドを安全に実行する MCP サーバ。

| 項目 | 内容 |
|---|---|
| ポート | 8009 |
| ツール数 | 1 (`shell_run`) |
| 設定ファイル | `config/shell_mcp_server.toml` |
| 監査ログ | `/opt/llm/logs/shell_audit.log` |
| 起動モード | `startup_mode = "subprocess"` (エージェント管理サブプロセス) |

---

## 2. セキュリティモデル

多層防御を実装している。

### 2.1 コマンド許可リスト

`command_allowlist` に列挙された `argv[0]` のベース名のみ実行可能。フルパス (`/usr/bin/ls`) のベース名 (`ls`) で照合する。リストに含まれないコマンドは HTTP 403 を返す。

```toml
command_allowlist = ["pytest", "python", "python3", "git", "ruff", "mypy"]
```

### 2.2 作業ディレクトリ制限

`shell_cwd_allowed_dirs` に列挙されたディレクトリ配下のパスのみ `cwd` として許可。`Path.resolve()` で正規化してから照合するため、シンボリックリンクによるトラバーサルを防止。

`cwd` 未指定時は `default_cwd` を使用。`default_cwd` も未設定なら親プロセスの cwd を継承。

### 2.3 リソース制限 (setrlimit)

子プロセスの `preexec_fn` で以下の制限を適用:

| リソース | 制限値 |
|---|---|
| `RLIMIT_CPU` | `max(timeout_sec × 2, 60)` 秒 (asyncio timeout の補助、最低 60 秒) |
| `RLIMIT_AS` | `max_memory_mb` MB |
| `RLIMIT_NOFILE` | 256 |
| `RLIMIT_NPROC` | 64 (fork bomb 対策) |
| `RLIMIT_FSIZE` | 256 MB |

### 2.4 タイムアウト・出力制限

- `timeout_sec`: デフォルト 30 秒、上限は `max_timeout_sec` (デフォルト 300 秒)
- `max_output_kb`: 合計 stdout+stderr のバイト上限 (デフォルト 512 KB、上限 4096 KB)
- タイムアウト時は `kill_policy` に従い SIGTERM → SIGKILL で終了

### 2.5 環境変数フィルタ

`env_allowlist` が非空のとき: リスト外のキーを削除 (allowlist モード)。
空のとき: `env_denylist` のグロブパターンにマッチするキーを削除 (denylist モード)。
デフォルトでは `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH` を除去。

### 2.6 サンドボックスバックエンド

`shell_sandbox_backend = "firejail"` のとき `firejail --private --net=none --noroot --` でラップ。`firejail` が PATH に存在しない場合は起動時に警告を出して `"none"` にフォールバック。

---

## 3. ツール仕様

### shell_run

```json
{
  "name": "shell_run",
  "args": {
    "command": "pytest -q tests/",
    "argv": null,
    "timeout_sec": 60,
    "cwd": "/opt/llm/workspace",
    "env": {"MY_VAR": "value"},
    "max_output_kb": 512,
    "dry_run": false
  }
}
```

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `command` | `str` | (必須) | コマンド文字列 (argv[0] がアローリストチェック対象) |
| `argv` | `list[str] \| null` | `null` | 明示的 argv リスト。指定時は `shlex.split(command)` を使わず直接使用 (インジェクション防止) |
| `timeout_sec` | `int` | 30 | タイムアウト秒数 (サーバ設定の `max_timeout_sec` でクランプ) |
| `cwd` | `str \| null` | `null` | 作業ディレクトリ (`shell_cwd_allowed_dirs` でバリデーション) |
| `env` | `dict[str, str]` | `{}` | 追加環境変数 (フィルタ後に OS 環境にマージ) |
| `max_output_kb` | `int` | 512 | 出力サイズ上限 KB |
| `dry_run` | `bool` | `false` | `true` のとき実行せずプレビュー文字列を返す |

**レスポンス (通常実行):**

```
exit_code=0 elapsed=1.23s
--- stdout ---
<stdout テキスト>
--- stderr ---
<stderr テキスト>
```

**レスポンス (dry_run=true):**

```json
{"preview": "Would execute: pytest -q tests/ (cwd: /opt/llm/workspace)", "dry_run": true}
```

---

## 4. 監査ログ

`/opt/llm/logs/shell_audit.log` に各実行を追記する。

```
2025-01-01T00:00:00+00:00 cmd='pytest -q tests/' argv=['pytest', '-q', 'tests/'] cwd='/opt/llm/workspace' uid=1000 exit=0 elapsed=1.23s truncated=False
```

MCP サーバの `/v1/call_tool` エンドポイントも `AUDIT` ログを `shell-mcp.log` に出力する (形式: `docs/04_mcp-protocol.md` §2.2.1 参照)。

---

## 5. 設定リファレンス (`config/shell_mcp_server.toml`)

| キー | デフォルト | 説明 |
|---|---|---|
| `command_allowlist` | `[]` | 許可コマンド名一覧 (空のとき全コマンドを拒否) |
| `shell_cwd_allowed_dirs` | `[]` | 許可作業ディレクトリ (空のとき全 cwd を拒否) |
| `default_cwd` | `""` | cwd 未指定時のデフォルト作業ディレクトリ |
| `max_timeout_sec` | 300 | タイムアウト上限 (秒) |
| `max_output_kb` | 4096 | 出力上限 (KB) |
| `max_memory_mb` | 512 | 子プロセスメモリ上限 (MB) |
| `shell_path` | `/usr/bin:/bin` | 子プロセスの `PATH` |
| `audit_log_path` | `""` | 監査ログパス (`/opt/llm/logs/shell_audit.log` を推奨); 空のとき監査ログなし |
| `shell_sandbox_backend` | `"none"` | `"firejail"` または `"none"` |
| `env_allowlist` | `[]` | 許可する req.env キー (非空時 allowlist モード) |
| `env_denylist` | `["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]` | 拒否する req.env キーのグロブ (env_allowlist 空時に有効) |
| `execution_user` | `""` | 実行 OS ユーザ (setuid; root 権限要) |
| `kill_policy` | `"sigterm_then_sigkill"` | タイムアウト終了ポリシー |
| `kill_grace_sec` | 2.0 | SIGTERM 後の猶予秒数 |
