---
title: "ADR-001: Mandatory Workflow Engine"
area: governance
tags:
  - system
  - workflow-engine
  - architecture
related:
  - adr_02_02_014_agent-control-plane-responsibility-boundaries.md
  - deployment_01_deployment.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - adr_02_01_004_platform-environment-failure-handling-policy.md
  - governance_01_documentation-policy.md
---

# ADR-001: Mandatory Workflow Engine

## Keywords

- workflow engine
- mandatory
- execution control plane
- state transitions

## Status

Accepted

## Summary

The Workflow Engine is the mandatory foundation for Agent execution: all Agent processing runs under it, with no workflow-disable mode and no bypass path. Human approval is decided before a Tool executes; the workflow has no approval stage. See Decision for the normative rules.

## Context

### Problem

This system executes tasks planned by the LLM. Some tools have side effects, some Tool calls require human approval, and tool execution must be observable and recoverable. A direct path from the LLM to tools makes auditing and recovery difficult.

### Constraints

- Execution on a single host in a single process is assumed
- In the deployment environment, the existence of the workflow definition file must be confirmed before startup
- There are no constraints from external protocols, libraries, or services
- Security requirement: every operation with side effects must be traceable
- Traceability: every human approval decision is recorded with the workflow context of the turn in which it was made

## Assumptions

