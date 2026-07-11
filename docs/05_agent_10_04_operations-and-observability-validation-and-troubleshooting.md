---
title: "Agent Operations and Observability - Validation and Troubleshooting"
category: agent
tags:
  - agent
  - operations
  - startup-validation
  - mcp-reload
  - troubleshooting
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Workflow Startup Validation(ワークフロー起動時検証)

エージェントは、オーケストレータを初期化する前に、ワークフロー定義ファイルが存在することを
無条件に検証する — これを無効化・縮退させる設定は存在しない
(2026-07-09に確認済み: `workflow_mode` は有効な設定キーではない — 詳細は
[Configuration: AgentConfig Structure](05_agent_08_01_configuration-loading-agent-config-part1.md#agentconfig-structure) を参照)。
ファイルが存在しない場合、実用的なガイダンスを伴う `RuntimeError` が発生する。

**期待されるパス:** `config/workflows/default.json`

**対処方法:** 期待されるパスにワークフロー定義をデプロイすること。このチェックをスキップする
設定トグルは存在しない — 以前 `workflow_mode = "disabled"` や `"auto"` を設定していた設定ファイルは、
ワークフローチェックに到達する前に、設定読み込みそのものが完全に失敗する
(`workflow_mode` が拒否キーであるため `ConfigLoadError` となる)。

このプリフライトチェック(`agent/startup.py` の
`StartupOrchestrator._check_workflow_definition()`。`agent/repl_health.py` の
`check_workflow_definition()` をラップ)は `Orchestrator.__init__()` の前に実行され、
期待されるファイルパスを含まない可能性のある分かりにくい `WorkflowLoadError` ではなく、
明確なエラーメッセージを生成する。`Orchestrator.__init__()` 自体も、プリフライトチェックを
通過した後に `WorkflowLoader().load()` が何らかの理由で失敗した場合、無条件に `RuntimeError` を発生させる。

For the exact validation rules applied, see
[05_agent_03_03 §ワークフローローダーの検証ルール](05_agent_03_03_turn-processing-flow-workflow-engine-part1.md).

**注記:** この検証は常にエージェント起動時に一度だけ実行される — これは設定項目ではなく、
`/reload` で変更することはできない。修正するには、ワークフロー定義ファイルをデプロイして
エージェントを再起動する必要がある。

See also: [workflow_schema_version and schema version mismatch recovery](90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md).

---

## Workflow Deployment Runbook

Workflow is a **mandatory** deployment artifact — there is no config setting, environment
variable, or deploy flag to disable or bypass it. Every failure mode below has a concrete
recovery path; none of them involve "turning workflow off."

### Quick validation commands

```bash
# Validate a workflow definition file directly (does not start any service)
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json

# Check workflow DB schema tables and version (against the deployed DB)
sqlite3 /opt/llm/db/workflow.sqlite ".tables"
sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM workflow_schema_version ORDER BY applied_at DESC;"
```

### Missing `config/workflows/default.json`

**Symptom:** `deploy.sh` prints `[FATAL] Missing required workflow definition: config/workflows/default.json` and exits before copying anything.

**Recovery:**
```bash
git checkout HEAD -- config/workflows/default.json   # restore from version control
bash deploy/deploy.sh                                 # re-run deployment
```

### Invalid workflow JSON (parse error)

**Symptom:** `deploy.sh` (or the validator CLI directly) prints `[FATAL] Invalid workflow definition ...: <JSON parse error>`.

**Recovery:** Fix the reported JSON syntax error, then re-validate before re-deploying:
```bash
PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json
```

### Missing required stages

**Symptom:** The validator reports `required stages missing: <names>`.

**Recovery:** Ensure the workflow definition's `stages` array includes objects with `id` values `plan`, `execute`, and `verify` (each also carrying `description`, `timeout_sec`, `retryable`).

### Invalid retry policy

**Symptom:** The validator reports one of: `retry_policy.max_attempts must be >= 1`, `retry_policy.backoff must be one of: exponential, fixed`, or `retry_policy.backoff_sec must be >= 0`.

**Recovery:** Correct the named `retry_policy` field per the message, then re-validate.

### Missing or incomplete `workflow.sqlite`

**Symptom:** `init_db.sh` or `setup_services.sh` prints `[FATAL] Workflow database schema is missing or incomplete.` naming one or more missing tables.

**Recovery:**
```bash
bash deploy/init_db.sh   # (re-)creates workflow.sqlite; safe to re-run (idempotent)
```

### Schema version mismatch

**Symptom:** Agent startup or `setup_services.sh` reports `Workflow schema version mismatch: expected <X>, found <Y>`.

**Recovery:**
```bash
bash deploy/init_db.sh   # applies pending migrations and records the current version
```

### Workflow definition update requires a restart

**Symptom:** A new `config/workflows/default.json` was deployed, but the running agent does not pick it up.

**Explanation:** The workflow definition is validated and loaded exactly once, at agent boot (`StartupOrchestrator._check_workflow_definition()` in `agent/startup.py`, then `Orchestrator.__init__()`). It is **not** a hot-reloadable setting — `/reload` does not apply to it.

**Recovery:** Deploy the new definition (`deploy.sh`), then fully restart the agent process. There is no partial-update path.

---

## MCP Server Reload and Restart Semantics(MCPサーバのリロードと再起動のセマンティクス)

**注記:** MCPサーバ定義(`transport`、`url`、`startup_mode`、
`healthcheck_mode`、`call_timeout_sec`、`startup_timeout_sec`、`tool_names`、
`auth_token`、`role`、`cmd`、`env`)は再起動時点のスナップショットである。`/reload`
は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告する
(`[RESTART] - mcp/<server>.<field>`)が、稼働中のプロセスには一切適用しない。
`/mcp` / `/mcp status` は常に稼働中(再起動前)のサーバ設定を反映し、保留中の
`/reload` の変更は反映しない。ウォッチドッグによる再起動(`watchdog_loop()`)は、
失敗したサブプロセスを*現在*の起動設定で再起動する — これはヘルス駆動の復旧であり、
設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。
変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

**注記:** MCPサーバ定義(`transport`、`url`、`startup_mode`、
`healthcheck_mode`、`call_timeout_sec`、`startup_timeout_sec`、`tool_names`、
`auth_token`、`role`、`cmd`、`env`)は再起動時点のスナップショットである。`/reload`
は `[mcp_servers.*]` の変更を検出し、再起動が必要な変更として報告する
(`[RESTART] - mcp/<server>.<field>`)が、稼働中のプロセスには一切適用しない。
`/mcp` / `/mcp status` は常に稼働中(再起動前)のサーバ設定を反映し、保留中の
`/reload` の変更は反映しない。ウォッチドッグによる再起動(`watchdog_loop()`)は、
失敗したサブプロセスを*現在*の起動設定で再起動する — これはヘルス駆動の復旧であり、
設定リロードではないため、保留中のMCPサーバ定義の変更も適用されない。
変更されたMCPサーバ定義が適用されるのは、エージェントの完全な再起動時のみである。

---

## Interpreting `/context`(`/context` の解釈)

```
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  System preview  : '...'
  Token estimate  : 1,080 (chars / 4)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
   history       :    1,987 chars ( 62%)
```

- **Remaining:** `context_char_limit` までの残り距離 → 圧縮のトリガー
- **Token estimate:** `/tokenize` エンドポイントが設定されていない限り `文字数 / 4`
- **Token limit:** `context_token_limit` が未設定の場合は `disabled`。`context_token_limit` が設定されている場合は `200,000 tokens`(または設定値)を表示
- **Memory layer:** `use_memory_layer=True` の場合は `enabled (entries=N)`

---

## Interpreting `/stats`(`/stats` の解釈)

```
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** ストリーミング途中で中断されたLLM応答が記録される。詳細は `session_diagnostics`(`kind=partial_completion`)を確認すること。正式な部分完了モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)
- **HB timeouts:** SSEハートビートタイムアウト(LLMの過負荷の可能性)
- **Cache hits:** ツール結果キャッシュのヒット数
- **Approval pending:** `Approval: PENDING — use /approve or /reject` の行は、`ctx.workflow.approval_pending=True` の場合のみ表示される。ワークフロータスクが `/approve` または `/reject` の入力を待機している場合に表示される。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

workflow startup validation
MCP server reload
/context
/stats
partial completion
troubleshooting
