## Goal

Update `check_docs_structure.py` (line 89) and `manage_frontmatter.py` (line 91) descriptions in `TOOL_DESCRIPTIONS.md` to the new rule text. (REQ-005 / AC-5)

## Scope

- Update `check_docs_structure.py` description (line 89) to reflect any-level detection and `related` format validation
- Update `manage_frontmatter.py` description (line 91) to document it as a one-time migration aid

## Assumptions

- The current descriptions reference the old rule text (second-level heading detection only)
- The new descriptions must match the strengthened tool behavior

## Design decisions

- Update both descriptions to match the new rule text
- For `check_docs_structure.py`: describe any-level detection and `related` format validation
- For `manage_frontmatter.py`: document it as a one-time migration aid

## Alternatives considered

- Keeping the old descriptions — rejected because they would be stale and misleading

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Update `check_docs_structure.py` description (line 89)
2. Update `manage_frontmatter.py` description (line 91)

### Method

- Edit the relevant lines directly
- Ensure the updated text matches the strengthened tool behavior

### Details

**Before (line 89):**
Description references second-level heading detection only.

**After:**
The updated description states:
- Detects body `Related Documents` / `Related Docs` / `Related Chapters` headings at ANY level in non-ADR documents
- Validates `related` format (basenames ending in `.md`)
- Keeps target-existence, self-reference, and duplicate checks
- Leaves the ADR requirement unchanged

**Before (line 91):**
Description does not clarify `merge-related`'s one-time-use nature.

**After:**
The updated description states:
- `merge-related` is a one-time migration aid for migrating body `## Related Documents` blocks into front matter `related:`
- It detects `## Related Documents` / `## Related Docs` / `## Related Chapters` headings (second-level only)
- For deep `### ` blocks, authors should manually migrate entries to front matter

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the tooling documentation per `routing.md` Docs mapping
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- No security implications — this is a tool description update
- The updated descriptions help prevent misuse of the tools

## Rollback considerations

- Reverting would restore stale descriptions
- If the owner later changes the tool behavior, these descriptions would need revision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Documentation review | Read updated descriptions vs tool behavior | Descriptions match current tool behavior |
| `tools/check_tool_descriptions_sync.py` | Integration: sync check | `uv run python tools/check_tool_descriptions_sync.py` | Passes |

## Completion criteria

- `check_docs_structure.py` description reflects any-level detection and `related` format validation
- `manage_frontmatter.py` description documents one-time migration aid
- No stale statements of the old rule remain
- `check_tool_descriptions_sync.py` passes

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
| 1 | Update `check_docs_structure.py` description | Pending | — | — | REQ-005 |
| 2 | Update `manage_frontmatter.py` description | Pending | — | — | REQ-005 |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
