## Goal

Add a three-layer retry landscape description to `docs/agent_03_02_turn-processing-flow-llm-tool-loop.md`, explicitly mapping each layer's retry mechanism, its config field, and its scope boundary — resolving REQ-002.

## Scope

- Add a new section near the existing "Retry Suppression" discussion in the "Role and Design of ToolLoopGuard" area.
- Describe three layers: ToolLoopGuard retry suppression (per-turn), WorkflowEngine retry_policy (stage-level), and LLM transport retry (connection-level).
- Each layer must include: config field name, scope boundary, and relationship to other layers.

## Assumptions

- The "Role and Design of ToolLoopGuard" subsection currently exists at L22-L33 in the document.
- The "Retry Suppression" guard is described at L28-L29.
- The "Known Limitations" section mentions `tool_error_retry_max > 0` at L105.

## Design decisions

- Add the three-layer retry landscape as a new subsection under "Role and Design of ToolLoopGuard".
- Use a table format consistent with the existing "ToolLoopGuard Design Decisions" table in the related document `docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md`.
- Do not change any behavior — this is documentation-only.

## Alternatives considered

- Adding the three-layer description to `docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md` instead — rejected because the Plan's intent is to extend the ToolLoopGuard section specifically in this document where the retry guard is first introduced.

## Implementation
### Target file

`docs/agent_03_02_turn-processing-flow-llm-tool-loop.md`

### Procedure

1. Locate the "Role and Design of ToolLoopGuard" subsection (L22-L33).
2. After the existing five-guard list (after L32), add a new subsection titled "Three-Layer Retry Landscape".
3. Include a table describing all three retry layers with their config fields and scope boundaries.

### Method

Current structure after L32 (before "Isolation of Incomplete Outputs"):
```markdown
If any guard is triggered, subsequent checks are skipped and the loop terminates. After a guard is triggered, a fallback attempt is made to generate a final answer without calling any further tools.

### Isolation of Incomplete Outputs
```

Required addition after L32 (before "### Isolation of Incomplete Outputs"):
```markdown
### Three-Layer Retry Landscape

The system has three independent retry mechanisms at different granularities:

| Layer | Config field | Scope | Relationship to other layers |
|---|---|---|---|
| ToolLoopGuard retry suppression | `tool_error_retry_max` (default 1) | Per-turn, per-(tool, args) pair within a single LLM turn's tool loop | Independent from WorkflowEngine retry; prevents same (tool, args) from being retried within one turn |
| WorkflowEngine stage-level retry | `workflow_engine.retry_policy.max_attempts` | Stage-level across turns; retries entire workflow stages on failure | Independent from ToolLoopGuard; operates across turns at the workflow level |
| LLM transport retry | `llm_max_retries` (config/agent.toml) | Connection-level; retries failed HTTP requests to the LLM endpoint | Independent from both above; operates at the network transport layer before the agent even sees the error |

**Key distinction**: These mechanisms do NOT compose. A ToolLoopGuard retry block does NOT reduce WorkflowEngine retry budget, and an LLM transport retry does NOT count against either. They operate at orthogonal levels of the stack.
```

### Details

The new subsection should be placed after L32 (the last line of the ToolLoopGuard description) and before L34 ("### Isolation of Incomplete Outputs"). It must use the same table formatting style as the existing tables in the document.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The cross-references between layers are intentional and should remain stable as long as the three mechanisms exist independently.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the three-layer description is found to be inaccurate, simply remove it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_03_02_*.md` | Documentation quality | `uv run python tools/check_docs_quality.py docs/agent_03_02_turn-processing-flow-llm-tool-loop.md` | Clean |
| `docs/05_agent_03_02_*.md` | Documentation structure | `uv run python tools/check_docs_structure.py docs/agent_03_02_turn-processing-flow-llm-tool-loop.md` | Clean |

## Completion criteria

- `docs/05_agent_03_02_...md`'s ToolLoopGuard section includes the three-layer retry landscape table.
- `uv run python tools/check_docs_quality.py docs/agent_03_02_turn-processing-flow-llm-tool-loop.md` passes clean.
- `uv run python tools/check_docs_structure.py docs/agent_03_02_turn-processing-flow-llm-tool-loop.md` passes clean.

## Out of scope

- Resolving ADR-014's Known Deviations entry — handled in the next procedure document (REQ-003).
- Adding a clarifying docstring note to `tool_loop_guard.py` — handled in the next procedure document (REQ-004).
- Changing any of the three retry mechanisms' behavior — this is documentation-only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140718
- **Related target files**: docs/agent_03_02_turn-processing-flow-llm-tool-loop.md
