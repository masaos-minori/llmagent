---
title: "Agent Tool Execution and Approval - Approval Flow"
category: agent
tags:
  - agent
  - tool-execution
  - approval-flow
  - risk-classification
  - plan-mode
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
source:
  - 05_agent_06_tool-execution-and-approval.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## 承認フロー

各ツール実行前に`check_approval()`が実行される:

### 事前チェック (即時拒否)

1. **`allowed_tools`ホワイトリスト:** リストが空でなく、ツールがリストに含まれない場合 → 拒否
2. **`allowed_root`ルートジェイル:** パス引数が`cfg.allowed_root`外の場合 → 拒否
3. **GitHubリポジトリの許可リスト:** 書き込み操作対象のリポジトリが`approval_github_allowed_repos`に含まれない場合 → 拒否 (フェイルクローズ)

#### `check_allowed_root(cfg, tool_name, args)`

いずれかのパス引数が`cfg.approval.allowed_root`の外にある場合`False`を返す。以下の場合は`True`を返す:
- `allowed_root`が未設定 (制限なし)
- すべてのパス引数が許可されたルート内のパスに解決される

#### `check_allowed_repo(cfg, tool_name, args)`

GitHub書き込みツールが許可リストにないリポジトリを対象とする場合`False`を返す。GitHub書き込みツールにのみ適用される。戻り値:
- GitHub書き込みツール以外は`True`
- `allowed_repos`が空の場合`False` (フェイルクローズ)
- `"owner/repo" in allowed_repos`チェックの結果

### 操作種別の分類

`classify_operation_type(tool_name)`は以下のいずれかを返す: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`。

分類の優先順位 (最初に一致したものが採用される):
1. `WRITE_TOOLS` → `OperationType.WRITE`
2. `DELETE_TOOLS` → `OperationType.DELETE`
3. 実行系ツール (`shell_run`) → `OperationType.EXECUTE`
4. API書き込みツール (github_*系ツール) → `OperationType.API_WRITE`
5. デフォルト → `OperationType.READ`

### リスク分類

優先順位: `approval_risk_rules`テーブル → `tool_safety_tiers`マッピング

#### ティア-リスク対応

| Tier | Risk level |
|---|---|
| `READ_ONLY` | `none` |
| `WRITE_SAFE` | `none` |
| `WRITE_DANGEROUS` | `medium` |
| `ADMIN` | `high` |

`tool_safety_tiers`に存在しないツールはデフォルトで`WRITE_DANGEROUS`となる (フェイルセーフ)。

| Risk level | Behavior |
|---|---|
| `none` | 自動承認 (プロンプトなし) |
| `medium` | プレビュー + `y/N`プロンプト |
| `high` | プレビュー + 完全な`yes`入力が必須 |

### リスクエスカレーション条件

- パスが`approval_protected_paths`に含まれる → `high`にエスカレート
- GitHubブランチが`approval_high_risk_branches` (デフォルト: main, master) に含まれる → `high`にエスカレート
- `gitops_force_push_blocked=True`かつ`force=True`引数 → 拒否
- `gitops_push_blocked=True` → すべてのGitHub書き込み操作を拒否

#### GitHub書き込みツール

`gitops_push_blocked`チェックで使用される7つのGitHub書き込みツール:

| Tool | Purpose |
|---|---|
| `github_push_files` | 複数ファイルをプッシュ |
| `github_create_or_update_file` | 単一ファイルを作成または更新 |
| `github_delete_file` | ファイルを削除 |
| `github_merge_pull_request` | PRをマージ |
| `github_create_pull_request` | PRを作成 |
| `github_update_pull_request` | PRを更新 |
| `github_create_branch` | ブランチを作成 |

`gitops_push_blocked=True`の場合、これらのツールはいずれもプロンプトなしで拒否される。

### ドライラン プレビュー

`approval_dry_run_tools` (デフォルト: write_file, edit_file, delete_file, delete_directory,
move_file) 内のツールは、承認プロンプト前に`dry_run=True`で事前実行される。結果はプレビューに追加される。

### 拒否時の処理

拒否されたツールはツール実行結果として`"Tool execution denied by user."`を受け取る (LLMには
toolロールメッセージとして返され、会話は自然に継続する)。

---

## プランモード

`/plan`は`ctx.conv.plan_mode`を切り替える。

- `True`の場合: `cfg.tool.plan_blocked_tools`内のツールは (プロンプトなしで) 自動拒否される
- デフォルトでブロックされるもの: `write_file`, `create_directory`, `delete_file`, `delete_directory`
- 目的: 破壊的操作を実行せずにLLMが推論・計画できるようにする

---

### `build_preview(tool_name, args)`

承認プロンプト前に表示される、人間が読める操作プレビューを構築する。

| Tool category | Preview format |
|---|---|
| `write_file`, `edit_file` | `{path}\n    content: {content[:200]}` |
| `delete_file`, `delete_directory`, `create_directory` | `{path or directory_path}` |
| `move_file` | `{source} → {destination}` |
| `shell_run` | `{command}` |
| `github_*` | `{owner}/{repo} {extra args JSON[:200]}` |
| その他のツール | `json.dumps(args)[:300]` |

### `TURN_LIMIT_HINT`

ターン単位の上限によりツール実行結果が破棄された場合に履歴に追加されるヒント。形式:

```
[Result omitted: per-turn tool result limit reached.]
```

このヒントは`tool_results_turn_max_chars` ([05_agent_08_01_configuration-loading-agent-config-part1.md](05_agent_08_01_configuration-loading-agent-config-part1.md) 参照) を超過した場合に追加される。

---

## ツール実行結果のキャッシュ

`ToolExecutor`はTTL + LRUキャッシュを維持する:

- キャッシュキー: JSONシリアル化されたツール名+引数 (プレーンな文字列、MD5化なし)
- 成功した結果 (`is_error=False`) のみキャッシュされる
- TTL: `tool_cache_ttl`秒 (デフォルト300)
- `tool_cache_max_size > 0`の場合LRU退避 (デフォルト200)
- キャッシュヒット時: 結果内で`request_id=""`
- `/clear`がキャッシュをクリアする
- キャッシュ統計: `/stats`で`Cache hits`として表示される

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`

## Keywords

approval flow
pre-flight checks
risk classification
plan mode
tool result cache
