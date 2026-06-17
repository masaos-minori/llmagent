# Multi-Agent Orchestration Implementation Plan

## Overview and Implementation Steps

---

## 1. Goal of This Plan

- The main goal is to migrate the current single REPL coordinator-style agent into a structure where a central Orchestrator controls multiple role-specific Workers.
- The goal is not to let one general-purpose agent handle one huge task alone, but to split the work across specialized agents.
- The centralized Orchestrator is responsible for workflow control, task scheduling, retry handling, approval, state management, and artifact management.
- Workers are separated by single responsibility, such as Planner / Retriever / PatchWorker / Integrator / Validator / Publisher.
- In the initial stage, a smaller minimal setup is also proposed, starting with only four roles: Planner / PatchWorker / Validator / Integrator.
- In the integrated specification, the system uses 10 MCP servers:
  -*Orchestrator / Planner / Retriever / Patch Worker / Validator / Integrator / Shell / Git / File / EventBus.
- In short, across all documents, the direction is consistent:
  -*Phase 1 starts with a minimal 4–6 role configuration, and Phase 2 and later can extend the system with roles such as Reviewer / Researcher / Memory Manager.

---

## 2. Current System Assumptions

- The current system is a CLI REPL architecture starting from `agent.py`, and most central control is concentrated in `AgentREPL`.
- The responsibilities currently concentrated in `AgentREPL` include:
  - user input handling
  - slash commands
  - RAG execution
  - LLM calls
  - tool loop execution
  - MCP calls
  - conversation history updates
  - session persistence
- The current system consists of the Agent itself plus multiple MCP servers, and MCP is operated as HTTP MCP with:
  - `GET /health`
  - `GET /v1/tools`
  - `POST /v1/call_tool`
- On startup, the Agent compares `/v1/tools` definitions and, if needed, can restart OpenRC services via watchdog.
- The current one-turn REPL flow is:
  - RAG → append history → compress → LLM → tool loop
- The current Agent has a responsibility-separated structure where `AgentContext` receives:
  - `LLMClient`
  - `ToolExecutor`
  - `HistoryManager`
  - `RagPipeline`
  - `CommandRegistry`
  - `AgentSession`
- This responsibility-separated structure can be reused as the basis for extracting a shared WorkerRuntime.

---

## 3. Target Architecture Overview

- The target structure is a centralized architecture of:
  -*User → Orchestrator (or orchestrator-mcp) → multiple Worker Agents
- The Orchestrator has Orchestrator MCP as its external interface.
- Internally, the Orchestrator needs at least:
  - Workflow Engine
  - Task Scheduler
  - Retry Controller
  - State Manager
  - Policy
  - Approval
  - Repository management
  - MCP Registry
  - Audit Logger
- Workers are implemented as MCP Servers, with a standardized interface but role-specific internal behavior.
- Supporting systems include:
  - Event Bus
  - Metadata DB
  - Shared Git Repo
  - Git LFS
  - Shell MCP
  - Git MCP
  - File MCP
  - EventBus MCP
- The source of truth for deliverables is Git, and the Event Bus carries only references, not the actual artifact content.
- The source of truth for execution state is the Metadata DB, which is also used for recovery after restart.
- The Event Bus is not designed for maximum throughput. It is positioned as a lightweight asynchronous foundation focused on persistence, replay, resend, and auditability.

---

## 4. Design Principles to Adopt

- The official communication method for the first implementation is HTTP MCP, not custom TCP or file watching.
- The reason is that the current environment already operates around:
  - HTTP MCP
  - OpenRC
  - watchdog
  - `/mcp` status display
- The first choice for work isolation is Git worktree.
- The reason is:
  - each PatchWorker can have an isolated file space
  - Integrator can merge results more easily
  - it fits well with the existing Git / File / GitHub MCP setup
- More specifically:
  - Planner / Validator / Integrator should prefer chat-type endpoints
  - PatchWorker should prefer code-type endpoints
- Backward compatibility is not the priority. The policy is to aggressively separate responsibilities from `agent.py` into the Orchestrator.

---

## 5. Role Definitions

### 5.1 Important Roles in Phase 1

