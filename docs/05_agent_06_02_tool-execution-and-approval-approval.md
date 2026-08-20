---
title: "Agent Tool Execution and Approval - Approval Flow"
category: agent
tags:
  - agent
  - tool-execution
  - approval-flow
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_06_02_tool-execution-and-approval-approval.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

承認フローの設計判断、リスク分類、計画モードについて文書化する。

**注意**: このドキュメントは**事前実行承認**（ツールレベル）のみを対象とする。**事後実行承認**（ワークフローレベル）については[05_agent_06_04_tool-execution-and-approval-canonical.md](05_agent_06_04_tool-execution-and-approval-canonical.md)を参照。

## Design Intent

### 事前チェック（即時拒否）

1. **`allowed_tools`ホワイトリスト**: リストが空でなく、ツールがリストに含まれない場合 → 拒否
2. **`allowed_root`ルートジェイル**: パス引数が`cfg.allowed_root`外の場合 → 拒否
3. **GitHubリポジトリの許可リスト**: 書き込み操作対象のリポジトリが`approval_github_allowed_repos`に含まれない場合 → 拒否 (**フェイルクローズ**)

### 操作種別の分類

`classify_operation_type(tool_name)`は以下のいずれかを返す: `READ`, `WRITE`, `DELETE`, `EXECUTE`, `API_WRITE`

### リスク分類の設計判断

`classify_risk(cfg, tool_name, args)`はベースリスクを次の優先順位で決定する:

1. `approval_risk_rules[tool_name]` (明示ルール)
2. `tool_safety_tiers[tool_name]` (ティアマッピング)
3. `tool_constants.py`分類によるフォールバック: `DELETE_TOOLS`/`SHELL_TOOLS` → `high`、`WRITE_TOOLS` → `medium`、それ以外 → `medium` (デフォルト)

**Design judgment**: `tool_safety_tiers`に存在しないツールはデフォルトで`WRITE_DANGEROUS`となる (**フェイルセーフ**)

#### ティア-リスク対応

| Tier | Risk level |
|---|---|
| `READ_ONLY` | `none` |
| `WRITE_SAFE` | `none` |
| `WRITE_DANGEROUS` | `medium` |
| `ADMIN` | `high` |

#### Risk level の振る舞い

| Risk level | Behavior |
|---|---|
| `none` | 自動承認 (プロンプトなし) |
| `medium` | プレビュー + `y/N`プロンプト |
| `high` | プレビュー + 完全な`yes`入力が必須 |

**Design judgment**: ベースリスクが`none`の場合、以降のオーバーライド・エスカレーション判定は行わずそのまま`none`を返す

### 特例リスクオーバーライド

ベースリスクが`none`以外の場合、以下がエスカレーション条件より先に評価され、該当すれば結果のリスクを直接置き換える:

| 条件 | Risk |
|---|---|
| `delete_directory`かつ`recursive=True` | `high` |
| 引数`force` / `overwrite` / `clobber`のいずれかが`True` | `high` |
| `shell_run`かつ`command`が`approval_shell_safe_prefixes`のいずれかで始まる | `none` |
| `shell_run`かつ上記に該当しない | `high` |

**Note**: これらは「拒否」ではなく`RiskLevel`の上書きである。`high`となった場合は通常の承認プロンプトに進み、実行が完全に拒否されるわけではない。

### リスクエスカレーション

特殊ケースリスク判定の後、以下がさらにエスカレーションとして評価される:

- パスが`approval_protected_paths`に含まれる → `high`にエスカレート
- GitHubブランチが`approval_high_risk_branches`に含む → `high`にエスカレート

### gitops系フラグ

- `gitops_push_blocked=True` → すべてのGitHub書き込み操作を拒否（**フェイルクローズ**）

### ドライラン プレビュー

- `approval_dry_run_tools`内のツールは、承認プロンプト前に`dry_run=True`で事前実行
- ドライラン結果が`is_error=True`の場合、`RiskLevel.HIGH`のツールはすぐに拒否される

### 拒否時の処理

拒否されたツールはツール実行結果として`"Tool execution denied by user."`を受け取る。

## プランモード

`/plan`は`ctx.conv.plan_mode`を切り替える:

- `True`の場合: `cfg.tool.plan_blocked_tools`内のツールは (プロンプトなしで) 自動拒否される
- デフォルトでブロックされるもの: `write_file`, `create_directory`, `delete_file`, `delete_directory`

**Design judgment**: 破壊的操作を実行せずにLLMが推論・計画できるようにする

## Responsibility Boundary

- **正典**: `agent/tool_policy.py`
- **プレビュー形式**: コード参照（機械的詳細のため省略）

## Key Constraints

- フェイルクローズ: GitHubリポジトリの許可リスト、gitops_push_blocked
- フェイルセーフ: `tool_safety_tiers`未定義ツールは`WRITE_DANGEROUS`
- ベースリスク`none`はエスカレーションをスキップ

## Operational Notes

- 不明

## Known Limitations

- GitHubツールはデフォルトで`approval_dry_run_tools`に含まれていないため、このパスは現在dormant

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`
- `00_security_02_high-risk-tool-common-policy.md` — 高リスクMCPツール共通ポリシー (承認-リスクティアマッピング)

## Keywords

approval flow
risk classification
plan mode
tool result cache
