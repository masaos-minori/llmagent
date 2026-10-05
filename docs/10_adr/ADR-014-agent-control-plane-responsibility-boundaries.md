---
title: "ADR-014: Responsibility Boundaries of the Agent Control Plane"
area: governance
tags:
  - system
  - workflow-engine
  - architecture
decision_scope:
  - system
related:
  - ADR-001-workflow-engine-mandatory.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
---

# ADR-014: Responsibility Boundaries of the Agent Control Plane

## Keywords

agent control plane
responsibility boundaries
orchestrator
workflow engine

## Status

Accepted

## Summary

The Workflow Engine is the mandatory and sole workflow control path (ADR-001), but actual Agent processing is composed of multiple layered components, `Orchestrator`, `LlmTurnExecutor`, `ToolExecutor`, and MCP Server, which also effectively handle processing order and verification. This ADR fixes the responsibility boundaries of these five components and establishes that no component duplicates responsibilities of other layers beyond its own layer (such as deciding persistent business state, managing the tool call execution order, or judging the technical safety of external operations).

## Context

### Problem

ADR-001 established that the Workflow Engine is the mandatory and sole workflow control path, but which responsibilities the components other than the Workflow Engine (`Orchestrator`, `LlmTurnExecutor`, `ToolExecutor`, MCP Server) actually bear was not documented. When implementation accumulates while responsibility boundaries remain undocumented, there is a risk that the same responsibility (for example, creating and holding the LLM/Tool call loop) appears duplicated in multiple components, or that one layer takes over a judgment that belongs to another layer (for example, the Orchestrator judging the safety of an individual Tool call). In fact, implementation verification while drafting this ADR found a duplication: `Orchestrator` created an unused `LLMTurnRunner` instance in its own constructor, while the actual LLM/Tool call loop was processed by a separate instance that `LlmTurnExecutor` creates internally on its own (see Known Deviations).

### Constraints

- Execution on a single host in a single Agent process is assumed (the same assumption as ADR-001)
- The ADR-001 decision that the Workflow Engine is the mandatory and sole workflow control path is not changed
- The calling form of Public APIs between existing components (such as `Orchestrator.handle_turn()`) is not broken

## Assumptions

- Target environment: a single host, a single Agent process
- Trust boundary: privileges are granted only within the Agent process (the same as ADR-001)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, a major redesign of the component structure (for example, merging `LlmTurnExecutor` and `ToolExecutor`)

## Decision

### Decision Details

1. The responsibility boundaries are fixed as follows.

   - **Workflow Engine** (`scripts/agent/workflow/workflow_engine.py`): responsible for persistent business state (Task, Attempt), stage transitions (`plan -> execute -> approval -> verify -> complete/failed`), retries, and approvals. The mandatoriness and uniqueness defined by ADR-001 are maintained as is.
   - **Orchestrator** (`scripts/agent/orchestrator.py`): responsible for coordinating processing within a single turn. It performs only coordination that completes within a turn, such as delegating task initialization and startup to the Workflow Engine, managing conversation state, and emitting audit events, and delegates decisions about persistent business state to the Workflow Engine.
    - **LlmTurnExecutor** (`scripts/agent/llm_turn_executor.py`): responsible for the short loop between the LLM and Tool Calls (streaming and Tool call round-trips within a turn). Creating and holding this loop is centralized in the component that actually drives the loop (currently `LlmTurnExecutor`), and no other component holds duplicate unused instances.
    - **ToolExecutor** (`scripts/shared/tool_executor.py`): responsible for executing a single Tool Call (gate checks, lifecycle checks, transport resolution, execution records). State spanning multiple calls and per-turn coordination are left to the Orchestrator/LlmTurnExecutor.
   - **MCP Server** (under `scripts/mcp_servers/`, for example `shell/shell_service.py`, `tool_validators.py`): responsible for the technical safety of external operations (allowlist validation, path validation, sandboxed execution, resource limits, argument validation). These safety judgments are not taken over by the Orchestrator/ToolExecutor layers.

2. No component takes over or duplicates responsibilities that belong to layers above or below it (such as deciding persistent business state, creating the Tool call loop twice, or judging the technical safety of external operations).

3. This ADR does not change the mandatoriness and uniqueness of the Workflow Engine defined by ADR-001. It is positioned as a complement that extends ADR-001's Scope (`Orchestrator`, `WorkflowEngine`, `WorkflowLoader`, `StateStore`) to `LlmTurnExecutor`, `ToolExecutor`, and MCP Server.

### Scope

