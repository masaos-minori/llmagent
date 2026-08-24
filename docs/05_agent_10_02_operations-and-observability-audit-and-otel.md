---
title: "Agent Operations and Observability - Audit Log and OTel"
area: agent
tags:
  - agent
  - operations
  - audit-log
  - otel
  - observability
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Purpose

To document the design intent and operational methods for audit logs and OTel tracing.

## Design Intent

### Audit Logs

Two events, `turn_start` and `turn_end`, are generated for each turn. Workflow-specific events (`workflow_start`, `stage_completed`, `approval_requested`) are additionally issued only when in workflow mode.

Audit logs serve as a persistent record, enabling analysis even after restarts. Unlike in-session observation counters like `RuntimeStats`, they can be used for incident response and change management decisions.

### OTel Tracing

The OTel SDK is treated as an optional dependency; the agent always falls back to a NoOp implementation so it can start even in environments where it is not installed. A global `TracerProvider` is intentionally not configured to allow multiple tracer instances to coexist within a process and to prevent contamination between tests.

## Responsibility Boundaries

- **In Scope**: Output of observability data from the agent process (audit logs, OTel spans).
- **Out of Scope**: Data transmission to external systems, details of metrics collection infrastructure.
- **Owners**: `agent/tool_audit.py` (audit writer), `shared/otel_tracer.py` (tracer initialization).

## Key Constraints

- Audit logs use JSON-lines format with a structure suitable for later parsing.
- OTel configuration keys (`otel_enabled`, `otel_endpoint`, `otel_service_name`) are set in `config/agent.toml`.
- If `otel_endpoint = ""`, spans are written to standard output / `agent.log`.
- Calling writing functions for `tool_approval` / `tool_exec` outside of a workflow context will result in an assertion error.

## Operational Notes

### Reading Audit Logs

- `turn_start` / `turn_end` are basic events occurring in all turns.
- `workflow_start` / `stage_completed` / `approval_requested` are additional events occurring only in workflow mode.
- The `turn_end` event includes workflow context (`workflow_id`).
- If no audit logger is configured, none of these events will be issued.

### Reading OTel Spans

Expected span names:
- `llm` — LLM call
- `compress` — History compression
- `workflow.run` — Workflow execution
- `workflow.stage` — Stage execution
- `workflow.approval` — Post-execution approval completion
- `workflow.retry` — Retry wait

### Troubleshooting

- Use `audit.log` or `session_diagnostics` to check training errors or token statistics.
- To extract spans, use `grep '"name":' /opt/llm/logs/agent.log`.

## Known Limitations / Unresolved Items

- OTel is an optional dependency and is typically disabled outside of production environments.
- Because a global `TracerProvider` is not configured, tracing integration with other processes is not possible.

## Related Documents

- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — Workflow observability
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) — Role of `session_diagnostics`
- `00_security_01_architecture-and-trust-boundaries.md` — System architecture / trust boundaries / threat modeling / authentication & authorization / auditing / local vs production / Fail-open/Fail-closed / prompt injection responsibility boundaries

(End of file - total 87 lines)