- Planner
  - Breaks a change request into `change_set` and task graph
  - Defines dependencies
  - Defines acceptance criteria

- Retriever
  - Performs RAG search
  - Extracts related code
  - Collects evidence
  - Provides context

- PatchWorker
  - Generates file-level patches
  - Produces diffs
  - Creates local implementation proposals

- Integrator
  - Merges multiple file patches into one `patch_set`
  - Generates validation artifacts
  - Produces integration summaries

- Validator
  - Runs syntax checks, lint, typecheck, unit tests, and runtime verification
  - Returns pass/fail and retry hints

- Publisher
  - Dedicated publishing role
  - Creates branches, commits, pushes, Draft PRs, and final summary

### 5.2 Candidates for Phase 2 and Later

- Reviewer
  - Handles review
  - Detects design deviations
  - Checks guideline compliance

- Researcher / enhanced Retriever
  - Improves pre-implementation investigation
  - Performs impact analysis

- Memory Manager
  - Organizes and reuses knowledge, rules, and failure lessons

---

## 6. Responsibilities of the Orchestrator

- The Orchestrator is responsible for:
  - starting workflows
  - expanding tasks
  - calling role MCP servers
  - dependency control
  - state updates
  - retry control
  - approval / policy control
  - barrier control
  - final result return
- In simpler terms, its core responsibilities are:
  - Task decomposition
  - Worker assignment
  - Phase management
  - Barrier management
  - Merge / Test / Retry judgment
- This is an extension of the current Agent's turn-level tool loop into a phase-level workflow loop.

### 6.1 Recommended Phases

- In the integrated proposal, the standard development flow is:
  - Retriever → PatchWorker → Validator → Integrator, with Planner generating the task graph first.
- In integrated spec v1, the workflow phases are:
  - `plan`
  - `retrieve`
  - `implement`
  - `integrate`
  - `validate`
  - `publish`
  - `finalize`
- In the implementation plan, a simpler Phase 1 phase set is proposed:
  - `plan`
  - `implement`
  - `validate`
  - `integrate`
  - `finalize`
- Therefore, the implementation must decide early whether `retrieve` should be:
  - a separate phase, or
  - embedded into Planner / Worker-side execution

### 6.2 Barrier and Retry

- PatchWorkers must not be dispatched until Planner is complete.
- Integrator must not run until all PatchWorkers are complete.
- If Validator fails, retry should be routed back to PatchWorker or Integrator.
- Retry policy should prefer:
  - retry for temporary failures
  - no retry for deterministic failures like syntax/lint/test failure

---

## 7. State Management and Persistence

- In multi-agent orchestration, state should be divided into three layers:
  - Run-level
  - Artifact-level
  - Knowledge-level
- Run-level state includes:
  - `run_id`
  - `phase`
  - `task graph`
  - `worker assignments`
  - `barrier state`
- Artifact-level state includes:
  - `worktree path`
  - `branch`
  - `changed files`
  - `patch status`
  - `validation status`
- Knowledge-level state includes:
  - `research notes`
  - `review comments`
  - `retry reasons`
  - `accepted decisions`
- In integrated spec v1, the source of truth for:
  - workflow
  - task
  - artifact
  - retry
  - approval
    is unified into `state_manager.py`.
- The main persistence target should be `workflow.sqlite`, optionally combined with JSONL audit logs.
- However, the implementation plan also proposes a new `orchestrator.sqlite`.
- Therefore, the design must decide first whether to:
  - reuse `workflow.sqlite`, or
  - create `orchestrator.sqlite`

---

## 8. Artifact Sharing and Git / Worktree Strategy

- The source of truth for deliverables is Git / Git LFS.
- The Event Bus should not carry actual files. It should only carry references such as:
  - repo
  - branch
  - commit
  - file path
  - PR URL
  - LFS paths
- PatchWorker generates patches and commits on a working branch.
- Validator checks out the target commit and validates it.
- Integrator merges validated results and resolves conflicts when necessary.
- Dangerous operations such as:
  - `git push`
  - `git merge`
  - direct update of `main`
  - protected branch exceptions
    must be controlled by the Orchestrator, not by Workers.
