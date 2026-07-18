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

- [ ] `tool_definitions_strict = true` (デフォルトは `false`; スキーマ不整合時に致命的エラーとするには本番で明示的に有効化)
- [ ] `routing_drift_strict = true`(ルーティングのドリフト発生時に致命的エラーとする)
- [ ] `serial_tool_calls = false`(デフォルト; DAGスケジューリングが常時有効になる。`true`はレガシーな逐次/並列判定モードに切り替える。`use_tool_dag`という設定フィールドは存在しない — [05_agent_08_03](05_agent_08_03_configuration-tools-memory.md#toolconfig-cfgtool)参照)
- [ ] `allowed_tools`が明示的に設定されている(空 = すべてのツールを許可;ホワイトリストにすべき)
- [ ] 登録済みのすべてのツールが`tool_safety_tiers`にエントリを持つ(ティア欠落 → 本番では致命的エラー)
- [ ] `tool_safety_tiers`に未知のキーがない(未知のキー → 本番では致命的エラー)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"`(`"none"`ではない)であり、firejailバイナリがインストールされている
- [ ] `cicd-mcp`: `workflow_allowlist`が明示的に設定されている(空 = startup時に RuntimeError/CicdAuthorizationError で起動失敗する。fail-closed動作)
- [ ] `config/agent.toml`で`security_profile = "production"`(起動時の強制チェックを有効化する)
- [ ] ヘルスチェックのしきい値(`startup_timeout_sec`、`McpServerHealthRegistry.failure_threshold`)を見直し済み
- [ ] MCP watchdog(自動ヘルスポーリング＋自動再起動ループ)は2026-07-16に削除された。subprocessモードのMCPサーバーがクラッシュした場合の復旧は、次回のtool dispatch時の`ensure_ready()`による再起動試行、またはエージェントプロセス自体の手動再起動に限られる — 外部のプロセス監視(systemd等)による死活監視・再起動運用を用意しておくこと
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

fail-open/closedポリシーの全体表については`04_mcp_05_01_access-control-and-allowlists.md`を参照。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
