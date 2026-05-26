# MCP サーバ責務分離 + Shell 実行仕様 — 方針と実装概要

作成日: 2026-05-26

---

## 1. MCP サーバ責務分離

### 1.1 問題の整理

現行の `fileop_mcp_server.py` (port 8005) は一つのサーバに読み取り・書き込み・削除をすべて集約している。
`allowed_dirs: ["/opt/llm"]` のみで境界を引いており、LLM は同一権限で読み・書き・削除が可能な状態になっている。
これは最小権限原則に反し、誤操作や prompt injection によるファイル破壊リスクを増大させる。

### 1.2 分離方針

責務を「アクセス種別」と「破壊度」で 4 サーバに分割する。

| サーバ | ポート | 責務 | allowed_dirs の粒度 |
|---|---|---|---|
| `file-read-mcp` | 8005 (現行維持) | 読み取り専用 | 広め (例: `/opt/llm`, `/workspace`) |
| `file-write-mcp` | 8007 (新設) | 作成・編集・移動 | 中程度 (例: `/opt/llm/workspace`) |
| `file-delete-mcp` | 8008 (新設) | 削除・プロジェクト管理 | 狭め (例: `/opt/llm/workspace`) |
| `shell-mcp` | 8009 (新設) | シェルコマンド実行 | `cwd` 許可ディレクトリで制御 |

各サーバは現行の `models / service / server` 3 層構成を踏襲する。

### 1.3 各サーバのツール割り当て

#### `file-read-mcp` (読み取り専用)

現行の FileService から読み取り系メソッドのみ移植する。

| ツール名 | 現行の対応 |
|---|---|
| `list_directory` | 現行と同一 |
| `list_directory_with_sizes` | 現行と同一 |
| `directory_tree` | 現行と同一 |
| `read_text_file` | 現行と同一 |
| `read_media_file` | 現行と同一 |
| `read_multiple_files` | 現行と同一 |
| `search_files` | 現行と同一 |
| `grep_files` | 現行と同一 |
| `get_file_info` | 現行と同一 |

設定ファイル: `config/file_read_mcp_server.json`
```json
{
  "allowed_dirs": ["/opt/llm", "/workspace"],
  "max_read_bytes": 1000000,
  "max_tree_depth": 5,
  "max_search_results": 200
}
```

#### `file-write-mcp` (作成・編集・移動)

書き込み系のみ。削除は含まない。

| ツール名 | 現行の対応 | 追加制約 |
|---|---|---|
| `write_file` | 現行と同一 | max_write_bytes |
| `edit_file` | 現行と同一 | dry_run=true を推奨 |
| `create_directory` | 現行と同一 | — |
| `move_file` | 現行と同一 | src/dst 両方が allowed_dirs 配下であること |

設定ファイル: `config/file_write_mcp_server.json`
```json
{
  "allowed_dirs": ["/opt/llm/workspace"],
  "max_write_bytes": 1000000
}
```

#### `file-delete-mcp` (削除・プロジェクト管理)

破壊的操作を分離し、audit log を必須とする。

| ツール名 | 説明 | 追加制約 |
|---|---|---|
| `delete_file` | ファイル削除 | audit log 必須 |
| `delete_directory` | ディレクトリ削除 | recursive=true はデフォルト false |

`require_approval_tools` (agent.json) に `delete_file` / `delete_directory` を追加し、
エージェントが実行前に y/N 確認を取るよう強制する。

設定ファイル: `config/file_delete_mcp_server.json`
```json
{
  "allowed_dirs": ["/opt/llm/workspace"],
  "audit_log_path": "/opt/llm/logs/delete_audit.log"
}
```

### 1.4 ツールルーティングの変更 (`tool_executor.py`)

現行の `_route()` を拡張してサーバキーを 4 つに分ける。

```python
_READ_TOOLS = frozenset({
    "list_directory", "list_directory_with_sizes", "directory_tree",
    "read_text_file", "read_media_file", "read_multiple_files",
    "search_files", "grep_files", "get_file_info",
})
_WRITE_TOOLS = frozenset({"write_file", "edit_file", "create_directory", "move_file"})
_DELETE_TOOLS = frozenset({"delete_file", "delete_directory"})

def _route(self, tool_name: str) -> str:
    if tool_name in _READ_TOOLS:
        return "file_read"
    if tool_name in _WRITE_TOOLS:
        return "file_write"
    if tool_name in _DELETE_TOOLS:
        return "file_delete"
    if tool_name == "shell_run":
        return "shell"
    if tool_name == "search_web":
        return "web_search"
    if tool_name.startswith("github_"):
        return "github"
    raise ValueError(f"Unknown tool: {tool_name}")
```

### 1.5 `agent.json` の変更点

`mcp_servers` に 3 サーバを追加。`file_server_url` は `file-read-mcp` に対応させ、
`file-write-mcp` / `file-delete-mcp` / `shell-mcp` を新規追加する。

