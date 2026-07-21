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

`classify_risk(cfg, tool_name, args)` (`agent/tool_policy.py`) はベースリスクを次の優先順位で決定する:

1. `approval_risk_rules[tool_name]` (明示ルール)
2. `tool_safety_tiers[tool_name]` (ティアマッピング)
3. `tool_constants.py`分類によるフォールバック: `DELETE_TOOLS`/`SHELL_TOOLS` → `high`、`WRITE_TOOLS` → `medium`、それ以外 → `medium` (デフォルト)

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

ベースリスクが`none`の場合、以降のオーバーライド・エスカレーション判定は行わずそのまま`none`を返す。

### 特例リスクオーバーライド (`_special_case_risk`)

ベースリスクが`none`以外の場合、以下がエスカレーション条件より先に評価され、該当すれば結果のリスクを直接置き換える (`agent/tool_policy.py`の`_special_case_risk()`):

| 条件 | Risk |
|---|---|
| `tool_name == "delete_directory"`かつ`args["recursive"]`が真 | `high` |
| 引数`force` / `overwrite` / `clobber`のいずれかが`True` | `high` |
| `tool_name == "shell_run"`かつ`command`が`approval_shell_safe_prefixes`のいずれかで始まる | `none` |
| `tool_name == "shell_run"`かつ上記に該当しない (または`command`が文字列でない) | `high` |

> **Explicit in code:** これらは「拒否」ではなく`RiskLevel`の上書きである。`high`となった場合は通常の承認プロンプト (完全な`yes`入力必須) に進み、実行が完全に拒否されるわけではない。

### リスクエスカレーション条件

特殊ケースリスク判定の後、以下がさらにエスカレーションとして評価される (パスまたはGitHubブランチによるエスカレーション。ベースリスクが既に`high`の場合はスキップ):

- パスが`approval_protected_paths`に含まれる → `high`にエスカレート
- GitHubブランチが`approval_high_risk_branches` (デフォルト: main, master) に含まれる → `high`にエスカレート

### gitops系フラグと承認フローの関係

- `gitops_push_blocked=True` → すべてのGitHub書き込み操作を拒否 (`check_approval()`冒頭、`_GITOPS_BLOCKABLE_TOOLS`に対して即時拒否。デフォルト`False`)。**Explicit in code。**

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

> **Note:** `github_create_issue`および`github_add_issue_comment`は共有のGitHubミューテーションセット（`_GITHUB_MUTATION_TOOLS = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS`）のメンバーであり、`OperationType.API_WRITE`分類やリポジトリ許可リストチェックで他で使用されているが、`gitops_push_blocked`のブロック対象からは**明示的に除外**されている。

### ドライラン プレビュー

`approval_dry_run_tools` (デフォルト: write_file, edit_file, delete_file, delete_directory,
move_file) 内のツールは、承認プロンプト前に`dry_run=True`で事前実行される。結果はプレビューに追加される。

### ドライラン失敗時のHIGHリスクツール拒否

ドライラン結果が`is_error=True`の場合、`RiskLevel.HIGH`のツールは`check_approval()`ですぐに拒否される（`denied_dry_run_error`、プロンプトなし）。

ドライランが`RuntimeError`または`OSError`を発生させた場合（サポートされていない操作 / 接続障害）、従来どおりテキストのみプレビューにフォールバックし、引き続きユーザーにプロンプトする。

> **Note:** この時点ではGitHubツールはデフォルトで`approval_dry_run_tools`に含まれていないため、このパスは現在 dormant であり、オペレーターがツールを選択した場合にのみ有効になる。

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

``` text
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

### スタンピード防止 (in-flight de-duplication)

`ToolExecutor._execute_with_stampede_protection()` (`shared/tool_executor.py`) は、同一キャッシュキー
(同一ツール名+引数) への並行呼び出しをin-flightの`Future`で共有し、実際の実行を1回に絞る。
先行呼び出しが例外を送出した場合、その例外は待機中のすべての呼び出し元に伝播する
(いずれかの呼び出しが無期限にハングすることはない)。

> **Explicit in code:** TTL/LRUキャッシュそのものとは別の仕組みであり、キャッシュミス時に同時に
> 発生した重複リクエストの二重実行を防ぐためのもの。

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
