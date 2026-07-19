---
title: "Agent Operations and Observability - Workflow Observability"
category: agent
tags:
  - agent
  - operations
  - workflow
  - otel-spans
  - session-diagnostics
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## OpenTelemetry (OTel)

`config/agent.toml` で設定する:

```toml
otel_enabled = true
otel_endpoint = ""          # "" = ConsoleSpanExporter (logs to agent.log)
otel_service_name = "llm-agent"
```

`otel_endpoint = ""` の場合: スパンは標準出力 / `agent.log` に書き込まれる。

```bash
# Extract span names from agent.log
tail -f /opt/llm/logs/agent.log | grep '"name":'
```

期待されるスパン:
```json
{"name": "compress", ...}
{"name": "llm", "attributes": {"model_url": "http://127.0.0.1:8080/..."}, ...}
{"name": "workflow.run", "attributes": {"workflow.task_id": "...", "workflow.version": "1.0"}, ...}
{"name": "workflow.stage", "attributes": {"workflow.stage_id": "execute", "workflow.attempt": 1}, ...}
```

---

## Workflow Observability(ワークフローの可観測性)

### OTel Spans(OTelスパン)

`WorkflowEngine` は、トレーサーが設定されている場合に4種類のスパンを発行する:

| Span name | 発行元 | Attributes |
|---|---|---|
| `workflow.run` | `WorkflowEngine.run()` | `workflow.task_id`, `workflow.version`, `workflow.workflow_id`, `workflow.session_id` |
| `workflow.stage` | `WorkflowEngine._run_stage()` | `workflow.stage_id`, `workflow.attempt`, `workflow.workflow_id` |
| `workflow.approval` | ワークフロー承認ゲート | `workflow.workflow_id`, `workflow.approval_id`, `workflow.approval_status` |
| `workflow.retry` | `WorkflowEngine._run_stage_with_retry()` | `workflow.workflow_id`, `workflow.task_id`, `workflow.stage_id`, `retry.attempt`, `retry.max_attempts`, `retry.error_type` |

上記3行(`workflow.stage`、`workflow.approval`、`workflow.retry`)は本表に未記載だったため追記。`workflow.approval` は承認ゲート通過時(既存approvalの再評価時)にも発行され、`workflow.retry` はリトライ可能なステージ(`stage_def.retryable == True`; デフォルト設定では`execute`のみ)が失敗しリトライ待機(`asyncio.sleep`)に入る直前に発行される(`workflow_engine.py`)。`_run_stage_with_retry()`は2026-07-17に、旧`_run_execute_with_retry()`を一般化したもの — `plan`/`execute`/`verify`すべてが同じ関数を経由し、`stage_def.retryable`に応じて単発実行かリトライループかが決まる(根拠: Explicit in code)。

トレーサーは `Orchestrator` → `WorkflowEngine` へと伝播するため、すべてのワークフロースパンは、それを包含する `llm` スパンと同じトレースコンテキストを共有する。補足: 実装上は `Orchestrator._handle_llm_turn()` が `llm` スパンを開始する呼び出しが `execute` ステージのコールバック(`execute_fn`)から呼ばれるため、`llm` スパンは `workflow.run` → `workflow.stage`(stage_id="execute")のネスト内の子スパンとして生成される。`workflow.approval` と `workflow.retry` は `llm` スパンとは別のタイミング(承認ゲート通過時・リトライ待機時)で発行される兄弟スパンである(根拠: Explicit in code, `orchestrator.py` の `_handle_llm_turn`/`_handle_workflow_engine` および `llm_turn_runner.py` の `_span_ctx`)。

### Workflow Identifiers(ワークフロー識別子)

ワークフローモードの各ターンでは、既存の `task_id` に加えて一意の `workflow_id`(UUID4)が生成される。両IDは以下を通じて伝播する:
- OTelスパン属性
- すべての監査ログイベント(`workflow_start`、`stage_completed`、`approval_requested`)
- `ToolApprovalEvent`、`ApprovalDecisionEvent`、`ToolExecEvent` のDTO
- `turn_end` 監査イベント
- `AgentContext` 内の `WorkflowState`(`ctx.workflow.workflow_id`)
- `workflow.sqlite` の `tasks` テーブル

### Audit Events(監査イベント)

3つのワークフロー固有イベントが、ターンごとに `audit.log` に追記される:

**`workflow_start` イベント**(タスク作成時に発行):
```json
{"event": "workflow_start", "task_id": "...", "workflow_id": "...", "session_id": "...", "workflow_version": "1.0", "ts": 1718600000.1}
```

