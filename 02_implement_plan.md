# 実装計画

> 立案日: 2026-05-28
> 対象 spec: `00_llm_spec_tobe.md` — 危険操作の承認モデル強化
> 計画のみ — 実装はユーザー承認後に着手。

---

## 1. Goal

ツール名ベースの承認 (`require_approval_tools`) を廃止し、引数・対象リソース・操作種別を含む危険度ベース承認モデルへ置き換える。

| 現状 | 目標 |
|---|---|
| `require_approval_tools: list[str]` でツール名マッチのみ | ツール名 + 引数 + リソーススコープで危険度を判定 |
| 承認時に引数内容を表示しない | 承認前に操作プレビューを表示 |
| 承認結果を audit.log に記録しない | `tool_approval` イベントを audit.log に構造化保存 |

---

## 2. Scope

**In**
- `agent_config.py` — 新フィールド追加・バリデーション
- `agent_repl_tool_exec.py` — `check_approval()` 拡張、リスク分類関数、プレビュー生成関数
- `agent_cmd_config.py` — 新フィールドの表示・`/reload` 対応
- `tests/test_tool_approval.py` — 新規テスト

**Out**
- `tool_executor.py` — MCP プロトコルに dry_run 機構はないため変更不要
- MCP サーバー側の変更なし
- DB スキーマ変更なし

---

## 3. Assumptions

- MCP プロトコルは dry_run モードを持たない。"dry_run を強制" は **実行前プレビュー表示** として実装し、承認後に実際のツール呼び出しを行う
- `require_approval_tools` は廃止。`agent.json` から削除し、`_apply_config_params` の reload 対象からも除去する
- リスク分類は **ツール名ベースのデフォルト + 引数パスや GitHub ブランチによるエスカレーション** の 2 段階で行う
- リスクレベル: `"none"` / `"medium"` / `"high"` の 3 値
- `"none"` は自動承認（現在の非 `require_approval_tools` ツールと同等）
- `"high"` は `"yes"` の完全入力を要求（誤 enter 防止）

---

## 4. Unknowns

| 項目 | 状態 | 解決方法 | Blocking |
|---|---|---|---|
| shell_run の安全判定をどの深さまで行うか | 未確定 | コマンド文字列のプレフィックス + キーワードマッチ（subprocess 呼び出しなし）で実装; 不完全であることをコメントに明記 | No |
| `github_*` の write 系を列挙できるか | 解決済み | `github_mcp_tools.py` を確認。high: `push_files` / `create_or_update_file` / `delete_file` / `merge_pull_request`; medium: `create_branch` / `create_pull_request` / `update_pull_request` / `create_issue` / `add_issue_comment` | No |
| `require_approval_tools` の既存設定が `agent.json` にある場合の扱い | 廃止方針 | `build_agent_config()` で `require_approval_tools` を読むコードを削除; `agent.json` からも除去 | No |

---

## 5. Affected areas

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `agent_config.py` | フィールド追加・削除 | `approval_risk_rules` / `approval_protected_paths` / `approval_high_risk_branches` / `approval_shell_safe_prefixes` 追加; `require_approval_tools` 削除 |
| `agent_repl_tool_exec.py` | 関数追加・既存改修 | `_classify_risk()` / `_build_preview()` 追加; `check_approval()` 引数拡張; 承認結果の audit.log 出力追加 |
| `agent_cmd_config.py` | 表示・reload 更新 | 新フィールドの `/config` 表示; `_apply_config_params()` に reload 行追加; `require_approval_tools` 削除 |
| `config/agent.json` | キー変更 | `require_approval_tools` 削除; 新フィールドのデフォルト値追加 |
| `tests/test_tool_approval.py` | 新規 | `_classify_risk` / `_build_preview` / `check_approval` のユニットテスト |

---

## 6. Design

### 6.1 リスクレベル定義

| レベル | 意味 | 承認方式 |
|---|---|---|
| `"none"` | 読み取り専用または副作用なし | 自動承認 |
| `"medium"` | ファイル書き込み・作成 / GitHub 読み書き低危険操作 | プレビュー表示 → `y/N` |
| `"high"` | 削除・shell 実行 / メインブランチへの push / `write_file` in protected path | プレビュー表示 → `yes` 完全入力 |

### 6.2 デフォルト `approval_risk_rules`

```json
{
  "write_file":                    "medium",
  "edit_file":                     "medium",
  "create_directory":              "medium",
  "move_file":                     "medium",
  "delete_file":                   "high",
  "delete_directory":              "high",
  "shell_run":                     "high",
  "github_push_files":             "high",
  "github_create_or_update_file":  "high",
  "github_delete_file":            "high",
  "github_merge_pull_request":     "high",
  "github_create_branch":          "medium",
  "github_create_pull_request":    "medium",
  "github_update_pull_request":    "medium",
  "github_create_issue":           "medium",
  "github_add_issue_comment":      "medium"
}
```