- **Target components**: `Orchestrator`, `WorkflowEngine`, `LlmTurnExecutor`, `ToolExecutor`, MCP Server (each server implementation under `scripts/mcp_servers/`)
- **Target processes**: the entire Agent process
- **Target data**: none (this ADR defines the allocation of responsibilities between components and does not change the data model itself)
- **Target Environment Profile**: production (the same as ADR-001; the only supported execution mode)
- **Target APIs or processing paths**: `Orchestrator.handle_turn()`, `WorkflowEngineAdapter.execute_turn()`, `LlmTurnExecutor.handle_llm_turn()`, `LlmTurnExecutor.run()`, `ToolExecutor.execute()` (or `_raw_execute()`), `validate_tool_args()` on the MCP Server side

### Out of Scope

- Redefinition of the mandatoriness and uniqueness of the Workflow Engine (handled by ADR-001)
- Redesign of the approval policy
- Redesign of the component structure itself, such as merging `LlmTurnExecutor` and `ToolExecutor`
- Details of the safety policy of each individual MCP Server (allowlist contents, sandbox types, and so on)

## Rationale

### 1. Primary Reason for Adoption — Maintainability

When responsibility boundaries are not documented, which component should decide what is left to the implementer's discretion when writing new code or changing existing code, which easily causes duplication and gaps. The unused `LLMTurnRunner` instance in `Orchestrator` found while drafting this ADR (see Known Deviations) shows that this lack of boundaries had already caused actual harm.

### 2. Second Reason for Adoption — Correctness

When each layer takes over judgments beyond its own scope, judgments become distributed across layers and it becomes ambiguous which layer's judgment is ultimately effective (for example, if both the Orchestrator and the MCP Server separately judge the safety of an individual Tool call, there is a risk of inconsistency where a change to one is not reflected in the other).

### 3. Third Reason for Adoption — Auditability

The mandatoriness and uniqueness of the Workflow Engine defined by ADR-001 are a discipline for the layer that the Workflow Engine manages. By likewise clarifying the responsibilities of the other layers (in-turn coordination, LLM/Tool round-trips, single Tool execution, safety of external operations), this ADR increases the auditability of the Agent control plane as a whole.

Do not use "the current code is implemented this way" as the sole reason for adoption.

## Alternatives Considered

### Alternative A: Leave Responsibility Boundaries Undocumented and Rely on Implicit Implementation Practice (Status Quo)

#### Description

Do not document each component's scope of responsibility, and treat the structure of the existing code as is as an implicit contract.

#### Advantages

- No additional documentation work
- No impact on the existing implementation

#### Disadvantages

- Problems like the unused `LLMTurnRunner` duplication in `Orchestrator` found while drafting this ADR cannot be prevented in advance
- The risk remains that new implementers mistakenly implement responsibilities that cross layers

#### Reason for Rejection

Rejected to prioritize Maintainability and prevent recurrence by making the boundaries explicit.

#### Reconsideration Conditions

- The component structure is greatly simplified and the cost of documenting boundaries is no longer justified

### Alternative B: Merge `Orchestrator` and `LlmTurnExecutor` into a Single Component

#### Description

Merge turn coordination and the LLM/Tool round-trip loop into a single class, structurally eliminating the responsibility-boundary problem itself.

#### Advantages

- The risk of duplicate creation between components disappears structurally
- The call path is simplified

#### Disadvantages

- A large-scale refactoring of the already extracted concern classes (`TurnCoordinator`, `WorkflowEngineAdapter`, `LlmTurnExecutor`, and so on) is required
- The responsibilities of a single class grow, with a risk of reduced readability instead

#### Reason for Rejection

Rejected because this ADR aims to clarify responsibility boundaries, and a redesign of the component structure itself should be a separate refactoring decision (see Out of Scope).

#### Reconsideration Conditions

- Operational experience shows that making the responsibility boundaries explicit alone cannot prevent duplicate creation from recurring

## Consequences

### Positive Consequences

- Each component's scope of responsibility is made explicit, making it easier to avoid duplicating or taking over judgments across layers in new implementations
- The unused `LLMTurnRunner` duplication in `Orchestrator` found while drafting this ADR was fixed through an issue (see Known Deviations)
- The mandatoriness and uniqueness of the Workflow Engine defined by ADR-001 are complemented consistently for the other layers

### Negative Consequences

- Not every existing implementation strictly follows this ADR's boundaries (see Known Deviations), so additional fix work arises
- Documenting component boundaries makes it necessary to verify the validity of boundary changes each time during future refactoring

## Invariants

- INV-023: Components other than the Workflow Engine (`Orchestrator`, `LlmTurnExecutor`, `ToolExecutor`) do not themselves decide persistent Task/Attempt state, stage transitions, retries, or whether to approve. These are decided only under the management of the Workflow Engine.
- INV-024: Creation of `LlmTurnExecutor` instances is centralized in the one component that actually drives the LLM/Tool Call round-trip loop. No other component holds unused or duplicate `LlmTurnExecutor` instances.
- INV-025: The technical safety judgments of external operations that the MCP Server is responsible for (allowlist validation, path validation, sandboxed execution, resource limits, argument validation) are not taken over or duplicated in the Orchestrator layer or the ToolExecutor layer.