```json
"mcp_servers": {
  "file_read":  {"transport": "http", "url": "http://127.0.0.1:8005", ...},
  "file_write": {"transport": "http", "url": "http://127.0.0.1:8007", ...},
  "file_delete":{"transport": "http", "url": "http://127.0.0.1:8008", ...},
  "shell":      {"transport": "http", "url": "http://127.0.0.1:8009", ...},
  "web_search": {"transport": "http", "url": "http://127.0.0.1:8004", ...},
  "github":     {"transport": "http", "url": "http://127.0.0.1:8006", ...}
}
```

`plan_blocked_tools` に `delete_file`, `delete_directory`, `shell_run` を追加する。

### 1.6 移行手順

1. `file-read-mcp` を新規作成し、旧 `fileop_mcp_server.py` の読み取り系を移植
2. port 8005 を `file-read-mcp` に割り当て; 旧 fileop は 8005 のまま暫定並走
3. `file-write-mcp` を新規作成し、書き込み系を移植
4. `file-delete-mcp` を新規作成し、削除系 + audit log を移植
5. `shell-mcp` を新規作成 (§2 の仕様に基づく)
6. `tool_executor._route()` を更新
7. `agent.json` の `mcp_servers` / `tool_definitions` を更新
8. 旧 `fileop_mcp_server.py` を削除し、init.d/file-mcp サービスを廃止

---

## 2. Shell 実行仕様

### 2.1 ツール定義

ツール名: `shell_run`
サーバ: `shell-mcp` (port 8009)

**Request スキーマ:**
```json
{
  "command": "pytest -q tests/",
  "timeout_sec": 60,
  "cwd": "/opt/llm/workspace/repo",
  "env": {"PYTHONPATH": "/opt/llm/scripts"},
  "max_output_kb": 256
}
```

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `command` | string | 必須 | 実行コマンド文字列 (argv[0] がホワイトリスト照合対象) |
| `timeout_sec` | int | 30 | タイムアウト秒数。config の `shell_max_timeout_sec` を上限とする |
| `cwd` | string | config の `shell_default_cwd` | 作業ディレクトリ。`shell_cwd_allowed_dirs` 配下であること |
| `env` | object | `{}` | 追加環境変数。既存 env とマージ (上書き) |
| `max_output_kb` | int | 512 | stdout+stderr の合計出力上限 (KB) |

**Response スキーマ:**
```json
{
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0,
  "timed_out": false,
  "truncated": false,
  "elapsed_sec": 3.2
}
```

### 2.2 実行ユーザー

- 専用 OS ユーザー `llm-agent` (非 root) でサービスを起動
- OpenRC の `shell-mcp` init スクリプトで `command_user="llm-agent"` を指定
- `llm-agent` は sudo 権限なし、`/opt/llm/workspace` 以外への書き込み権限なし

### 2.3 コマンドホワイトリスト

```json
"shell_allowed_commands": [
  "pytest", "python", "python3",
  "git", "ruff", "mypy", "pre-commit",
  "make", "uv", "pip"
]
```

- 照合対象: `shlex.split(command)[0]` で取り出した argv[0] のベース名
- `shell=False` 固定。シェル展開・パイプ・セミコロンはサブプロセスに渡されない
- ホワイトリスト外の場合: 即時エラー応答 (HTTP 400 / `is_error=True`)
- PATH を `"/opt/llm/venv/bin:/usr/bin:/bin"` に制限して PATH インジェクション防止

### 2.4 タイムアウトと Kill ポリシー

```
asyncio.wait_for(proc.wait(), timeout=timeout_sec)
  → TimeoutError 発生
    → os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # プロセスグループに送信
    → asyncio.sleep(2.0)
    → os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # 強制終了
```

`proc` 生成時に `start_new_session=True` を指定してプロセスグループを作成し、
子プロセスが増殖しても全体を一括終了できるようにする。

### 2.5 リソース制限

`preexec_fn` で `resource.setrlimit()` を呼び出す。

| リソース | 定数 | 設定値 | 意図 |
|---|---|---|---|
| CPU 時間 | `RLIMIT_CPU` | `timeout_sec + 5` 秒 | timeout 後の暴走防止 |
| 仮想メモリ | `RLIMIT_AS` | `shell_max_memory_mb × 1024 × 1024` | OOM 防止 |
| open fd 数 | `RLIMIT_NOFILE` | 64 | fd リーク防止 |
| 子プロセス数 | `RLIMIT_NPROC` | 32 | fork bomb 防止 |
| 書き込みファイルサイズ | `RLIMIT_FSIZE` | `1024 × 1024 × 100` (100 MB) | 一時ファイル爆発防止 |

```python
def _set_resource_limits(max_memory_mb: int, timeout_sec: int) -> None:
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,    (timeout_sec + 5, timeout_sec + 10))
    resource.setrlimit(resource.RLIMIT_AS,     (max_memory_mb * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC,  (32, 32))
    resource.setrlimit(resource.RLIMIT_FSIZE,  (100 * 1024**2,) * 2)
```

`create_subprocess_exec(..., preexec_fn=lambda: _set_resource_limits(...))` で適用する。

### 2.6 stdout/stderr 出力制限

- `proc.communicate(timeout=timeout_sec)` で stdout + stderr を取得
- 合計バイト数が `max_output_kb * 1024` を超えた場合は末尾を切り捨てて
  `\n[output truncated at {max_output_kb}KB]` を付加
