---
title: "Pre-Production Fail-Open Checklist"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Pre-Production Fail-Open Checklist

## 本番投入前フェイルオープン確認チェックリスト

本番環境へのデプロイ前に、以下を確認する。

- [ ] `tool_definitions_strict = true`(スキーマ不整合時に致命的エラーとする)
- [ ] `routing_drift_strict = true`(ルーティングのドリフト発生時に致命的エラーとする)
- [ ] `plugin_strict = true`(プラグインエラー時にfail-fastとする)
- [ ] `use_tool_dag = true`(DAGスケジューリング;`false`はレガシーな非本番動作)
- [ ] `allowed_tools`が明示的に設定されている(空 = すべてのツールを許可;ホワイトリストにすべき)
- [ ] 登録済みのすべてのツールが`tool_safety_tiers`にエントリを持つ(ティア欠落 → 本番では致命的エラー)
- [ ] `tool_safety_tiers`に未知のキーがない(未知のキー → 本番では致命的エラー)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"`(`"none"`ではない)であり、firejailバイナリがインストールされている
- [ ] `cicd-mcp`: `workflow_allowlist`が明示的に設定されている(空 = fail-closed: すべて拒否)
- [ ] `config/agent.toml`で`security_profile = "production"`(起動時の強制チェックを有効化する)
- [ ] `mcp_watchdog_interval = 30.0`(自動再起動が有効)
- [ ] ヘルスチェックのしきい値(`startup_timeout_sec`、`mcp_watchdog_max_restarts`)を見直し済み
- [ ] 監査ログのパスが設定され、書き込み可能である
- [ ] APIキー(`github_token`、`auth_token`)が環境変数経由で設定されており、設定ファイルにハードコードされていない
- [ ] `cicd_mcp_server.toml`の`repo_allowlist`が空でない(空 = すべてのリポジトリを拒否)
- [ ] `github_mcp_server.toml`の`allowed_repos`が空でない(空 = すべてのGitHub書き込み操作を拒否)

### firejailのインストール

```bash
# Debian/Ubuntu
sudo apt-get install firejail

# Alpine
apk add firejail

# Verify installation
firejail --version
```

インストール後、`config/shell_mcp_server.toml`を更新する。

```toml
shell_sandbox_backend = "firejail"
```

fail-open/closedポリシーの全体表については`04_mcp_05_security_and_safety_model.md`を参照。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
