---
title: "Agent Operations and Observability - Validation and Troubleshooting (Part 1)"
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
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
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
設定トグルは存在しない — ワークフロー必須であり、ワークフロー定義なしでの起動はできない。

このプリフライトチェック(`agent/startup.py` の
`StartupOrchestrator._initialize()`。`agent/repl_health.py` の
`check_workflow_definition()` をラップ)は `Orchestrator.__init__()` の前に実行され、
期待されるファイルパスを含まない可能性のある分かりにくい `WorkflowLoadError` ではなく、
明確なエラーメッセージを生成する。`Orchestrator.__init__()` 自体も、プリフライトチェックを
通過した後に `WorkflowLoader().load()` が何らかの理由で失敗した場合、無条件に `RuntimeError` を発生させる。

**補足(起動シーケンス):** `StartupOrchestrator._initialize()` の実際の呼び出し順は
`_init_command_registry()` → `_check_workflow_definition()` → `_check_workflow_schema()` →
`_init_orchestrator()` である。つまりワークフロー定義ファイルの存在検証
(`check_workflow_definition()`)の直後に、`workflow.sqlite` の必須テーブル・必須カラム・
`workflow_schema_version` の一致を検証する `check_workflow_schema()`(`agent/repl_health.py`)が
同じ `_initialize()` 内で連続実行され、いずれも `Orchestrator.__init__()` より前に完了する。
どちらも失敗時は `RuntimeError` を送出し、`StartupOrchestrator.run()` 側で捕捉されずに
起動そのものを中断させる(根拠: Explicit in code)。

**補足(`Orchestrator.__init__()` のエラーメッセージ):** `WorkflowLoader().load()` が
`WorkflowLoadError` または任意の例外を送出した場合、`Orchestrator.__init__()` は
`f"[workflow] WorkflowLoader failed: {exc}. Expected definition at: {WORKFLOWS_DIR / 'default.json'}."`
という書式で `RuntimeError` を再送出する。期待パスは常にメッセージに含まれる
(根拠: Explicit in code)。

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

> **矛盾(要修正):** 上記の `retry_policy.backoff must be one of: exponential, fixed` というメッセージ例は現在の実装と一致しない。
> `scripts/agent/workflow/workflow_loader.py` の `_SUPPORTED_BACKOFF` は `{"fixed"}` のみを定義しており、
> `"exponential"` は現時点でサポート対象に含まれない。実際に発生するメッセージは
> `retry_policy.backoff must be one of: fixed` である。`backoff` に `"exponential"` を指定した場合も
> この同じメッセージで拒否される(根拠: Explicit in code)。

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

**Explanation:** The workflow definition is validated and loaded exactly once, at agent boot (`StartupOrchestrator._initialize()` in `agent/startup.py`, then `Orchestrator.__init__()`). It is **not** a hot-reloadable setting — `/reload` does not apply to it.

**Recovery:** Deploy the new definition (`deploy.sh`), then fully restart the agent process. There is no partial-update path.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`

## Keywords

workflow startup validation
MCP server reload
/context
/stats
partial completion
troubleshooting
retry_policy.backoff
workflow_schema_version
check_workflow_schema
