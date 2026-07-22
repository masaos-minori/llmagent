## Goal

Classify each item in Known Issues files into keep, move to main doc, or delete categories.

## Scope

- Review all 5 Known Issues files for item classification
- Provide classification recommendations for each file

## Assumptions

1. The existing documentation structure and content are correct; only classifications need to be determined
2. DESIGN entries (confirmed design decisions with implementation verification) should be kept as they document invariants
3. Items marked as "resolved" or "verified" during previous cleanup sessions may need re-evaluation

## Design decisions

- Classify each item individually based on whether it affects current specification
- Use three categories: Keep, Move, Delete
- Document the rationale for each classification

## Alternatives considered

- Processing all files in a single procedure
- Creating separate procedures for each file

## Implementation

### Target files

- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- `docs/05_agent_90_inconsistencies_and_known_issues.md`
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- `docs/90_shared_90_inconsistencies_and_known_issues.md`

### Procedure

#### Step 1: Classify RAG Known Issues

For `docs/03_rag_90_inconsistencies_and_known_issues.md`:

1. Open the file
2. Review each item
3. Classify as Keep/Move/Delete:
   - DESIGN-2 (FTS5 normalized_content): **Keep** — confirmed design decision with implementation verification
   - DESIGN-3 (documents/chunks responsibility separation): **Keep** — confirmed design decision with implementation verification
   - Remaining items: Review each against current implementation

#### Step 2: Classify MCP Known Issues

For `docs/04_mcp_90_inconsistencies_and_known_issues.md`:

1. Open the file
2. Review each item
3. Classify as Keep/Move/Delete:
   - include_disabled filter / disabled_code structured code: **Evaluate** — was this resolved since last review?
   - Tool execution availability metadata: **Evaluate** — was this resolved since last review?

#### Step 3: Classify Agent Known Issues

For `docs/05_agent_90_inconsistencies_and_known_issues.md`:

1. Open the file
2. Check if it's empty except for Related Documents and Keywords sections
3. If empty, consider removing the file entirely or adding a placeholder note

#### Step 4: Classify Event Bus Known Issues

For `docs/06_eventbus_90_inconsistencies_and_known_issues.md`:

1. Open the file
2. Review each item
3. Classify as Keep/Move/Delete:
   - Ack offset monotonicity: **Evaluate** — still unresolved?
   - /replay?format=json pagination: **Evaluate** — still unresolved?
   - DLQ promotion inline processing: **Evaluate** — still unresolved?
   - dlq.py::promote_to_dlq() not called from production path: **Evaluate** — still unresolved?

#### Step 5: Classify Shared Known Issues

For `docs/90_shared_90_inconsistencies_and_known_issues.md`:

1. Open the file
2. Review each item
3. Classify as Keep/Move/Delete:
   - recover_corruption() DatabaseError propagation: **Evaluate** — still unresolved?

#### Step 6: Document classifications

Create a summary table of classifications for each file:

| File | Item | Classification | Rationale |
|---|---|---|---|
| ... | ... | Keep/Move/Delete | ... |

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The classifications help prevent misunderstanding about what needs ongoing attention

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert any deletions if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All Known Issues files | Classification accuracy | Manual review | Each item classified correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-125342_require.md
- Source plan: plans/20260722-171210_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181901
- Related target files: docs/03_rag_90_inconsistencies_and_known_issues.md, docs/04_mcp_90_inconsistencies_and_known_issues.md, docs/05_agent_90_inconsistencies_and_known_issues.md, docs/06_eventbus_90_inconsistencies_and_known_issues.md, docs/90_shared_90_inconsistencies_and_known_issues.md