ツール名が `approval_risk_rules` に存在しない場合は `"none"` （自動承認）。

### 6.3 引数によるエスカレーション

`_classify_risk(cfg, tool_name, args)` は以下の順で判定する:

1. `approval_risk_rules` からベースレベルを取得（なければ `"none"` で終了）
2. **パスエスカレーション**: `path` / `file_path` / `directory_path` 引数が `approval_protected_paths` のいずれかで始まる場合 → `"high"` に昇格
3. **ブランチエスカレーション**: `branch` / `base` 引数が `approval_high_risk_branches` に含まれる場合 → `"high"` に昇格
4. **シェル安全化**: `shell_run` かつ `command` 引数が `approval_shell_safe_prefixes` で始まる場合 → `"none"` に降格（自動承認）
5. 最終レベルを返す

### 6.4 プレビュー生成

`_build_preview(tool_name, args)` — ツールごとに人間が読みやすいプレビュー文字列を生成:

| ツール | プレビュー内容 |
|---|---|
| `write_file` / `edit_file` | path + content 先頭 200 文字 |
| `delete_file` / `delete_directory` | path |
| `move_file` | source → destination |
| `shell_run` | command 文字列 |
| `github_*` | owner/repo + operation + key args |
| その他 | args を JSON 表示 |

### 6.5 `check_approval` シグネチャ変更

```python
# 変更前
async def check_approval(ctx: AgentContext, tool_name: str) -> bool

# 変更後
async def check_approval(ctx: AgentContext, tool_name: str, args: dict) -> bool
```

呼び出し側 (`execute_all_tool_calls`) は既に `args_preview` を持っているため、渡すだけでよい。

### 6.6 audit.log 出力

承認結果を以下の JSON-lines 形式で `audit_logger` へ出力:

```json
{
  "event": "tool_approval",
  "task_id": "<turn_id>",
  "tool": "delete_file",
  "risk": "high",
  "decision": "approved",
  "args_preview": {"path": "/opt/llm/agent.log"},
  "ts": 1716900000.0
}
```

`decision`: `"approved"` / `"denied"` / `"auto"` (risk=none 時)

---

## 7. Implementation steps

### Step 1 — `agent_config.py`: フィールド追加・削除

- `require_approval_tools` フィールドを削除
- 以下を追加:

```python
approval_risk_rules: dict[str, str] = field(default_factory=lambda: {
    "write_file": "medium", "edit_file": "medium",
    "create_directory": "medium", "move_file": "medium",
    "delete_file": "high", "delete_directory": "high",
    "shell_run": "high",
    "github_push_files": "high", "github_create_or_update_file": "high",
    "github_delete_file": "high", "github_merge_pull_request": "high",
    "github_create_branch": "medium", "github_create_pull_request": "medium",
    "github_update_pull_request": "medium",
    "github_create_issue": "medium", "github_add_issue_comment": "medium",
})
approval_protected_paths: list[str] = field(default_factory=lambda: [
    "/opt/", "/etc/", "/boot/", "/usr/", "/bin/", "/sbin/",
])
approval_high_risk_branches: list[str] = field(default_factory=lambda: [
    "main", "master",
])
approval_shell_safe_prefixes: list[str] = field(default_factory=lambda: [
    "ls", "cat", "echo", "git log", "git status", "git diff",
    "git show", "git branch", "pwd", "find", "grep",
])
```

- `_validate_tool_params()` に `approval_risk_rules` の値バリデーション追加:
  ```python
  valid_levels = {"none", "medium", "high"}
  bad = {k: v for k, v in self.approval_risk_rules.items() if v not in valid_levels}
  if bad:
      raise ValueError(f"approval_risk_rules: invalid levels {bad}")
  ```

- `build_agent_config()`:
  - `require_approval_tools` 行を削除
  - 新フィールドを `cfg.get()` で読むコードを追加

### Step 2 — `agent_repl_tool_exec.py`: リスク分類 + プレビュー + check_approval 拡張

**`_PREVIEW_PATH_KEYS`** — パス引数名セット:
```python
_PREVIEW_PATH_KEYS: frozenset[str] = frozenset(
    {"path", "file_path", "directory_path", "source", "destination"}
)
```

**`_classify_risk(cfg, tool_name, args) -> str`**:
1. `approval_risk_rules` ルックアップ → ベースレベル取得
2. パスエスカレーション
3. ブランチエスカレーション
4. シェル安全化 (`shell_run` かつ safe prefix → `"none"`)
5. 最終レベルを返す

**`_build_preview(tool_name, args) -> str`**:
- ツール別プレビュー文字列生成

