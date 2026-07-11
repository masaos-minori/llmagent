---
title: "MCP Security and Safety Model: Authentication, Security Profiles, Output Limits and Sandboxing"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - authentication
  - sandboxing
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
source:
  - 04_mcp_05_security_and_safety_model.md
---

# MCP セキュリティと安全性モデル: 認証・セキュリティプロファイル・サンドボックス

## `read_only` フラグ（git-mcp）

```toml
read_only = true   # default: all write tools return [DENIED]
```

`true` の場合: `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` は全て承認の有無に関わらず
`[DENIED]` を返す。書き込みを有効にするには明示的に `false` を設定する。

---

## 認証（`auth_token`）

```toml
# In server config or McpServerConfig
auth_token = ""   # empty = no auth
```

空でない場合: サーバーは `Authorization: Bearer <token>` ヘッダーを要求する。
欠落または不一致 → HTTP 401。
適用対象: 全サーバー（`McpServerConfig.auth_token` によりサーバーごとに設定）。

**ローカル/開発環境の互換性:** `auth_token=""`（Bearer 認証なし）は意図的な
ローカル/開発環境の互換性のための挙動であり、見落としではない。**空の `auth_token` は
本番環境で使用してはならない** — これを拒否する起動時の強制については、
下記の [Security Profile](#security-profile-security_profile) を参照。

---

## セキュリティプロファイル（`security_profile`）

```toml
# In config/agent.toml [mcp_servers] section
security_profile = "local"   # or "production"
```

HTTP MCP サーバーに Bearer トークン認証が必須かどうかを制御する。

| プロファイル | 挙動 |
|---|---|
| `local`（デフォルト） | 認証は任意。HTTP サーバーで `auth_token` が欠落している場合、起動時に warning が出力される。 |
| `production` | 認証が必須。いずれかの HTTP サーバーに `auth_token` がない場合、起動は `RuntimeError` で失敗する。 |

**強制のポイント:** `agent/repl_health.py` の `audit_security_defaults()` は、`security_profile == "production"` かつ HTTP サーバーの `auth_token` が空の場合、起動時に例外を発生させる。また `shell_sandbox_backend == "none"` および空の `tool.allowed_tools` についても警告する。

**リロードの境界:** `/reload` はこのチェックを再実行することはなく、実行中の MCP サーバーに
`auth_token` の変更を適用することもない — トークンの変更は常に再起動が必要として
報告される（[Configuration: Hot-reload eligibility](05_agent_08_01_configuration-loading-agent-config-part1.md#config-file-ownership-and-hot-reload-eligibility) を参照）。
本番環境の認証検証は起動時にのみ実行される; これを弱めたり回避したりできるランタイムパスは存在しない。

**Audit API の分離:** `agent/security_audit_config.py` は、MCP サーバーの config モデル（`mcp_servers.shell.models`, `mcp_servers.git.models`, `mcp_servers.github.models_config`, `mcp_servers.cicd.models`）をインポートする、エージェント層における唯一の許可されたポイントである。4つの狭いスコープの DTO（`ShellAuditConfig`, `GitAuditConfig`, `GitHubAuditConfig`, `CicdAuditConfig`）と、オプションの依存関係（`ImportError` → `None`）および config 読み込み失敗（`Exception` → `RuntimeError`）を処理する4つのローダー関数を公開する。

---

## 出力とリソースの制限

| 上限 | デフォルト | サーバー |
|---|---|---|
| 最大レスポンスバイト数 | 512 KB（`MCP_MAX_RESPONSE_BYTES = 524288`） | 全サーバー（切り詰め） |
| shell 最大出力 | 4096 KB（config） | shell-mcp |
| shell 最大メモリ | 512 MB（`RLIMIT_AS`） | shell-mcp |
| shell 最大タイムアウト | 300秒（config） | shell-mcp |
| git_show 最大文字数 | 8000文字 | git-mcp |
| cicd ログ上限 | 256 KB / 5ジョブ | cicd-mcp |
| file 最大読み取り | 1 MB（config） | file-read-mcp |
| file 最大書き込み | 1 MB（config） | file-write-mcp |
| GitHub per_page | 100（config） | github-mcp |

---

## サンドボックスバックエンド（shell-mcp）

```toml
# Development:
shell_sandbox_backend = "none"    # WARNING at startup; no isolation
# Production:
shell_sandbox_backend = "firejail"  # RuntimeError at startup if binary missing
```

| バックエンド | 使用場面 | 本番環境で必要か | 起動時の挙動 |
|---|---|---|---|
| `firejail` | プロセス分離、制限されたファイルシステム | **必須** | バイナリ欠落時は RuntimeError |
| `none` | 開発専用 — 分離なし | No | WARNING をログ出力; 本番モードでは RuntimeError |

- `"firejail"`: argv の先頭に `["firejail", "--private", "--net=none", "--noroot", "--"]` を付加する
- `"none"`: サンドボックスなし; `RLIMIT_*` のリソース制限のみ適用

**起動時の強制**（plan 20260626-091916 で追加）:
- `backend == "firejail"` かつ `shutil.which("firejail")` が None を返す場合 → 起動時に `RuntimeError`
- `backend != "firejail"` かつ `backend != "none"` の場合 → 起動時に WARNING
- 本番モードで `backend == "none"` の場合 → `RuntimeError`

firejail のインストール: `sudo apt-get install firejail`（Debian/Ubuntu）または `apk add firejail`（Alpine）。
確認: `firejail --version`

**リソース制限**（`preexec_fn` 経由で適用）: `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_NOFILE`,
`RLIMIT_NPROC`, `RLIMIT_FSIZE`

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Keywords

mcp
security
safety-model
auth-token
security-profile
production
firejail
sandbox-backend
resource-limits
output-limits
