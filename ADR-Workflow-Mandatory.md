# ADR-Workflow-Mandatory

## Status

Accepted

## Date

2026-07-23

## Context

The system executes LLM-planned tasks, some tools have side effects, some operations require approval, tool execution must be observable and recoverable, direct LLM-to-tool path would make auditing and recovery harder.

## Decision

Workflow execution is mandatory. Workflow definitions are required deployment artifacts. Workflow bypass mode is not supported. Optional workflow mode is not supported. Direct execution fallback is not supported.

## Rationale

All side-effecting operations must be traceable. Approval state must survive process boundaries. Retry and idempotency behavior must be centralized. Partial task completion must be inspectable. Recovery requires persisted task and attempt state. Tool execution should not depend solely on LLM conversational state.

## Alternatives Considered

### Direct tool execution without workflow

Rejected. Makes auditing and recovery harder. No persistent state for approval or retry logic.

### Optional workflow mode

Rejected. Creates inconsistent behavior between workflows enabled/disabled. Operators cannot rely on predictable execution patterns.

### Workflow disabled for local mode

Rejected. Local mode still needs audit trails and approval tracking. Different rules for different environments create confusion.

### Workflow fallback when workflow definition is missing

Rejected. Silent degradation hides configuration errors. Startup failure provides immediate feedback.

### Per-tool ad hoc approval without workflow state

Rejected. Approval state would not survive process restarts. No way to track which approvals were applied to which attempts.

## Consequences

Deployment must include workflow definition files. Startup must fail if mandatory workflow artifacts are missing or invalid. Workflow schema must be initialized before service startup. Operators must treat workflow failures as platform failures. Simple chat and tool-backed tasks share the same execution control plane.

## Non-Goals

Define every workflow stage. Redesign approval policy. Introduce EventBus integration. Change runtime behavior.

## Related Documents

- [Workflow Deployment Checklist](docs/02_deployment-part2.md#32-workflow-deployment-checklist)
- [Workflow Deployment Failure Modes](docs/02_deployment-part2.md#33-workflow-deployment-failure-modes)
- [Workflow Schema Responsibilities](docs/02_deployment-part2.md#31-applying-schema)