**`check_approval(ctx, tool_name, args) -> bool`** 改修:
```python
async def check_approval(ctx: AgentContext, tool_name: str, args: dict) -> bool:
    risk = _classify_risk(ctx.cfg, tool_name, args)
    if risk == "none":
        _audit_approval(ctx, tool_name, risk, args, "auto")
        return True
    preview = _build_preview(tool_name, args)
    print(f"\n[{risk} risk] {tool_name}")
    print(f"  Preview: {preview}")
    prompt = "  Execute? [yes/no]: " if risk == "high" else "  Execute? [y/N]: "
    answer = (await asyncio.to_thread(input, prompt)).strip().lower()
    approved = (answer == "yes") if risk == "high" else (answer == "y")
    decision = "approved" if approved else "denied"
    _audit_approval(ctx, tool_name, risk, args, decision)
    if not approved:
        print(f"  Skipped: {tool_name}")
    return approved
```

**`_audit_approval(ctx, tool_name, risk, args, decision) -> None`**:
- `ctx.services.audit_logger` が None なら no-op
- JSON-lines 形式で `tool_approval` イベント出力

**呼び出し側変更** (`execute_all_tool_calls`):
```python
# 変更前
if not await check_approval(ctx, tc_name):

# 変更後
if not await check_approval(ctx, tc_name, args_preview):
```

### Step 3 — `agent_cmd_config.py`: 表示・reload 更新

- `_print_config_values()` から `require_approval_tools` 表示行を削除
- 新フィールド (`approval_risk_rules`, `approval_protected_paths`, etc.) の表示を追加:
  ```
  Approval settings:
    risk rules    : write_file=medium, delete_file=high, ...
    protected_paths: /opt/, /etc/, ...
    high_risk_branches: main, master
  ```
- `_apply_config_params()`:
  - `require_approval_tools` reload 行を削除
  - 新フィールドの reload 行を追加

### Step 4 — `config/agent.json` 更新

- `_doc` セクション: `require_approval_tools` エントリを削除; 新フィールドのドキュメントを追加
- 実値セクション: `require_approval_tools` キーを削除; 新フィールドはコードデフォルトを使う（`agent.json` に明示不要）

### Step 5 — `tests/test_tool_approval.py` 新規作成

テストケース:

```python
class TestClassifyRisk:
    test_write_file_returns_medium
    test_delete_file_returns_high
    test_unknown_tool_returns_none
    test_write_to_protected_path_escalates_to_high
    test_shell_run_safe_prefix_returns_none
    test_shell_run_dangerous_returns_high
    test_github_push_to_main_returns_high
    test_github_create_pr_to_feature_returns_medium

class TestBuildPreview:
    test_write_file_shows_path_and_content_preview
    test_delete_file_shows_path
    test_shell_run_shows_command
    test_move_file_shows_source_and_destination
    test_unknown_tool_shows_json_args

class TestCheckApproval:
    test_none_risk_auto_approved_no_input
    test_medium_risk_y_approved
    test_medium_risk_n_denied
    test_high_risk_yes_approved
    test_high_risk_y_denied  # "y" は high risk では不十分
    test_audit_log_written_on_approval
    test_audit_log_written_on_denial
    test_audit_log_skipped_when_no_audit_logger
```

### Step 6 — バリデーション

```bash
# 残存チェック
rg 'require_approval_tools' scripts/ config/ tests/

ruff format scripts/ tests/
ruff check scripts/ tests/ --fix && ruff check scripts/ tests/
mypy scripts/ tests/
pytest tests/test_tool_approval.py -v
pytest -v
pre-commit run --all-files
```

---

## 8. Validation plan

| チェック | ツール | 合格基準 |
|---|---|---|
| `require_approval_tools` 残存なし | `rg` | 0 件 |
| フォーマット | `ruff format` | 差分なし |
| lint | `ruff check` | エラー 0 |
| 型検査 | `mypy` | 新規エラーなし |
| 全テスト | `pytest -v` | 全 passed |

---

## 9. Risks

### 高 (Blocking)

| リスク | 対処 (Step) |
|---|---|
| `check_approval` シグネチャ変更で call site が TypeError になる | Step 2: `execute_all_tool_calls` の呼び出しを同時に更新 |
| `require_approval_tools` を `agent.json` や `_apply_config_params` に残したまま削除すると AttributeError | Step 1・3・4 を同一コミットで適用 |

### 中

| リスク | 対処 |
|---|---|
| シェルコマンドのプレフィックスマッチが不完全 (`sudo ls` など) | コメントに制限を明記; `approval_shell_safe_prefixes` はユーザー設定可能 |
| `approval_risk_rules` デフォルトに含まれない GitHub ツール名が存在する | Step 1 前に `github_mcp_tools.py` を読んで write 系ツール名を全列挙 |
| `"high"` で `"yes"` を要求すると既存ユーザーが戸惑う | `/help` 出力・`/config` 表示にリスクレベルと確認方式を記載 |

### 低 (受容)

| リスク | 対処 |
|---|---|
| audit.log に `args_preview` として機密情報が入りうる | `mask_args()` を通した後の値を保存する |
| protected_paths マッチが前方一致のため `/opt_backup/` も保護される | 末尾 `/` を必須にした正規化ルールをコメントに明記 |