## Verification

### Automated Tests

- **Test**: A regression test that `Orchestrator` does not hold an unused `LlmTurnExecutor` instance (needs to be newly created)
  - **Verifies**: INV-024
  - **Type**: Unit
  - **Blocking**: No (not yet implemented; to be added after the Known Deviations issue is resolved)

### Startup Validation

Not applicable (this ADR is a static design discipline about allocating responsibilities between components and is not a target of startup validation).

### Deployment Validation

Not applicable.

### Runtime Monitoring

- Health Check: Not applicable
- Metrics: substituted by existing workflow events and Tool execution audit logs (ADR-001, the existing audit mechanism)
- Logs: continue to use existing audit-log mechanisms such as `agent.tool_audit`
- Alert conditions: Not applicable

### Manual Review

- When adding a new component, or during code review of a change that alters the scope of responsibility of the Orchestrator/LlmTurnExecutor/ToolExecutor/MCP Server, confirm consistency with this ADR's responsibility boundaries

Register any Invariant without Verification as an unverified item in an Issue. INV-023 and INV-025 currently have no automated tests and depend only on code review (Manual Review).

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

See Related Documents > Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

- ~~`Orchestrator.__init__` (`scripts/agent/orchestrator.py`) creates an unused `LLMTurnRunner` instance as `self._llm_runner`, while the actual LLM/Tool Call round-trip loop is processed by a separate instance that `LlmTurnExecutor` (`scripts/agent/llm_turn_executor.py`) creates internally on its own. This is a current deviation from INV-024 (centralized `LlmTurnExecutor` creation) and is tracked by a fix issue (`issues/done/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md`).~~ → **RESOLVED**: `Orchestrator.__init__` has been refactored so that it no longer constructs `_llm_runner`. Currently `self._llm_executor = LlmTurnExecutor(...)` is actively used (passed to `WorkflowEngineAdapter`, `await self._llm_executor.handle_llm_turn(...)`), and no duplicate instance exists.
- The definition in this ADR that "the Workflow Engine is responsible for retries" does not itself contradict INV-023, but separate "retry" concepts also exist in `ToolLoopGuard.check_retry()` (`scripts/agent/tool_loop_guard.py`) and in the LLM transport layer (such as `llm_max_retries` in `config/agent.toml`), and their relationship to the WorkflowEngine's `retry_policy` is undocumented. Because their granularity differs, this is not immediately judged an INV-023 violation, but the lack of organization is tracked by a documentation issue (`issues/done/20260914-123659_arch03_retry_ownership_documentation_and_layering.md`). → **RESOLVED**: An explanation of the three layers of retry scope has been added to `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md` (REQ-002).

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The structure of any of the Orchestrator/LlmTurnExecutor/ToolExecutor/MCP Server components changes significantly through merging or splitting
- The mandatoriness and uniqueness of the Workflow Engine (ADR-001) itself are re-evaluated
- The deployment changes to multiple hosts or a distributed configuration
- An implementation that contradicts this ADR's responsibility boundaries is newly found at a scale that Known Deviations can no longer track

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Related ADRs

- ADR-001: Mandatory Workflow Engine

### Specifications

- [ADR-001: Mandatory Workflow Engine](ADR-001-workflow-engine-mandatory.md) — the prerequisite ADR defining the mandatoriness and uniqueness of the Workflow Engine
- [Turn Processing Flow](../23_agent/agent_03_03_turn-processing-flow-workflow-engine.md) — details of workflow execution

### Operations

- None

### Known Issues

- `issues/done/20260914-121616_arch01_orchestrator-dead-llm-turn-runner-reference.md` — issue fixing the violation of invariant INV-024.

### Implementation References

- `scripts/agent/orchestrator.py` — `Orchestrator.handle_turn()`
- `scripts/agent/workflow/workflow_engine.py` — `WorkflowEngine.run()`
- `scripts/agent/workflow_engine_adapter.py` — `WorkflowEngineAdapter.execute_turn()`
- `scripts/agent/llm_turn_executor.py` — `LlmTurnExecutor.handle_llm_turn()`
- `scripts/agent/llm_turn_executor.py` — `LlmTurnExecutor.run()`
- `scripts/shared/tool_executor.py` — `ToolExecutor._raw_execute()`
- `scripts/mcp_servers/tool_validators.py` — `validate_tool_args()`
- `scripts/mcp_servers/shell/shell_service.py`
- Tests — `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`, `tests/agent/test_llm_turn_runner.py`

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
- [x] Automatable verification does not rely only on Manual Review (some INVs currently rely only on Manual Review; adding automated tests will be considered after the INV-024 fix issue is resolved)
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)