- Target environment: a single host, a single Agent process
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within the Agent process
- External dependencies: none (the workflow definition is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external workflow engine

## Decision

### Decision Details

1. The WorkflowEngine is mandatory. The workflow definition file is a mandatory deployment artifact. If it is missing or fails validation, Agent startup is aborted.
2. Every operation by the Agent that changes external state, executes a Tool, or involves multiple steps runs under the management of the Workflow Engine.
3. There is no workflow-disable mode.
4. There is no direct execution path that bypasses the workflow, including a fallback path taken when the workflow definition fails to load.
5. All Agent processing, including simple question answering, is placed under the management of the Workflow Engine. Simplicity of processing is not a reason to bypass the Workflow Engine.
6. The basic states are `plan -> execute -> verify -> completed/failed`; a Task that exceeds its retry budget is persisted as a third terminal state `halted`. Human approval is decided before a Tool executes, by the tool-level approval owned by `agent/tool_policy.py` and `agent/tool_approval.py`, inside the `execute` stage. The workflow has no approval stage, and a workflow definition that contains the `require_approval` key is rejected at load time. Workflow management is never skipped.
7. Execution success and verification success are distinguished.
8. The Workflow Engine's own precondition checks, such as Health Checks and pre-startup validation, are out of scope.
9. Workflow state (Task, Attempt, processed Event, Artifact) is persisted in `workflow.sqlite`. When a Task is deleted, its related Attempts, processed Events, and Artifacts are deleted by Cascade.
10. Every tool-level approval decision (approved or denied) is written to the audit log as a `tool_approval` event carrying the `workflow_id` and a `task_id` field that holds the turn ID. No separate approval table is kept.

### Scope

- **Target components**: `Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`
- **Target processes**: the entire Agent process
- **Target data**: task state, event-processing records, artifacts
- **Target Environment Profile**: production (the only supported execution mode)
- **Target APIs or processing paths**: `handle_turn()`, `WorkflowEngine.run()`

### Out of Scope

- Details of individual workflow stage definitions
- Redesign of the tool-level approval policy (risk rules and safety tiers in `agent/tool_policy.py`)
- Introduction of EventBus integration
- Changes to runtime behavior
- Schema design of the workflow definition file
- Monitoring and metrics design
- The overall production failure policy (handled by ADR-004)

## Rationale

### 1. Primary Reason for Adoption — Correctness

Every operation with side effects must be traceable (see Context). A direct execution path makes auditing and recovery difficult.

### 2. Second Reason for Adoption — Recoverability

Inspecting and recovering partially completed tasks requires persisted task and attempt state. Without workflow management, resuming after an interruption is impossible.

### 3. Third Reason for Adoption — Operability

Tool execution should not depend solely on the LLM conversation state. Workflow management makes execution patterns consistently predictable and simplifies incident response.

### 4. Why the Workflow Has No Approval Stage

An approval stage placed after the `execute` stage cannot prevent anything: when it is reached, every Tool of the turn has already run, and rejecting only halts the Task without reverting its effects. Nothing runs only after approval, because the `verify` stage records the turn end. Requiring an approval on every turn also trains operators to approve without reading, which weakens the tool-level approval that does prevent operations. Approval is therefore decided only before a Tool executes, and the decision is traced through the audit log.

## Alternatives Considered

### Alternative A: Direct tool execution without workflow

- **Advantages:** Simple structure; reduced overhead for low-risk operations
- **Disadvantages:** Auditing and recovery become difficult; no persistent state for retry logic; partially completed tasks cannot be inspected
- **Reason for Rejection:** To prioritize Correctness and Recoverability and to ensure auditability and recoverability.
- **Reconsideration Conditions:** Audit requirements are significantly relaxed; Recoverability is no longer needed

### Alternative B: Optional workflow mode

- **Advantages:** Simpler development; flexible deployment options
- **Disadvantages:** Inconsistent behavior between workflow-enabled and workflow-disabled modes; operators cannot predict execution patterns; audit trails and approval decision tracking are still needed when disabled
- **Reason for Rejection:** Rejected to prioritize Operability and Data Integrity, because environment-specific rules cause confusion.
- **Reconsideration Conditions:** The operational scale grows and the overhead of workflow management exceeds an acceptable level

### Alternative C: Fallback execution when workflow definition is missing

- **Advantages:** Silent mitigation of configuration errors; flexibility during a migration period
- **Disadvantages:** Hides configuration errors; does not provide immediate feedback through a startup failure
- **Reason for Rejection:** Rejected to prioritize the Fail-Fast principle and detect configuration errors immediately.
- **Reconsideration Conditions:** A long migration period is required and a phased rollout becomes mandatory

### Alternative D: Per-tool approval without workflow state

- **Advantages:** Simple execution flow; low complexity
- **Disadvantages:** Tasks and Attempts cannot be tracked or recovered after an interruption; retry and idempotency behavior cannot be managed centrally
- **Reason for Rejection:** Rejected to prioritize Recoverability, because workflow state is needed to track and recover Tasks and Attempts. Tool-level approval is kept, and the workflow keeps its own state alongside it.
- **Reconsideration Conditions:** Task and Attempt state are no longer needed for recovery

### Alternative E: Post-execution approval stage

- **Advantages:** A recorded human checkpoint for the result of each turn; the next input is blocked until the result is reviewed
- **Disadvantages:** Cannot prevent an operation: the Tools have already run, and rejection does not revert their effects; an approval on every turn, including turns without side effects; encourages approving without reading, which weakens the tool-level approval; adds persistent pending state, startup recovery, and expiry handling
- **Reason for Rejection:** Rejected because it adds operator burden and state without preventing any operation; tool-level approval and the audit log provide the control and the trace.
- **Reconsideration Conditions:** Tool effects become staged so that they are applied only after approval (for example, changes held in a working area until the turn is approved)

## Consequences

### Positive Consequences

- Every operation with side effects is traceable
- Human approval is requested only where it can prevent an operation, and turns without side effects complete without operator action
- Retry and idempotency behavior are managed centrally
- Partially completed tasks can be inspected
- Persistent task and attempt state required for recovery is available
- Workflow failures are treated as platform failures
- Workflow events, tool-level approval decisions, and error events are logged

### Negative Consequences

- Deployment requires the workflow definition file, and startup fails when workflow artifacts are missing (INV-01)
- The workflow schema must be initialized before service startup
- Simple chat and tool-based tasks share the same execution control plane
- Startup requires checking consistency between the workflow definition file and the DB Schema, and incident response requires investigating workflow state
- There is no human checkpoint for the combined result of a turn; reviewing a turn relies on the diff command and the audit log

## Invariants

- INV-01: If the workflow definition file is missing, Agent startup is aborted.
- INV-02: No external state-change path bypasses the Workflow Engine.
- INV-03: Execution success and verification success are distinguished and verified independently.
- INV-05: If the workflow definition file fails validation, startup is aborted.
- INV-06: If the required DB Schema is inconsistent, startup is aborted.
- INV-07: At process startup, interrupted Attempts are recovered as `failed` by `recover_stale_attempts()`.
- INV-08: Each stage execution is guaranteed idempotent by the deterministic key `{task_id}:{stage_id}:{attempt}`, and a duplicate start with the same key is rejected by `begin_stage_if_new()`. Because the attempt number is incremented on each retry, a retry is treated as a separate record (only a duplicate start within the same attempt number is rejected).
- INV-10: The workflow has no approval stage. A workflow definition that contains the `require_approval` key is rejected at load time, and Agent startup is aborted.
- INV-11: Every tool-level approval decision is recorded in the audit log as a `tool_approval` event with the `workflow_id` and a `task_id` field that holds the turn ID.

## Verification

### Automated Tests

| Test | Verifies | Type | Blocking | Implementation |
|---|---|---|---|---|
| Startup-failure test when the workflow definition is missing | INV-01 | Integration | Yes | - |
| Startup-failure test when the workflow definition is invalid | INV-05 | Integration | Yes | - |
| Startup-failure test when the required DB Schema is inconsistent | INV-06 | Integration | Yes | - |
| Test that no external state-change path bypasses the Workflow Engine | INV-02 | Regression | Yes | - |
| `test_execute_success_verify_failure_marks_task_failed` (confirms that when verify fails after a successful execute, the task state becomes `failed`, not `completed`) | INV-03 | Unit | Yes | - |
| Optimistic-locking and recovery behavior test for `recover_stale_attempts()` | INV-07 | Unit | Yes | `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py` |
| `test_begin_stage_if_new_idempotent` (confirms that a double start of `begin_stage_if_new()` with the same event_id is rejected, passing) | INV-08 | Unit | Yes | `tests/agent/workflow/test_workflow_stage_persistence.py` |
| The loader rejects a workflow definition that contains the `require_approval` key, for any value | INV-10 | Unit | Yes | `tests/agent/workflow/test_workflow_loader.py::TestRequireApprovalKeyRejected` |
| A tool-level approval decision, approved or denied, is written as a `tool_approval` event with the `workflow_id` and the turn ID in `task_id` | INV-11 | Unit | Yes | `tests/agent/test_tool_audit.py::TestAuditApprovalInv11` |

### Startup Validation

- Whether the workflow definition file exists
- Whether the workflow definition is valid (parseable JSON, required fields, stages, retry policy)
- Whether the definition has no `require_approval` key
- Whether the required DB tables exist
- Whether the DB schema version matches

### Deployment Validation

- Check the SHA256 checksum of the workflow definition file before and after deployment
- Whether the deployed workflow definition matches the source

### Runtime Monitoring

- Health Check: health checks of the workflow engine itself are out of scope
- Metrics: workflow status, attempt state
- Logs: workflow events, tool-level approval decisions, error events
- Alert conditions: workflow failure, Schema inconsistency

### Manual Review

- Review of changes to the workflow definition
- Review of changes to the approval policy
- Workflow definition validation before deployment

## Implementation Notes

- Startup preflight checks for the workflow definition file and the workflow DB schema run before `Orchestrator` construction and abort startup on failure (Explicit in code — `scripts/agent/startup_component_init.py`).
- `Orchestrator` construction raises when the workflow definition fails to load, so no fallback mode exists; turns are routed only through the `WorkflowEngine` built from that definition (Explicit in code — `scripts/agent/orchestrator.py`; verified by `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal`).
- The workflow has no approval stage and `workflow.sqlite` has no `approvals` table. A task is complete only after its `verify` stage runs (Explicit in code — `scripts/db/schema_sql.py` workflow schema DDL).
- The `tool_approval` audit event is written only inside a workflow context, which guarantees INV-11's workflow linkage (Explicit in code — `scripts/agent/tool_audit.py`).
- Invariant IDs are not contiguous: `INV-04`, `INV-09`, and `INV-12` are absent from the list. The present IDs are stable and referenced by the invariant verification matrix in `adr_01_index.md`; do not renumber them.

See Implementation References for the file/symbol list.

## Known Deviations

Not applicable

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions are no longer valid
- The reasons for rejecting an alternative no longer hold
- The format of the workflow definition file changes significantly
- The approval model changes fundamentally
- Persistent storage moves to something other than SQLite

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text as of 2026-10-14; individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-004: Failure Handling Policy Across Environments
- ADR-014: Responsibility Boundaries of the Agent Control Plane

## Implementation References

- `scripts/agent/orchestrator.py` — `Orchestrator.handle_turn()`
- `scripts/agent/workflow/workflow_engine.py` — `WorkflowEngine.run()`
- `scripts/agent/workflow/workflow_loader.py` — `WorkflowLoader.load()`
- `scripts/agent/workflow/state_store.py` — `StateStore.recover_stale_attempts()`
- `scripts/agent/workflow/idempotency_ops.py` — `begin_stage_if_new()`
- `scripts/agent/startup_component_init.py` — workflow definition and workflow DB schema preflight checks
- `scripts/db/schema_sql.py` — workflow schema DDL
- `scripts/agent/tool_audit.py` — `audit_approval()`
- `config/workflows/default.json` — workflow definition file
- Tests — `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] Verifiable Invariants are defined
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