- The implementation plan proposes the following structure per worker:
  - `runs/<run_id>/workers/<worker_id>/`
  - `worktrees/<run_id>/<worker_id>/`
  - `artifacts/<run_id>/`

---

## 9. Position of the Event Bus

- In the integrated proposal, the Event Bus is for lightweight notification only.
- Routing and dependency resolution are handled by the Orchestrator.
- The Event Bus provides:
  - persistence
  - resend
  - replay
  - audit log delivery
  - UI update event delivery
- The initial implementation recommends a Pull / Polling model.
- A future extension may add SSE subscribe support.
- Physical logs should use JSONL / NDJSON, and query/index support should use SQLite.
- Delivery semantics are at least once, and consumers must deduplicate using `event_id`.

---

## 10. MCP Interface Policy

- All Workers and Orchestrator are exposed as MCP Servers.
- The standard interface is:
  - `GET /health`
  - `GET /v1/tools`
  - `POST /v1/call_tool`
- At minimum, `orchestrator-mcp` should provide:
  - `orchestrate_task`
  - `get_run_status`
  - `get_run_artifacts`
  - `retry_phase`
  - `abort_run`
  - `list_workers`
- For Phase 1, the minimum startup set may begin with:
  - `orchestrate_task`
  - `get_run_status`
- The current MCP pattern mainly uses:
  - `{"result": str, "is_error": bool}`
- But the Orchestrator needs structured data such as:
  - `run_id`
  - `phase`
  - `workers`
  - `plan`
  - `artifact summary`
- Therefore, an extended response format is recommended:
  - `result_text`
  - `result_data`
  - `meta`

---

## 11. REPL / Agent Redesign Policy

- `agent.py` remains as the CLI entrypoint.
- `agent_repl.py` is reduced to a UI and slash command adapter.
- `AgentContext` keeps only conversation state.
- It must not own:
  - workflow
  - task
  - artifact
  - retry
  - approval
- Direct workflow execution is removed from the REPL and replaced by Orchestrator calls.
- Commands such as:
  - `/plan`
  - `/mcp`
  - `/stats`
  - `/context`
  - `/rag`
    must be redefined for the new architecture.

---

## 12. Implementation Steps by Phase

### Phase 0. Fix Responsibility Boundaries

- Target:
  - `agent.py`
  - `agent_repl.py`
  - `agent_context.py`
  - `agent_commands.py`
  - `agent_rag.py`
- Separate:
  - UI responsibility
  - orchestration responsibility
  - conversation state responsibility
- Identify and confirm removal targets:
  - old direct tool loop
  - old direct RAG path
  - old direct coordinator logic
- Clarify the boundary between Integrator and Publisher.

### Phase 1. Add Orchestrator Skeleton and State Layer

- Create:
  - `orchestrator.py`
  - `workflow_engine.py`
  - `task_scheduler.py`
  - `retry_controller.py`
  - `state_manager.py`
  - `orchestrator_models.py`
- Implement:
  - workflow/task/artifact DTOs
  - state machine
  - scheduler skeleton
  - retry skeleton
  - `workflow.sqlite` schema
- Completion condition:
  - workflow creation
  - state updates
  - task registration
  - event recording
    all work independently

### Phase 2. Shrink the REPL Layer

- Reduce:
  - `agent.py`
  - `agent_repl.py`
  - `agent_context.py`
    into UI-only mode
- Remove workflow state from AgentContext
- Make REPL call the Orchestrator

### Phase 3. Move RAG to Retriever

- Extract the core of `agent_rag.py` into a service
- Move it into `retriever_mcp_server.py`
- Remove direct RAG path from REPL
- Make RAG run through Retriever MCP

### Phase 4. Add Planner

- Add `planner_mcp_server.py`
- Implement:
  - request → change\_set
  - task graph
  - dependencies
  - acceptance criteria
- Completion condition:
  - one request creates file tasks under one workflow\_id

### Phase 5. Add PatchWorker

- Implement:
  - `patch_worker_mcp_server.py`
  - `worker_runtime.py`
  - `worker_launcher.py`
  - `worktree_manager.py`
