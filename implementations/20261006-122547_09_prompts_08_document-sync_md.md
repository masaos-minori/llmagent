## Goal

Remove any stale statement of the old rule from `prompts/08_document-sync.md`. (REQ-005 / AC-5)

## Scope

- Remove any stale statement of the old rule (second-level heading detection only) from `prompts/08_document-sync.md`

## Assumptions

- The current prompt carries the old rule text (second-level heading detection only)
- The updated prompt must match the new rule text

## Design decisions

- Remove the stale statement and replace it with the new rule text
- Ensure the prompt's authoring guidance matches the current rule

## Alternatives considered

- Keeping the old prompt — rejected because it would be stale and misleading

## Implementation

### Target file

`prompts/08_document-sync.md`

### Procedure

1. Remove any stale statement of the old rule
2. Add the new rule text if needed

### Method

- Edit the relevant section(s) directly
- Ensure the updated text matches the new rule behavior

### Details

**Before:**
The prompt carries the old rule text (second-level heading detection only).

**After:**
The updated prompt states:
- Body `Related Documents` / `Related Docs` / `Related Chapters` headings are not allowed in non-ADR documents at ANY level
- `related:` is the single related-document list for non-ADR documents
- Contextual prose links and purpose-specific navigation (`Reading Order`, `Related ADRs`) are explicitly allowed
- The ADR `## Related Documents` body block requirement remains until `rel002`

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the authoring guidance per `routing.md` Docs mapping
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- No security implications — this is a prompt documentation update
- The updated prompt helps prevent misuse of the authoring process

## Rollback considerations

- Reverting would restore stale prompt content
- If the owner later changes the rule, this prompt would need revision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `prompts/08_document-sync.md` | Documentation review | Read updated section vs new rule text | No stale statements; new rule text present |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- Stale statement of the old rule removed
- New rule text present
- No stale statements of the old rule remain

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
| 1 | Remove stale statement from `prompts/08_document-sync.md` | Pending | — | — | REQ-005 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: prompts/08_document-sync.md
