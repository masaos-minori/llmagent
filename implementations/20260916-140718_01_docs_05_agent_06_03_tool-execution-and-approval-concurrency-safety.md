## Goal

Add a distinguishing note to `docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`'s "ToolLoopGuard Design Decisions" table next to the existing `tool_error_retry_max` row, explicitly stating it is `ToolLoopGuard`'s own in-memory per-turn block distinct from `WorkflowEngine.retry_policy`'s persistent stage-level retry.

## Scope

- Add a distinguishing note next to the `tool_error_retry_max` row in the "ToolLoopGuard Design Decisions" section.
- The note must explicitly state that `tool_error_retry_max` is `ToolLoopGuard`'s own in-memory per-turn block, distinct from `WorkflowEngine.retry_policy`'s persistent stage-level retry.

## Assumptions

- The "ToolLoopGuard Design Decisions" table currently exists at L41-L51 in the document.
- The `tool_error_retry_max` row currently exists at L49 with no distinguishing note from `WorkflowEngine.retry_policy`.

## Design decisions

- Add the note inline next to the existing row — do not create a new standalone section.
- Do not change any behavior — this is documentation-only.

## Alternatives considered

- Creating a new "Retry Mechanism Landscape" section — rejected because the Plan's intent is to add a distinguishing note near the existing content, not create a new standalone section.

## Implementation
### Target file

`docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`

### Procedure

1. Locate the "ToolLoopGuard Design Decisions" table (L41-L51).
2. After the existing `tool_error_retry_max` row (L49), add a distinguishing note as a prose paragraph below the table, clarifying the distinction between ToolLoopGuard's retry suppression and WorkflowEngine's stage-level retry.

### Method

Current table structure:
```markdown
| Guard | Config field | Behavior |
|---|---|---|
| Deduplication | `tool_dedup_max_repeats` (default 3) | ... |
| Cycle Detection | `tool_cycle_detect_window` (default 2) | ... |
| Retry Limit | `tool_error_retry_max` (default 1) | ... |
| Consecutive Errors | `tool_error_max_consecutive` (default 3) | ... |
```

Required addition after the table (before the "Concurrency Limits" subsection):
```markdown
**Distinction from WorkflowEngine retry**: `tool_error_retry_max` is ToolLoopGuard's own in-memory per-turn block — it suppresses retries of the same `(tool, args)` pair within a single turn. It is NOT the same as `WorkflowEngine.retry_policy.max_attempts`, which governs stage-level retries across turns. These are two independent mechanisms at different granularities: ToolLoopGuard operates within a single LLM turn's tool loop, while WorkflowEngine operates across turns at the workflow stage level.
```

### Details

The note should be placed after the table but before the "Concurrency Limits" subsection heading. The exact location is after L51 (the last table row) and before L53 ("### Concurrency Limits").

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The note references `WorkflowEngine.retry_policy` which is documented in `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` (REQ-002) — cross-referencing is intentional.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the note is found to be misleading, simply remove it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_06_03_*.md` | Documentation quality | `uv run python tools/check_docs_quality.py docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` | Clean |
| `docs/05_agent_06_03_*.md` | Documentation structure | `uv run python tools/check_docs_structure.py docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` | Clean |

## Completion criteria

- `docs/05_agent_06_03_...md`'s `tool_error_retry_max` documentation explicitly distinguishes it from `WorkflowEngine.retry_policy`.
- `uv run python tools/check_docs_quality.py docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` passes clean.
- `uv run python tools/check_docs_structure.py docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md` passes clean.

## Out of scope

- Adding the three-layer retry landscape description — handled in the next procedure document (REQ-002).
- Resolving ADR-014's Known Deviations entry — handled in the next procedure document (REQ-003).
- Adding a clarifying docstring note to `tool_loop_guard.py` — handled in the next procedure document (REQ-004).

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-123659_arch03_retry_ownership_documentation_and_layering.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140718
- **Related target files**: docs/05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
