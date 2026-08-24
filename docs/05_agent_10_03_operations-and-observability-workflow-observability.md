---
title: "Agent Operations and Observability - Workflow Observability"
area: agent
tags:
  - agent
  - operations
  - workflow-observability
  - tracing
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Purpose

Documents observability (spans, status, state transitions) during workflow execution.

## Design Intent

Workflow observability is divided into three layers:

1. **OTel Spans** — Records execution time, errors, and metadata for each workflow stage. Span names follow the `workflow.{stage}` pattern.
2. **Audit Logs** — Outputs `turn_start`/`turn_end` and workflow-specific events (`workflow_start`, `stage_completed`, `approval_requested`) in JSON-lines format.
3. **Session Diagnostics** — Records workflow completion status, retry counts, and final errors in the `session_diagnostics` table.

These three layers support three use cases: real-time execution monitoring, post-mortem failure investigation, and long-term operational metrics.

## Responsibility Boundary

- **Scope**: Generation and output of observational data during workflow execution.
- **Out of Scope**: Execution logic of the workflow engine itself, decision logic for post-execution approvals.
- **Owners**: `agent/workflow.py` (`WorkflowEngine`), `agent/tool_audit.py` (Audit Writer).

## Key Constraints

- Additional observability events occur only when in workflow mode. In normal mode, only `turn_start`/`turn_end` are generated.
- Calling writing functions for `tool_approval` / `tool_exec` outside of a workflow context results in an assertion error.
- Session diagnostics are stored in the `session_diagnostics` table and are separate from the messages table.

## Operational Notes

### Reading Workflow Spans

Expected span names:
- `workflow.run` — Entire workflow execution
- `workflow.stage` — Individual stage execution
- `workflow.approval` — Post-execution approval passed
- `workflow.retry` — Waiting for retry

### Troubleshooting Failure

1. Check `audit.log` for `workflow_start`/`stage_completed` events to identify which stage failed.
2. Check `session_diagnostics` for the workflow completion status and final error.
3. Refer to OTel spans for detailed execution time and metadata.

### Verifying Normal Operation

- Verify that `workflow_start` occurs after `turn_start`.
- Verify that `stage_completed` occurs at the end of each stage.
- Verify that `approval_requested` occurs at steps requiring approval.

## Known Limitations / Unresolved Issues

- Since additional observability events occur only in workflow mode, differentiation from normal mode is required.
- Workflow information might be redundantly recorded in both audit logs and session diagnostics.

## Related Docs

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — Startup and Health Checks
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — Audit Logs and OTel
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — Role of `session_diagnostics`
