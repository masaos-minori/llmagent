# セキュリティ監査構成の読み込み失敗がローカルモードでチェックをスキップする

## Summary

PRODUCTIONモードで shell/github/cicd 構成の読み込みに失敗すると `RuntimeError` が発生し、エージェント起動がブロックされる（意図的な挙動）。ローカルモードでは警告のみで続行されるが、`shell_cfg is None` の場合は `command_allowlist` の空チェックがスキップされるため、シェルコマンドの allowlist チェックが行われない。

## Severity

High

## Confidence

High

## Evidence

- `agent/security_audit_config.py:58-60` — `load_shell_audit_config()` が `RuntimeError` を発生させる
- `agent/security_audit_config.py:73` — `load_git_audit_config()` が `RuntimeError` を発生させる
- `agent/security_audit_config.py:91-92` — `load_github_audit_config()` が `RuntimeError` を発生させる
- `agent/security_audit_config.py:105-106` — `load_cicd_audit_config()` が `RuntimeError` を発生させる
- `agent/repl_health.py:489-497` — `shell_cfg = None` の後、`sandbox_backend` チェックがスキップされる
- `agent/repl_health.py:525` — `shell_cfg.command_allowlist` の空チェックもスキップされる

## Current behavior

PRODUCTIONモードで構成ファイルが壊れていると起動できない（これは意図的な挙動）。ローカルモードで構成ファイルがない場合、シェルコマンドの allowlist チェックがスキップされる（安全側だが、意図しない挙動）。

## Impact

- ローカルモードで構成ファイルがない場合、シェルコマンドの allowlist チェックがスキップされる
- ユーザーは allowlist チェックが行われていないことに気づかない
- システムのセキュリティポリシー違反の可能性

## Recommended action

ローカルモードで構成ファイルがない場合、デフォルトの deny-all ポリシーを適用するか、明示的な警告メッセージを出す。

## Suggested Tests

- **Test target:** `agent/repl_health.py::audit_security_defaults()`
- **Behavior to verify:** ローカルモードで構成ファイルがない場合、deny-all ポリシーが適用されること
- **Failure mode:** 構成ファイルがない場合に allowlist チェックがスキップされ、すべてのシェルコマンドが許可される
