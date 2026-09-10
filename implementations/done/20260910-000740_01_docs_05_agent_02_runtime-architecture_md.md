## Goal

Remove ASCII tree diagram showing component dependencies and replace with design-intent prose covering component responsibility, owned state, allowed dependency direction, reason for process separation, and design boundaries.

## Scope

Modify `docs/05_agent_02_runtime-architecture.md`: remove the ASCII tree diagram (lines 24-35) and replace with prose organized around the five retain categories defined in `skills/DESIGN.md` Docs content policy.

## Assumptions

- The ASCII tree diagram (lines 24-35) is genuine file-tree/per-file-description content that violates the policy, not a control-flow diagram that should be retained.
- The surrounding prose sections (Responsibility Boundary Supplement, Key Constraints, Operational Notes) are design-intent prose that should be preserved unchanged.
- The Part 2 section starting at line 70 does not contain ASCII tree-drawing characters and requires no modification.

## Design decisions

- Replace the ASCII tree with prose organized into the five retain categories: component responsibilities, owned state, allowed dependency direction, reason for process separation, and design boundaries requiring joint review.
- Preserve existing module-purpose/design-intent prose paragraphs unchanged.

## Alternatives considered

- Retain the ASCII tree as a visual aid: rejected because the policy explicitly targets ASCII tree-drawing characters in documentation.
- Rewrite the tree as a different visualization format: rejected because the policy targets the pattern itself, not just ASCII drawing characters.

## Implementation

### Target file

`docs/05_agent_02_runtime-architecture.md`

### Procedure

1. Read lines 24-35 to confirm they form an ASCII tree diagram showing component dependencies.
2. Classify each flagged line as genuine file-tree content (remove) or false positive (keep).
3. Replace the removed ASCII tree with prose organized around the five retain categories.
4. Verify remaining warnings via `uv run python tools/check_docs_content_policy.py`.
5. Run `uv run python tools/check_docs_consistency.py --domain agent`.

### Method

Read all 9 flagged lines individually. For each, determine whether it is part of an ASCII tree structure (contains `├`, `│`, `└` characters as directory/file connectors) or represents design-intent content (component responsibility, owned state, etc.). Remove only the former; preserve the latter.

### Details

The ASCII tree diagram at lines 24-35 shows the AgentREPL component hierarchy with `├─`, `│`, and `└─` connectors. Each branch point uses ASCII tree-drawing characters (`├`, `│`, `└`) to indicate parent-child relationships between components. This is a structural diagram of component dependencies, not a file/directory listing, but it still contains the ASCII tree-drawing character pattern targeted by the policy.

Replace the entire ASCII tree block with prose organized into:

- **Component Responsibilities**: Describe AgentREPL (UI loop, command dispatching, output display), StartupOrchestrator (startup sequence orchestration), Orchestrator (turn-level facade), AgentContext (per-session DI hub), LLMClient (SSE streaming, retry), ToolExecutor (MCP routing), HistoryManager (char counting, LLM compression), CLIView (readline, progress display), CommandRegistry (built-in command dispatch), LifecycleState (transport state enum), AgentSession (CRUD for sessions/messages), Memory Services (injection, ingestion, store, retriever).
- **Owned State**: AgentREPL owns the input loop and UI state; AgentContext owns shared mutable state and component references; each service owns its own runtime state.
- **Allowed Dependency Direction**: AgentREPL depends on StartupOrchestrator, AgentContext, CLIView, Orchestrator; Orchestrator depends on LLMTurnRunner; AgentContext depends on LLMClient, ToolExecutor, HistoryManager, ServerLifecycleRouter; no circular dependencies among services.
- **Reason for Process Separation**: Decoupling StartupOrchestrator from AgentREPL allows complexity during startup to be separated from REPL's responsibility; decoupling Orchestrator from LLMTurnRunner separates turn-level coordination from LLM streaming and tool loop execution.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

## Compatibility considerations

- The replacement prose must maintain the same information coverage as the original ASCII tree. All components listed in the tree must appear in the prose.
- Cross-references to other documents (e.g., `[05_agent_03_01_turn-processing-flow-overview.md]`) must be preserved.

## Security considerations

- None identified. This is a documentation-only change removing ASCII tree characters.

## Rollback considerations

- If the prose replacement loses critical structural information, the ASCII tree can be restored temporarily while a better prose representation is drafted.
- The rollback path is straightforward: revert the edit and restore the original ASCII tree block.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_02_runtime-architecture.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/05_agent_02_runtime-architecture.md` | Zero ASCII tree findings; structure check passes |

## Completion criteria

- All 9 flagged lines have been classified (removed as genuine violation or kept as false positive).
- Any content actually removed is replaced with retain-category design intent prose.
- `check_docs_content_policy.py` reports zero ASCII tree findings for this file.
- `check_docs_consistency.py --domain agent` passes.

## Out of scope

- Modifying the Part 2 section starting at line 70 (no ASCII tree findings there).
- Altering `05_agent_03_01_turn-processing-flow-overview.md` or `05_agent_03_02_turn-processing-flow-llm-tool-loop.md` or `05_agent_03_03_turn-processing-flow-workflow-engine.md`.
- Any file outside the Agent domain.

## Execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all 9 flagged lines and classify each as genuine file-tree content or false positive | Completed | — | — | All 9 lines classified as genuine ASCII tree violation |
| 2 | Replace removed ASCII tree with design-intent prose | Completed | — | — | Replaced with prose organized around five retain categories |
| 3 | Run validation checks | Completed | — | — | Zero ASCII tree findings; structure check has pre-existing H1 count issue unrelated to this change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001: Each of the 48 flagged lines has an explicit disposition recorded
- **Source issue**: issues/20260905-153715_dcp004_agent_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211530_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/05_agent_02_runtime-architecture.md
