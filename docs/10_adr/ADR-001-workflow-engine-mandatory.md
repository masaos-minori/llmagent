---
title: "ADR-001: Mandatory Workflow Engine"
area: governance
tags:
  - system
  - workflow-engine
  - architecture
related:
  - ADR-014-agent-control-plane-responsibility-boundaries.md
  - deployment_01_deployment.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - ADR-004-environment-failure-handling-policy.md
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

To manage the Agent's execution state, approvals, retries, verification, persistence, and post-restart recovery with a common state model, the Workflow Engine is the mandatory foundation for Agent execution. Every operation by the Agent that changes external state, executes a Tool, involves multiple steps, or requires approval runs under the management of the Workflow Engine. There is no workflow-disable mode and no direct execution path that bypasses the workflow.

## Context

### Problem

This system executes tasks planned by the LLM. Some tools have side effects, some operations require approval, and tool execution must be observable and recoverable. A direct path from the LLM to tools makes auditing and recovery difficult.

### Constraints

- Execution on a single host in a single process is assumed
- In the deployment environment, the existence of the workflow definition file must be confirmed before startup
- There are no constraints from external protocols, libraries, or services
- Security requirement: every operation with side effects must be traceable
- Data integrity: approval state must persist across process boundaries

## Assumptions

- Target environment: a single host, a single Agent process
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within the Agent process
- External dependencies: none (the workflow definition is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external workflow engine

## Decision

### Decision Details

1. The WorkflowEngine is mandatory. The workflow definition file is a mandatory deployment artifact. If it is missing or fails validation, Agent startup is aborted.
2. Every operation by the Agent that changes external state, executes a Tool, involves multiple steps, or requires approval runs under the management of the Workflow Engine.
3. There is no workflow-disable mode.
4. There is no direct execution path that bypasses the workflow, including a fallback path taken when the workflow definition fails to load.
5. All Agent processing, including simple question answering, is placed under the management of the Workflow Engine. Simplicity of processing is not a reason to bypass the Workflow Engine.
6. The basic states are defined as `plan -> execute -> approval -> verify -> complete/failed`. When approval is not required, approval may be skipped, but workflow management itself is never skipped.
7. Execution success and verification success are distinguished.
8. The Workflow Engine's own precondition checks, such as Health Checks and pre-startup validation, are out of scope.
9. Workflow state (Task, Attempt, approval, processed Event, Artifact) is persisted in `workflow.sqlite`. When a Task is deleted, its related Attempts, processed Events, Artifacts, and approvals are deleted by Cascade.

### Scope

- **Target components**: `Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`
- **Target processes**: the entire Agent process
- **Target data**: task state, approval state, event-processing records, artifacts
- **Target Environment Profile**: production (the only supported execution mode)
- **Target APIs or processing paths**: `handle_turn()`, `WorkflowEngine.run()`, `request_approval()`

### Out of Scope

- Details of individual workflow stage definitions
- Redesign of the approval policy
- Introduction of EventBus integration
- Changes to runtime behavior
- Schema design of the workflow definition file
- Monitoring and metrics design
- The overall production failure policy (handled by ADR-004)

## Rationale

### 1. Primary Reason for Adoption — Correctness

Every operation with side effects must be traceable, and approval state must persist across process boundaries. A direct execution path makes auditing and recovery difficult.

### 2. Second Reason for Adoption — Recoverability

Inspecting and recovering partially completed tasks requires persisted task and attempt state. Without workflow management, resuming after an interruption is impossible.

### 3. Third Reason for Adoption — Operability

Tool execution should not depend solely on the LLM conversation state. Workflow management makes execution patterns consistently predictable and simplifies incident response.

## Alternatives Considered

### Alternative A: Direct tool execution without workflow

#### Description

Allow a direct path from the LLM to tools and skip workflow management.

#### Advantages

- Simple structure
- Reduced overhead for low-risk operations

#### Disadvantages

- Auditing and recovery become difficult
- No persistent state for approval/retry logic
- Partially completed tasks cannot be inspected

#### Reason for Rejection

To prioritize Correctness and Recoverability and to ensure auditability and recoverability.

#### Reconsideration Conditions

- Audit requirements are significantly relaxed
- Recoverability is no longer needed

### Alternative B: Optional workflow mode

#### Description

Make workflow mode optional and allow enabling/disabling it per environment.

#### Advantages

- Simpler development
- Flexible deployment options

#### Disadvantages

- Inconsistent behavior between workflow-enabled and workflow-disabled modes
- Operators cannot predict execution patterns
- Audit trails and approval tracking are still needed when disabled

#### Reason for Rejection

Rejected to prioritize Operability and Data Integrity, because environment-specific rules cause confusion.

#### Reconsideration Conditions

- The operational scale grows and the overhead of workflow management exceeds an acceptable level

### Alternative C: Fallback execution when workflow definition is missing

#### Description

Fall back to direct execution when the workflow definition is missing.

#### Advantages

- Silent mitigation of configuration errors
- Flexibility during a migration period

#### Disadvantages

- Hides configuration errors
- Does not provide immediate feedback through a startup failure

#### Reason for Rejection

Rejected to prioritize the Fail-Fast principle and detect configuration errors immediately.

#### Reconsideration Conditions

- A long migration period is required and a phased rollout becomes mandatory

### Alternative D: Ad-hoc per-tool approval without workflow state

#### Description

Manage approvals only through ad-hoc tool-level approval, without workflow state.

#### Advantages

- Simple approval flow
- Low complexity

#### Disadvantages

- Approval state does not survive a process restart
- It cannot be tracked which approval applies to which attempt
- Batch result verification is not possible

#### Reason for Rejection

Rejected to prioritize Recoverability and Data Integrity, because state must persist across process boundaries.

#### Reconsideration Conditions

- Approval requirements are greatly simplified and batch verification is no longer needed

## Consequences

### Positive Consequences

- Every operation with side effects is traceable
- Approval state persists across process boundaries
- Retry and idempotency behavior are managed centrally
- Partially completed tasks can be inspected
- Persistent task and attempt state required for recovery is available
- Workflow failures are treated as platform failures
- Workflow events, approval events, and error events are logged

### Negative Consequences

- Deployment requires the workflow definition file
- Startup fails when workflow artifacts are missing
- The workflow schema must be initialized before service startup
- Simple chat and tool-based tasks share the same execution control plane
- Startup requires checking consistency between the workflow definition file and the DB Schema, and incident response requires investigating workflow state

## Invariants

- INV-01: If the workflow definition file is missing, Agent startup is aborted.
- INV-02: No external state-change path bypasses the Workflow Engine.
- INV-03: Execution success and verification success are distinguished and verified independently.
- INV-04: Pending-approval state is restored after a restart.
- INV-05: If the workflow definition file fails validation, startup is aborted.
- INV-06: If the required DB Schema is inconsistent, startup is aborted.
- INV-07: At process startup, interrupted Attempts are recovered as `failed` by `recover_stale_attempts()`.
- INV-08: Each stage execution is guaranteed idempotent by the deterministic key `{task_id}:{stage_id}:{attempt}`, and a duplicate start with the same key is rejected by `begin_stage_if_new()`. Because the attempt number is incremented on each retry, a retry is treated as a separate record (only a duplicate start within the same attempt number is rejected).

## Verification

### Automated Tests

- **Test**: Startup-failure test when the workflow definition is missing
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Startup-failure test when the workflow definition is invalid
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Startup-failure test when the required DB Schema is inconsistent
  - **Verifies**: INV-06
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Test that pending-approval state is restored after a restart (`test_startup_recovered_approval_can_resume`)
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Test that no external state-change path bypasses the Workflow Engine
  - **Verifies**: INV-02
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: `test_execute_success_verify_failure_marks_task_failed` (confirms that when verify fails after a successful execute, the task state becomes `failed`, not `completed`)
  - **Verifies**: INV-03
  - **Type**: Unit
  - **Blocking**: Yes

- **Test**: Optimistic-locking and recovery behavior test for `recover_stale_attempts()` (`tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`)
  - **Verifies**: INV-07
  - **Type**: Unit
  - **Blocking**: Yes

- **Test**: `test_begin_stage_if_new_idempotent` (confirms that a double start of `begin_stage_if_new()` with the same event_id is rejected, `tests/agent/workflow/test_workflow_stage_persistence.py`, passing)
  - **Verifies**: INV-08
  - **Type**: Unit
  - **Blocking**: Yes

### Startup Validation

- Whether the workflow definition file exists
- Whether the workflow definition is valid (parseable JSON, required fields, stages, retry policy)
- Whether the required DB tables exist
- Whether the DB schema version matches

### Deployment Validation

- Check the SHA256 checksum of the workflow definition file before and after deployment
- Whether the deployed workflow definition matches the source

### Runtime Monitoring

- Health Check: health checks of the workflow engine itself are out of scope
- Metrics: workflow status, approval state, attempt state
- Logs: workflow events, approval events, error events
- Alert conditions: workflow failure, approval timeout, Schema inconsistency

### Manual Review

- Review of changes to the workflow definition
- Review of changes to the approval policy
- Workflow definition validation before deployment

## Implementation Notes

- Startup preflight checks for the workflow definition file and the workflow DB schema run before `Orchestrator` construction and abort startup on failure (Explicit in code — `scripts/agent/startup_component_init.py`).
- `Orchestrator` construction raises when the workflow definition fails to load, so no fallback mode exists (Explicit in code — `scripts/agent/orchestrator.py`; verified by `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal`).
- `Orchestrator` constructs the `WorkflowEngine` from the loaded workflow definition and routes turns through it (Explicit in code — `scripts/agent/orchestrator.py`).

See Implementation References for the file/symbol list.

## Known Deviations

No confirmed deviations.

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
- **Decision Change (2026-10-08)**: The wording of Decision Details #4, which now names the fallback path taken when the workflow definition fails to load as prohibited, was approved as a task-level approval decision (repository administrator instruction); individual reviewer names are not recorded.

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
- `config/workflows/default.json` — workflow definition file
- Tests — `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

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
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)
