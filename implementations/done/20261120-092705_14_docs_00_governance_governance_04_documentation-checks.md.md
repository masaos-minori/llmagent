## Goal

- Complete the GV-024 Tool column so it names `check_adr_reference.py` as the owner of the front matter cross-check half, and document the generated header-list mechanism in §18.

## Scope
**Release unit**: N/A: not part of a release unit

- REQ-010 (GV-024 Tool column registration fix matching §12) and REQ-012 (§18 wording for the generated list mechanism and its guard).

## Assumptions
- Verified current source: the GV-024 row's Tool column lists only `check_adr_authority.py`, while §12 documents that `check_adr_reference.py` owns the `FRONTMATTER_DIVERGENCE` cross-check (Step 2); §18 is the current "ADR Section Header Compliance" section number (the §17/§18 confusion was confirmed in Step 2).
- The generated list itself lives in governance_01 (its own row); this row only documents the mechanism.

## Design decisions
- Keep governance_04 as the registry-level description: §18 gains one short paragraph naming the generator (`generate_adr_authority.py`), the guard block, and the checker constant as the normative source — no heading list is duplicated here (AC-5 keeps exactly one readable list).

## Alternatives considered
- Listing the headings in governance_04 §18 as well — rejected: it would recreate the multiple-sources problem the Plan closes.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
- Add `check_adr_reference.py` to the GV-024 row's Tool column, keeping the row's existing cell format (REQ-010).
- Extend §18 "ADR Section Header Compliance" with the generated-list mechanism wording: readable list generated into the governance_01 guard block from `check_adr_structure.py`'s constant, drift gated by `generate_adr_authority.py --check` (REQ-012).
### Method
- Table-cell and section-text edits only.
### Details
- Match the existing Tool-column syntax (backticked tool names, comma-separated) so the checker-to-rule mapping parsers keep reading the row.

## Compatibility considerations
- `tools/check_tool_descriptions_sync.py` must pass after the row change (it is one of this row's validators); docs structure/quality checks must stay green.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — descriptions and governance rows agree (AC-3).
- Docs checkers named in `routing.md` (`check_docs_structure.py`, `check_docs_quality.py`) — no findings; the §18 anchor referenced by governance_01 resolves.

## Completion criteria
- GV-024 names both tools, §18 states the generated-mirror mechanism, and both validators pass (AC-3, AC-5).

## Out of Scope
- governance_01's block and wording (its own row) and any tool code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `check_adr_reference.py` to the GV-024 Tool column (REQ-010) | Completed | 20261120 | 20261120 | — |
| 2 | Document the generated-list mechanism in §18 (REQ-012) | Completed | 20261120 | 20261120 | — |
| 3 | Run `check_tool_descriptions_sync.py` and the docs checkers named in `routing.md` | Completed | 20261120 | 20261120 | — |

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
- **Requirement ID**: REQ-010 (GV-024 Tool column), REQ-012 (§18 generated-list mechanism)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
