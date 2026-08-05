---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
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

# Long-Running HTTP Operation (startup_mode=subprocess)

Agentは起動時にuvicornを起動し、`startup_timeout_sec` まで0.5秒ごとに `/health` をポーリングする。
ヘルスチェックが一度も成功しない場合は `RuntimeError` となる。

この `RuntimeError` は `security_profile`(`scripts/shared/mcp_config.py` の `SecurityProfile`)によって扱いが異なる。`security_profile=production` の場合、再試行(`HEALTH_CHECK_RETRY_DELAY_SEC` の遅延を挟んだ1回)後も失敗すると `RuntimeError` が捕捉されずに伝播し、Agentプロセス全体が終了する。`security_profile=local` の場合は同じ失敗が警告としてログ・表示されるのみで、当該サーバは無効化されるが、Agentプロセスおよび他のMCPサーバは動作を継続する。ヘルスチェック自体は `scripts/agent/http_lifecycle.py` の `/health` ポーリング(`HttpStartupError`)に由来し、`scripts/agent/startup.py` が上記のsecurity_profile依存の分岐を適用する。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
