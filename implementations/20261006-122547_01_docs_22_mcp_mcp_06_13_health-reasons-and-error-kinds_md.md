## Goal

Remove the body `### Related Documents` block (lines 68-71) and stray `### Keywords` block (lines 73-76, verbatim dup of `## Keywords` at 165-168) from `mcp_06_13`; tidy blank lines/file ending; confirm contextual links remain. Both body entries already present in front matter `related:`. (REQ-001, REQ-002 / AC-2)

## Scope

- Remove the `### Related Documents` block (lines 68-71)
- Remove the stray `### Keywords` block (lines 73-76)
- Tidy blank lines and file ending
- Confirm contextual links remain intact

## Assumptions

- The two body entries (`mcp_00_document-guide.md`, `mcp_06_02_configuration-file-inventory.md`) already exist in front matter `related:` — verified by survey
- The `### Keywords` block is a verbatim duplicate of `## Keywords` (lines 165-168) — confirmed as UNK-03
- Contextual prose links in the document body are not affected by this removal

## Design decisions

- Adopt the recommended option: remove both blocks since no link is lost
- Keep the `---` separator before the removed blocks (or replace with a single trailing `---` if needed)

## Alternatives considered

- Keep the `### Related Documents` block — rejected because it duplicates front matter and violates the single-store rule
- Keep the `### Keywords` block — rejected because it is a verbatim duplicate of `## Keywords`

## Implementation

### Target file

`docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md`

### Procedure

1. Remove lines 68-71 (`### Related Documents` block including its two list items)
2. Remove lines 73-76 (stray `### Keywords` block including its two keywords)
3. Tidy blank lines and file ending
4. Confirm contextual links remain

### Method

- Edit the file directly to remove the two blocks
- Verify no link was lost by comparing front matter `related:` with the removed entries

### Details

**Before (lines 66-79):**
```markdown
---

### Related Documents

- `mcp_00_document-guide.md`
- `mcp_06_02_configuration-file-inventory.md`

### Keywords

health-reasons
scheduling

---
```

**After:**
```markdown
---
```

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the MCP server-catalog / health-reasons task entry in `docs/00_index.md`'s "Document References by Task" table
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- No security implications — this is a documentation cleanup
- The removed blocks contained only document references, not sensitive information

## Rollback considerations

- Reverting would restore the duplicate blocks — the survey confirms no link is lost by removal
- If a still-needed link is discovered later, it can be added back to front matter `related:`

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md` | Documentation review | Read removed-block region; front matter still has both entries | No body Related/Keywords section; contextual links intact |
| Survey before/after | Proof no link lost | Baseline vs after survey diff | No still-needed link removed |

## Completion criteria

- Body `### Related Documents` block removed (lines 68-71)
- Stray `### Keywords` block removed (lines 73-76)
- Front matter `related:` still contains both entries (`mcp_00_document-guide.md`, `mcp_06_02_configuration-file-inventory.md`)
- Contextual links remain intact
- No blank-line or file-ending issues introduced

## Out of scope

- Any change to ADR documents or ADR rules (handled by `rel002`)
- Changing contextual links inside ordinary prose
- Removing `Reading Order`, `Related ADRs` or other purpose-specific navigation sections
- Reorganizing or renaming documents
- Changing front matter fields other than `related:`
- Adding a local gate to `.pre-commit-config.yaml`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove body `### Related Documents` and stray `### Keywords` blocks | Pending | — | — | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A (documentation review) |
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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: docs/22_mcp/mcp_06_13_health-reasons-and-error-kinds.md