**`stage_completed` イベント**(executeステージ完了後に発行):
```json
{"event": "stage_completed", "task_id": "...", "workflow_id": "...", "session_id": "...", "stage_id": "execute", "elapsed_ms": 1234.5, "ts": 1718600001.4}
```

**`approval_requested` イベント**(人間の承認が必要な場合に発行):
```json
{"event": "approval_requested", "task_id": "...", "workflow_id": "...", "session_id": "...", "approval_id": "...", "ts": 1718600001.5}
```

**`turn_end` イベント**(ワークフローコンテキストを含むよう更新):
```json
{"event": "turn_end", "task_id": "...", "workflow_id": "...", "session_id": "...", "elapsed_ms": 1234.5, ...}
```

実際には上記に加え `input_tokens`、`output_tokens`、`parse_error_count`、`heartbeat_timeout_count`、`reconnect_count`、`partial_completion`、`error_kind` も含まれる(orchestrator.py)(根拠: Explicit in code)。

補足: `workflow_start`、`stage_completed`、`approval_requested`、`tool_approval`、`approval_decision`、`tool_exec` の各イベントは、`ctx.services_required.audit_logger` が `None`(監査ロガー未設定)の場合はいずれも発行されない(早期return)。また `tool_approval`・`tool_exec` の各書き込み関数は、ワークフローコンテキスト外(`ctx.workflow.workflow_id` が未設定)で呼び出されるとassertion errorになる(`tool_audit.py`)(根拠: Explicit in code)。

### Reading workflow audit events(ワークフロー監査イベントの読み方)

```bash
# All workflow events
grep -E '"workflow_start"|"stage_completed"|"approval_requested"' /opt/llm/logs/audit.log | jq .

# Execute stage latency grouped by workflow_id
grep '"stage_completed"' /opt/llm/logs/audit.log | jq '{workflow_id, task_id, stage_id, elapsed_ms}'

# Pending approvals with workflow context
grep '"approval_requested"' /opt/llm/logs/audit.log | jq '{workflow_id, task_id, approval_id}'

# All events for a specific workflow_id
grep '"workflow_id":"<id>"' /opt/llm/logs/audit.log | jq .
```

### Session Diagnostics(セッション診断)

診断情報は `DiagnosticStore.save()` を通じて `session_diagnostics` テーブルに永続化される。セッション概要はセッション終了時に書き込まれる:

```json
{
  "session_id": "...",
  "turns": 5,
  "workflow_count": 3,
  "task_count": 3,
  "approval_events": 1,
  "retry_count": 2,
  "artifacts": ["path/to/artifact"],
  ...
}
```

これらの件数は、セッション終了時に `workflow.sqlite` から導出される。

実装上の `session_summary` は、上記フィールドに加えて `session_id`、`timestamp`、`turns`、`tool_calls`、`tool_errors`、`partial_completions`、`parse_errors`、`heartbeat_timeouts`、`reconnects`、`semantic_cache_hits`、`input_tokens`、`output_tokens`、`compress_count`、`fallback_truncate_count`、`latency_summary`、`rag_query_count`、`rag_stage_outcomes` も含む、ワークフロー以外の実行統計全般を含む単一のサマリーである(`repl.py` の `_persist_session_diagnostics()`)(根拠: Explicit in code)。

`workflow_count` は `tasks` テーブルの `session_id` 一致行のうち `workflow_id IS NOT NULL` な行を `COUNT(DISTINCT workflow_id)` で集計、`task_count` は同条件の行数、`approval_events` は `approvals` テーブルの件数、`retry_count` は `attempts` テーブルで `stage_id='execute'` の件数から `task_count` を差し引いた値(0未満は0に丸め)である(根拠: Explicit in code)。

`DiagnosticStore.save()` は `workflow_id` と `task_id` を受け取れる引数を持つが(`session_diagnostics` テーブルにも同名カラムが存在)、`_persist_session_diagnostics()` からの `session_summary` 保存時にはこれらは指定されず、`workflow_id`/`task_id` はワークフロー単位ではなくJSON化された `content` 内の集計値としてのみ記録される(根拠: Explicit in code)。

セッション診断のクエリ:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC LIMIT 10;"
```

特定の診断エントリの取得:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE session_id = ? AND kind = 'session_summary' ORDER BY created_at DESC LIMIT 1;" | jq .content
```

あるセッションの全診断種別の一覧表示:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT DISTINCT kind FROM session_diagnostics WHERE session_id = ? ORDER BY kind;"
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

OTel spans
workflow identifiers
audit events
session diagnostics
