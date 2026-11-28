## Goal

Record MDQ under the single lowercase-snake error-code vocabulary and remove the statement that audit log functions are implemented within each server's dispatch handler, which contradicts the single-emission boundary (REQ-008 documentation, REQ-004 closed vocabulary, REQ-005 single boundary).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 7 is not listed in any `### Release units` entry)

## Assumptions
- Documentation-only row: the lightweight fill applies.
- Re-verified 20261127: the doc has no Error Type Vocabulary section and does not name MDQ as using exception-class names; the statement to remove is line 64, "Audit log functions are implemented within each server's dispatch handler." The plan's earlier evidence line for this row was stale and is corrected in the plan.
- Cross-plan overlap: `plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md` and `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md` name this file in their Reference Files tables as owned by this plan, so no other plan edits it.
- The CI/CD plan's procedure for this file (`implementations/20261127-152110_13_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md.md`) records the CI/CD code vocabulary; it does not change line 64, so the two edits are compatible.
- The code vocabulary content is the set defined by `scripts/mcp_servers/mdq/mdq_error_codes.py` (seq 08); this document records it, it does not define it.

## Design decisions
- The vocabulary statement names one closed set of lowercase-snake codes for MDQ, so the doc cannot reintroduce an exception-class-name vocabulary later.
- The audit statement is replaced by the emission-boundary statement, matching the behavior seq 01 implements.

## Alternatives considered
- Keep line 64 and add an MDQ exception — rejected: the requirement removes the contradicting statement; an exception note would leave two rules in the same doc.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure
- Replace line 64 with the single-emission-boundary statement: one audit record per authenticated call, emitted from the server boundary, not from a handler.
- Record MDQ under the single lowercase-snake code vocabulary.

### Method
- N/A: documentation-only change.

### Details
- The existing rule that persistent output carries no raw query text and no absolute path stays as written; seq 03 and seq 10 implement it for MDQ.
- Step 3b correction (20261128): verified against current source — the statement to remove is line 68, not line 64 (line 64 is the "Approval correlation" heading); the recorded line number was stale by four lines. It was replaced with the single-emission-boundary statement.
- Step 3b correction (20261128): the doc has no Error Type Vocabulary section as the Assumptions state, so MDQ is recorded under the closed vocabulary inside the same paragraph as the emission boundary, naming the eight codes and the `target` redaction rule. The CI/CD row's content for this file is unchanged, so the two edits stay compatible.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only; the documented behavior is the redaction and exactly-one-record requirement.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Completion criteria
- No statement remains that audit log functions live in each server's dispatch handler (AC-7).
- MDQ is recorded under the single lowercase-snake code vocabulary (AC-5).

## Out of Scope
- The MDQ error-code table, which is written in `docs/22_mcp/mcp_04_04_mdq.md` (seq 27).
- The redaction implementation (seq 03, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128-093658 | 20261128-093658 | line 68 replaced with the single-emission-boundary statement plus the closed code vocabulary and the target redaction rule |
| 3 | Run the documentation checker named in `rules/tool-gates.md` | Completed | 20261128-093658 | 20261128-093658 | `uv run python tools/check_docs_content_policy.py` 20261128: all four documentation checkers Pass, as recorded in seq 27's gates row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-008 (documentation), REQ-004 (closed code vocabulary), REQ-005 (single audit boundary)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`