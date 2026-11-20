## Goal

- Add ADR-017 to ADR-007's front matter `related` list and its `## Related ADRs` section, closing the confirmed incomplete-list gap without any model change.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-017 (ADR-007 lists ADR-017) — ungated: the intentional `ADR-007 --Reference--> ADR-017` edge already exists in the model, so listing it satisfies ADR-016 Decision 7.

## Assumptions
- `## Related ADRs` currently lists only ADR-002 and ADR-004 (line 343-346, verified in Step 2); Decisions 9/10 rely on ADR-017's authentication rules.
- A front matter related edge must exist in the model (cross-check rule); the existing intentional `Reference` edge satisfies this, so no `config/adr_authority.toml` edit belongs here.

## Design decisions
- N/A: the addition is a direct conformance fix with no design choice.

## Alternatives considered
- N/A: single-line conformance addition.

## Implementation
### Target file
`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
### Procedure
- Add the `adr_02_03_017_mcp-authentication.md` entry to the front matter `related` list and the `ADR-017` entry to `## Related ADRs`, matching the existing entry format of each list (REQ-017).
### Method
- Direct text edits in the two lists only.
### Details
- N/A: no inference beyond the two verified list locations.

## Compatibility considerations
- N/A: revert the commit.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py` — no `FRONTMATTER_DIVERGENCE` findings (the listed edge exists in the model).
- Docs checkers named in `routing.md`.

## Completion criteria
- Both lists name ADR-017 and the front matter/model cross-check passes (AC-2).

## Out of Scope
- Any model change and any edit to ADR-007's decision text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add ADR-017 to the front matter and `## Related ADRs` lists (REQ-017) | Completed | 20261120 | 20261120 | — |
| 2 | Run `check_adr_reference.py` and the docs checkers named in `routing.md` | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-017 (ADR-007 lists ADR-017)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
