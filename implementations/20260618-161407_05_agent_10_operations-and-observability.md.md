# Implementation: docs — workflow observability

## Goal

Document workflow-level OTel spans and audit log event schema.

## Scope

- `docs/05_agent_10_operations-and-observability.md`

## Details

Add section: "Workflow Observability"

Include:
- OTel span names: `workflow.run`, `workflow.stage`
- Span attributes: `workflow.task_id`, `workflow.version`, `workflow.stage_id`, `workflow.attempt`
- Audit event types: `workflow_start`, `stage_completed`, `approval_requested`
- Audit event fields per type

## Validation plan

| Check | Command | Target |
|---|---|---|
| Manual review | read doc | accurate |
