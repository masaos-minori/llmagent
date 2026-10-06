## Goal

Update `governance_04` section 8 / GV-005 row to reflect any-level detection and `related` format validation; note the ADR exception stays until `rel002`. (REQ-003, REQ-004 / AC-1)

## Scope

- Update section 8 / GV-005 row to reflect:
  - Body `Related Documents` detection at ANY heading level (not just `##`)
  - `related` format validation (basenames ending in `.md`)
  - ADR exception remains until `rel002`
- Change GV-005 status from Warning to blocking (if appropriate)

## Assumptions

- The current GV-005 status is Warning (non-blocking) — may need to be changed to blocking
- The strengthened tool behavior (any-level detection + format validation) is the adopted policy

## Design decisions

- Update the GV-005 row to describe the strengthened check behavior
- Consider changing GV-005 from Warning to blocking (structural checks should block)
- Note the ADR exception remains until `rel002`

## Alternatives considered

- Keeping GV-005 as Warning — rejected because structural checks should block (matches UNK-01 recommendation)

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Update section 8 / GV-005 row to describe any-level detection
2. Add `related` format validation description
3. Note the ADR exception remains until `rel002`
4. Consider changing GV-005 status from Warning to blocking

### Method

- Edit the relevant section(s) directly
- Ensure the updated text matches the strengthened tool behavior

### Details

**Before:**
GV-005 currently describes detection of `## Related Documents` headings only (non-blocking).

**After:**
The updated GV-005 row describes:
- Detection of body `Related Documents` / `Related Docs` / `Related Chapters` headings at ANY level in non-ADR documents
- `related` format validation (basenames ending in `.md`)
- ADR exception remains until `rel002`
- Status changed from Warning to blocking (if appropriate)

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the governance rule set per `routing.md` Docs mapping
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- No security implications — this is a governance rule clarification
- The updated text aligns the documented contract with the implemented enforcement

## Rollback considerations

- Reverting would restore the outdated GV-005 description
- If the owner later changes the blocking/non-blocking decision, this status would need revision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Documentation review | Read updated section vs `check_docs_structure.py` enforcement | Any-level detection described; format validation noted; ADR exception noted |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- GV-005 row describes any-level detection
- `related` format validation described
- ADR exception timeline noted (until `rel002`)
- Status appropriately updated (Warning → blocking if appropriate)
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
| 1 | Update GV-005 row in `governance_04` | Pending | — | — | REQ-003, REQ-004 |
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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