- `truncated: true` を response に含める

### 2.7 作業ディレクトリ制限

`cwd` は `shell_cwd_allowed_dirs` 配下に限定する。

```json
"shell_cwd_allowed_dirs": ["/opt/llm/workspace", "/tmp/llm-work"]
```

`Path(cwd).resolve()` で symlink を解決してから prefix チェックする
(FileService._resolve_safe と同方式)。

### 2.8 Audit Log

全 `shell_run` 呼び出しを構造化ログとして記録する。

```
2026-05-26T12:34:56 user=llm-agent cmd="pytest -q" cwd=/opt/llm/workspace exit=0 elapsed=3.2s
```

- ファイル: `/opt/llm/logs/shell_audit.log`
- 成功・失敗・タイムアウトすべて記録
- ログローテーション: logrotate で週次、4 世代保持

### 2.9 設定ファイル

`config/shell_mcp_server.json`:
```json
{
  "_doc": {
    "shell_allowed_commands": "実行を許可するコマンド名リスト (argv[0] のベース名で照合)",
    "shell_max_timeout_sec":  "リクエストで指定できる timeout_sec の上限",
    "shell_max_output_kb":    "stdout+stderr の合計出力上限 (KB)",
    "shell_max_memory_mb":    "子プロセスの仮想メモリ上限 (MB)",
    "shell_cwd_allowed_dirs": "cwd として許可するディレクトリ一覧",
    "shell_default_cwd":      "cwd 未指定時のデフォルト作業ディレクトリ",
    "shell_path":             "子プロセスの PATH 環境変数",
    "shell_audit_log":        "Audit ログのファイルパス"
  },
  "shell_allowed_commands": ["pytest", "python", "python3", "git", "ruff", "mypy"],
  "shell_max_timeout_sec":  300,
  "shell_max_output_kb":    4096,
  "shell_max_memory_mb":    512,
  "shell_cwd_allowed_dirs": ["/opt/llm/workspace"],
  "shell_default_cwd":      "/opt/llm/workspace",
  "shell_path":             "/opt/llm/venv/bin:/usr/bin:/bin",
  "shell_audit_log":        "/opt/llm/logs/shell_audit.log"
}
```

---

## 3. 実装ファイル一覧 (追加分)

| ファイル | 役割 |
|---|---|
| `scripts/file_read_mcp_models.py` | 読み取り系 Pydantic モデル |
| `scripts/file_read_mcp_service.py` | 読み取り系サービスロジック |
| `scripts/file_read_mcp_server.py` | FastAPI app + MCPServer (port 8005) |
| `scripts/file_write_mcp_models.py` | 書き込み系 Pydantic モデル |
| `scripts/file_write_mcp_service.py` | 書き込み系サービスロジック |
| `scripts/file_write_mcp_server.py` | FastAPI app + MCPServer (port 8007) |
| `scripts/file_delete_mcp_models.py` | 削除系 Pydantic モデル |
| `scripts/file_delete_mcp_service.py` | 削除系サービスロジック + audit log |
| `scripts/file_delete_mcp_server.py` | FastAPI app + MCPServer (port 8008) |
| `scripts/shell_mcp_models.py` | shell_run Request/Response モデル |
| `scripts/shell_mcp_service.py` | ShellService (subprocess + resource limit + audit) |
| `scripts/shell_mcp_server.py` | FastAPI app + MCPServer (port 8009) |
| `config/file_read_mcp_server.json` | 読み取り MCP 設定 |
| `config/file_write_mcp_server.json` | 書き込み MCP 設定 |
| `config/file_delete_mcp_server.json` | delete MCP 設定 |
| `config/shell_mcp_server.json` | shell MCP 設定 |
| `init.d/file-read-mcp` | OpenRC init スクリプト (port 8005) |
| `init.d/file-write-mcp` | OpenRC init スクリプト (port 8007) |
| `init.d/file-delete-mcp` | OpenRC init スクリプト (port 8008) |
| `init.d/shell-mcp` | OpenRC init スクリプト (port 8009) |

## 4. 廃止ファイル

| ファイル | 廃止タイミング |
|---|---|
| `scripts/fileop_mcp_server.py` | 移行検証後 |
| `scripts/fileop_mcp_service.py` | 移行検証後 |
| `scripts/fileop_mcp_models.py` | 移行検証後 |
| `config/fileop_mcp_server.json` | 移行検証後 |
| `init.d/file-mcp` | 移行検証後 |

## 5. 未決事項

| 項目 | 内容 |
|---|---|
| chroot / mount namespace | `llm-agent` が非 root のため `unshare --mount --pid` が使えるか Gentoo 環境で確認が必要 |
| file-delete-mcp の audit log ローテーション | logrotate 設定を `deploy/` に含めるか |
| `file-write-mcp` の `move_file` | 移動元が `file-read` 側の allowed_dirs にあるケースへの対処 |
| shell_mcp の stdin | 現仕様では stdin を閉じる (`stdin=DEVNULL`)。対話的コマンドは対象外 |
