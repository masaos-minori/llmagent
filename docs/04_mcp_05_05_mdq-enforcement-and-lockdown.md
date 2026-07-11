---
title: "MCP Security and Safety Model: MDQ/RAG Boundary Enforcement, Fail-Open/Fail-Closed Defaults and Deny-All Lockdown"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - mdq
  - rag
  - lockdown
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_04_mdq-rag-boundary.md
source:
  - 04_mcp_05_security_and_safety_model.md
---

# MCP セキュリティと安全性モデル: MDQ/RAG 境界の強制と Fail-Open/Fail-Closed・Deny-All ロックダウン

### 境界の強制

自動化された pytest チェック（`tests/test_mdq_rag_boundary.py`）が、CI 実行ごとに MDQ/RAG の
境界を検証する。エージェント層における、禁止されたクロス DB 参照および許可されない直接 SQLite アクセスを
ソースファイル内でスキャンする。

#### 許可されたアクセスパス

| 層 | DB | 機構 | コンテキスト |
|---|---|---|---|
| `mcp/mdq/` | `mdq.sqlite` | 自身のサービス | 通常運用 |
| `scripts/mcp_servers/rag_pipeline/` | `rag.sqlite` | 自身のサービス | 通常運用 |
| エージェント層 | `session.sqlite` | `SQLiteHelper("session")` | 通常運用 |
| エージェント層 | `workflow.sqlite` | `SQLiteHelper("workflow")` | 通常運用 |
| エージェント層 | `rag.sqlite` | `RagMaintenanceService` 経由の `SQLiteHelper("rag")` | 管理者専用の `/db` コマンド |

#### 禁止されたアクセスパス

| 層 | DB | 理由 |
|---|---|---|
| `mcp/mdq/` | `rag.sqlite` | クロス DB 依存 |
| `scripts/mcp_servers/rag_pipeline/` | `mdq.sqlite` | クロス DB 依存 |
| エージェント層（通常時） | `mdq.sqlite` または `rag.sqlite` | 直接 DB アクセスではなく MCP ツールを使用すること |

#### 誤検知への対応

新しい管理者向け保守ファイルが `rag.sqlite` への直接アクセスを必要とする場合は、そのファイル名を
`tests/test_mdq_rag_boundary.py` の `ALLOWED` セットに追加し、その例外を上記の許可パス表に
記載すること。`ALLOWED` への変更には PR での設計レビューコメントが必要である。

---

### 既知の課題

- MDQ-02: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は未実装 — BM25 とベクトルモードのみ利用可能。

---

## Fail-open 対 Fail-closed のデフォルト

「Fail-closed」とは、リストが空の場合にその設定がアクセスを拒否することを意味する。
「Fail-open」とは、リストが空の場合にその設定が全アクセスを許可することを意味する。

| サーバー | 設定 | デフォルト | 空の場合の挙動 |
|---|---|---|---|
| shell-mcp | `command_allowlist` | `[]` | **Fail-closed** — 全シェルコマンドを拒否 |
| git-mcp | `allowed_repo_paths` | `[]` | **Fail-closed** — 全リポジトリアクセスを拒否 |
| github-mcp | `allowed_repos` | `[]` | **Fail-closed** — 全 GitHub 書き込み操作を拒否 |
| cicd-mcp | `workflow_allowlist` | `[]` | **Fail-closed** — 全ワークフロートリガーを拒否 |

### 本番デプロイ前に確認すべき危険なデフォルト値

- `shell-mcp`: `sandbox_backend = "none"`（デフォルト）は OS レベルのサンドボックスがないことを意味する。
  本番環境では `"firejail"` を設定すること; `/health` レスポンスで確認可能。
- `cicd-mcp`: `workflow_allowlist = []` は fail-closed（全拒否）である; 許可するワークフローを明示的に列挙すること。
- `github-mcp`: `allow_force_push = false`（デフォルト）; `require_pr_review = true`（デフォルト）。