- Add:
  - file-level patch creation
  - diff creation
  - worker-specific worktree isolation
  - parallel execution of multiple file tasks

### Phase 6. Add Integrator

- Implement `integrator_mcp_server.py`
- Merge multiple file patches into one `patch_set`
- Generate validation artifacts and integration summaries

### Phase 7. Add Validator

- Implement `validator_mcp_server.py`
- Run syntax/lint/test on the whole `patch_set`
- Distinguish deterministic vs transient failure
- Connect results to `retry_controller`

### Phase 8. Add Repository / Policy / Approval / Audit

- Implement:
  - `repository_gateway.py`
  - `policy_engine.py`
  - `approval_gate.py`
  - `mcp_registry.py`
  - `audit_logger.py`
  - `orchestrator_barrier.py`
- Centralize local / GitHub repository I/O
- Make GitHub write → Draft PR subject to approval
- Show role MCP health and capability in `/mcp`

### Phase 9. Add Publisher

- Implement `publisher_mcp_server.py`
- Support:
  - branch
  - commit
  - push
  - Draft PR
  - final summary
- Only approval-passed `patch_set` can be published

### Phase 10. Integrate with agent / MCP Operations

- Add `mcp_servers.orchestrator` and orchestrator tool definitions to `config/agent.json`
- Add/update:
  - `scripts/orchestrator_mcp_server.py`
  - `config/orchestrator_mcp_server.json`
  - `init.d/orchestrator-mcp`
  - `deploy/deploy.sh`
  - `deploy/setup_services.sh`
- Completion condition:
  - `orchestrator-mcp` runs and is monitored like existing MCP servers
  - it appears in `/mcp`

### Phase 11. Redesign Commands and Remove Old Paths

- Redefine:
  - `/plan`
  - `/mcp`
  - `/stats`
  - `/context`
  - `/rag`
- Remove:
  - old direct tool loop
  - old direct RAG execution
  - old coordinator logic

---

## 13. Minimum Goal for Phase 1

- Start `orchestrator-mcp` as an MCP server
- Run four role presets:
  - Planner
  - PatchWorker
  - Validator
  - Integrator
- Isolate PatchWorker using Git worktree
- Store run state and audit logs with SQLite + JSONL
- Make validation fail → retry work end to end

---

## 14. Main Risks and Mitigations

- REPL / Orchestrator responsibility overlap
  → prevent by strictly separating UI responsibilities from workflow responsibilities

- Double state ownership between AgentContext and state\_manager
  → prevent by keeping workflow state only in `state_manager.py`

- Higher latency from distributed role MCPs
  → mitigate with parallel file tasks and retrieval reuse

- Consistency problems from file-level task splitting
  → absorb in Integrator’s `patch_set` merge and Validator’s full `patch_set` validation

- Artifact replacement after approval
  → store `patch_set` hash in approval record and allow publish only for approved hash

- Retry loops running out of control
  → exclude deterministic failures from retry and use max\_attempts per error class

- workflow\.sqlite growth
  → use artifact size limits, truncation policy, and keep room for future artifact-store separation

- HTTP MCP integration mismatch
  → update `/v1/tools` and `tool_definitions` together, and keep OpenRC service names exactly aligned

---

## 15. Summary

- The target is a local development platform where a central Orchestrator manages workflows and multiple Workers handle single responsibilities.

- The key strategy is to reuse current assets:
  - REPL
  - MCP
  - ToolExecutor
  - RAG
  - Git
  - file
  - session
  - workflow
  - audit
    while redistributing responsibilities into:
  - UI
  - orchestration
  - worker
  - repository
  - policy
  - approval
  - publish

- The most natural order for Phase 1 is:

  - Orchestrator skeleton
    - REPL reduction
    - Retriever separation
    - Planner
    - PatchWorker
    - Integrator
    - Validator
    - Policy / Approval
    - Publisher
    - MCP integration

- The essence of the implementation is not simply running multiple LLMs.

- The real goal is to build a coordinated execution platform with:
  - run-level state management
  - phase / barrier / retry control
  - artifact consistency
  - approval-gated publishing
  - replayable audit logs
