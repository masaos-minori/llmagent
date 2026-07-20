---
title: "MCP Security and Safety Model: Fail-Open vs Fail-Closed Summary, Dry-Run, Risk Tiers and AI Notes"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - fail-open-fail-closed
  - risk-tiers
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
---

# MCP セキュリティと安全性モデル: Fail-Open/Fail-Closed 要約・Dry-Run・リスクティア・AI 注記

## Fail-Open 対 Fail-Closed の要約

| 制御 | ポリシー | 空/未設定時の挙動 |
|---|---|---|
| `allowed_dirs`（file-read/write/delete-mcp） | Fail-closed | 全アクセスを拒否 |
| `allowed_dirs`（mdq-mcp） | Fail-closed | パスを受け取る全ツールを拒否（`MdqAuthorizationError`） |
| `allowed_repos`（github-mcp, fail_closed モード） | Fail-closed | 全書き込みを拒否 |
| `allowed_repos`（github-mcp, fail_open モード） | Fail-open | 全リポジトリを許可 |
| `allowed_repo_paths`（git-mcp） | Fail-closed | 全アクセスを拒否 |
| `repo_allowlist`（cicd-mcp） | Fail-closed | 全リポジトリを拒否 |
| `workflow_allowlist`（cicd-mcp） | **Fail-closed** | 全ワークフローを拒否 |
| `command_allowlist`（shell-mcp） | Fail-closed | 全コマンドを拒否 |
| `path_denylist`（github-mcp） | Fail-open（デフォルトでブロックなし） | 全パスを許可 |
| `protected_branches`（github-mcp） | Fail-open（デフォルトでブロックなし） | 全ブランチを許可 |

### 起動時の Audit

`agent/repl_health.py` の `audit_security_defaults()` はエージェント起動時に実行され、
セキュリティ姿勢の要約をログに出力する。各サーバーの config ファイルを読み込み、以下の設定をチェックする。

| 設定 | サーバー config ファイル | チェック内容 |
|---|---|---|
| `shell_sandbox_backend` | `shell_mcp_server.toml` | `"firejail"` + バイナリ欠落時は RuntimeError; `"firejail"` または `"none"` 以外の場合は WARNING; 本番環境で `"none"` の場合は RuntimeError |
| `command_allowlist` | `shell_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |
| `allowed_repo_paths` | `git_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |
| `workflow_allowlist` | `cicd_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |

空の allowlist に対する警告は以下の形式を使用する: `DENY-ALL detected: {setting} is empty. {server} will reject ALL requests from this category. Verify this is intentional or add allowed values to config.`

チェックの最後に、以下の要約行がログに出力される。

```
Security posture summary — fail-closed (deny when empty): <list>; fail-open (allow when empty): <list>
```

Fail-closed 設定が空であることは意図された安全なデフォルトである（アクセスが拒否される）。Fail-open
設定が空であることは、無制限のアクセスを許可してしまうため警告として強調される。

---

## Dry-Run のサポート

`dry_run=True`（副作用のない実行前プレビュー）をサポートするツール:

| サーバー | dry_run をサポートするツール |
|---|---|
| file-write-mcp | `write_file`, `edit_file`, `create_directory`, `move_file` |
| file-delete-mcp | `delete_file`, `delete_directory` |
| shell-mcp | `shell_run` (arg: `dry_run`) |
| git-mcp | `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| cicd-mcp | `trigger_workflow` |

**cicd-mcp の注記:** リポジトリとワークフローの allowlist チェックは、`handle_trigger_workflow` 内の `dry_run` バイパスよりも先に実行される。拒否対象のリクエストは `dry_run=True` であっても常に拒否される。

エージェントレベル: `config/agent.toml` の `approval_dry_run_tools` は、確認プロンプトを表示する前に
承認フローが自動で `dry_run=True` を実行するツールを列挙する。

---

## リスクティア分類

ツールのリスクティア（`config/agent.toml::tool_safety_tiers` から）:

| ティア | 例 | 承認方式 |
|---|---|---|
| `READ_ONLY` | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` | 自動承認 |
| `WRITE_SAFE` | `write_file`, `edit_file`, `git_add`, `git_commit` | `y/N` プロンプト |
| `WRITE_DANGEROUS` | `delete_file`, `shell_run`, `github_push_files`, `git_checkout`, `git_pull`, `git_push`, `trigger_workflow` | `yes`（フルワード）の入力が必要 |
| `ADMIN` | （カスタム; デフォルトでは未設定） | `yes` の入力が必要 |

`tool_safety_tiers` に記載のないツールは、デフォルトで `WRITE_DANGEROUS` として扱われる（フェイルセーフ）。

`tool_safety_tiers` のエントリは、実際に登録されたツール名でなければならない（サーバーキーではない）。起動時に双方向の検証が実行される。

- **ティアの欠落:** `tool_safety_tiers` に記載されていない登録済みツールがある場合、本番環境ではエラー（致命的な `RuntimeError`）、local/development では warning となる。
- **未知のキー:** `tool_safety_tiers` 内のキーが登録済みツール名でない場合、本番環境ではエラー（致命的な `RuntimeError`）、local/development では warning となる。

両方のチェックは、strict-key、safety-tier、allowed-tools の全ての検証を1回のパスに統合する `ProductionConfigValidator.validate()` を介して実行される。

---

## AI システムのための注記

1. **GitHub への書き込みアクセスを前提としないこと。** `allowed_repos` はデフォルトで空である（fail-closed）。
    GitHub への書き込みを試みる前に `allowed_repos` が設定されているか確認すること。

2. **シェルコマンドが実行されることを前提としないこと。** `command_allowlist` はデフォルトで空である。
    `shell_run` を試みる前に allowlist を確認すること。

3. **`allowed_repo_paths` が空 = git アクセス拒否。** git-mcp のツールを使用する前に設定すること。

4. **`workflow_allowlist` は fail-closed である**（`repo_allowlist` と同様）。空リストは全ての
    ワークフロートリガーを拒否する。`cicd_mcp_server.toml` で許可するワークフローを明示的に列挙すること。

5. **mdq-mcp は本番運用可能である。** FTS5 のインデックス化と検索は機能として実装済み。本番の RAG ワークロードには `rag-pipeline-mcp` を使用すること。指針については[04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary)を参照。

6. **破壊的操作の前に `dry_run=True` でプレビューすること。** エージェント内の承認フローは、
    ユーザープロンプトを表示する前に、登録済みツールに対して `dry_run=True` を自動的に注入する。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Keywords

mcp
security
safety-model
fail-open
fail-closed
dry-run
risk-tier
tool-safety-tiers
approval
ai-notes