### 起動時の audit

  `agent/repl_health.py` の `audit_security_defaults()` は起動時に実行され、以下をログに記録する。
- 空である全ての fail-closed 設定（情報提供 — アクセスは正しく拒否されている）
- 空である全ての fail-open 設定（警告 — 意図しないアクセスが許可される可能性がある）
- 要約行: `Security posture summary — fail-closed (...): ...; fail-open (...): ...`

---

## 意図的な deny-all ロックダウン

空の fail-closed allowlist は、MCP サーバーの操作カテゴリ全体を無効化する。
これは、特定のツールカテゴリを完全に禁止したいセキュリティ制限付きデプロイメント
（例: シェルコマンド禁止、DB クエリ禁止）における正しい挙動である。

### deny-all を引き起こす設定

| 設定 | サーバー | 空の場合の効果 |
|---------|--------|-------------------|
| `shell.command_allowlist` | shell-mcp | 全シェルコマンドを拒否 |
| `git.allowed_repo_paths` | git-mcp | 全 git 操作を拒否 |
| `github.allowed_repos` | github-mcp | 全リポジトリアクセスを拒否 |

### 意図的なロックダウンの設定方法

1. 該当する TOML で、対象の allowlist を空に設定する。
   ```toml
   # shell_mcp_server.toml
   command_allowlist = []   # deny all shell commands
   ```

2. 起動時の警告を抑制するため、`config/agent.toml` でロックダウンを明示的に認める。
   ```toml
   [agent]
   security_lockdown_enabled = true
   ```

3. エージェントを再起動する。起動ログには以下が表示される。
   ```
   INFO Security: security_lockdown_enabled=True — deny-all warnings suppressed
   ```

### ランタイムでの deny-all 状態の確認

起動時、`audit_security_defaults()` は各 deny-all 状態をログに記録する。
```
WARNING DENY-ALL detected: shell.command_allowlist is empty. shell-mcp will
        reject ALL shell commands. Verify this is intentional or add allowed
        commands to shell_mcp_server.toml.
```

`security_lockdown_enabled=False`（デフォルト）の場合、これらの警告は起動ごとに
表示される — これは config を見直すよう促す意図的なリマインダーである。deny-all の状態が
意図的であると確認できた場合にのみ `true` に設定すること。有効化した場合:
- fail-closed 設定（`command_allowlist`, `db_allowlist`, `allowed_repo_paths`）に対する DENY-ALL 警告は抑制される
- fail-open の警告（`tool.allowed_tools`）は引き続き表示される
- セキュリティ姿勢の要約行は詳細情報付きで引き続き表示される

### ロックダウンの解除

該当する TOML に許可値を戻し、
`security_lockdown_enabled = false` を設定する。適用するにはエージェントを再起動すること。

---

## Fail-Open / Fail-Closed 設定のレビュー

| 設定 | デフォルト | fail-open 時の挙動 | 本番環境での推奨 |
|---|---|---|---|
| `tool_definitions_strict` | `true` | `false` = スキーマ不一致が WARNING に格下げされる | `true` を維持する |
| `shell_sandbox_backend` | `"none"` | `"none"` = OS 分離なし | 本番環境では `"firejail"` を設定する |
| `workflow_allowlist`（cicd-mcp） | `[]` | `[]` = 全トリガーを拒否（fail-closed） | 許可するワークフローを明示的に列挙する |
| `command_allowlist`（shell-mcp） | `[]` | `[]` = 全コマンドを拒否（fail-closed） | 許可するコマンドを列挙する |
| `mcp_watchdog_interval` | `0`（local） / `30.0`（prod） | `0` = 自動再起動なし | 本番環境では `30.0` を使用する |

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`

## Keywords

mcp
security
safety-model
mdq-rag-boundary-enforcement
deny-all
lockdown
fail-open
fail-closed
security-audit
