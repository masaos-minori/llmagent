## Goal

Update `governance_02` to state that `related:` is the single related-document list for non-ADR documents; body `Related Documents` not used there; contextual/navigation links allowed; ADR exception remains until `rel002`. (REQ-003 / AC-1)

## Scope

- Update the `related` field description to state `related:` is the single related-document list for non-ADR documents
- State that a body `Related Documents` section is not used in non-ADR documents
- Clarify that contextual links and purpose-specific navigation sections (`Reading Order`, `Related ADRs`) stay
- Note that the ADR exception remains until `rel002`

## Assumptions

- The current governance text already states the single-store rule (per Background item 32); only wording updates are needed
- The ADR exception is explicitly stated and will remain until `rel002`

## Design decisions

- Adopt the recommended option: keep the current governance structure and update wording only
- Preserve the nuance: preservation of the ADR `## Related Documents` body block continues until `rel002`; contextual prose links and purpose-specific navigation are explicitly allowed

## Alternatives considered

- Rewriting the entire governance section — rejected because only wording updates are needed

## Implementation

### Target file

`docs/00_governance/governance_02_documentation-metadata.md`

### Procedure

1. Update the `related` field description to state it is the single related-document list for non-ADR documents
2. Add explicit statement that body `Related Documents` sections are not used in non-ADR documents
3. Clarify that contextual links and purpose-specific navigation sections (`Reading Order`, `Related ADRs`) are allowed
4. Note the ADR exception remains until `rel002`

### Method

- Edit the relevant section(s) directly
- Ensure the updated text matches the strengthened tool behavior

### Details

**Before:**
The current `related` field description states the single authoritative store but does not explicitly prohibit body `Related Documents` sections in non-ADR documents, nor does it clarify the ADR exception timeline.

**After:**
The updated description explicitly states:
- `related:` is the single related-document list for non-ADR documents
- Body `Related Documents` / `Related Docs` / `Related Chapters` sections are not used in non-ADR documents
- Contextual prose links and purpose-specific navigation (`Reading Order`, `Related ADRs`) are explicitly allowed
- The ADR `## Related Documents` body block requirement remains until `rel002`

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the governance rule set per `routing.md` Docs mapping
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- No security implications — this is a governance rule clarification
- The updated text aligns the documented contract with the implemented enforcement

## Rollback considerations

- Reverting would restore the ambiguity between the documented rule and the enforced behavior
- If the owner later chooses a different policy for body sections, this wording would need revision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_02_documentation-metadata.md` | Documentation review | Read updated section vs `check_docs_structure.py` enforcement | Single-store rule explicit; body Related prohibited; ADR exception noted |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- `related:` described as the single related-document list for non-ADR documents
- Body `Related Documents` prohibition explicitly stated for non-ADR documents
- Contextual/navigation link allowance clarified
- ADR exception timeline noted (until `rel002`)
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
| 1 | Update `related` field description in `governance_02` | Pending | — | — | REQ-003 |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md
