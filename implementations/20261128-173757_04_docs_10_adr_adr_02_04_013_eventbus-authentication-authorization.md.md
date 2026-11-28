## Goal
- Add one sentence to ADR-013 Decision Detail 12 recording that a body without `consumer_authorization` is rejected with HTTP 422 (`REQ-005` ADR wording; no decision changes).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: Decision Detail 12 in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.

## Assumptions
- Decision Detail 12 is at line 103 and Decision Detail 13 at line 107 of the ADR (checked at the Plan's evidence revision). DD12 rejects only the empty body `{}` and says a well-formed no-change body returns 200 with `changed: false`.
- The maintainer confirmed on 2026-11-28 that a body without `consumer_authorization` is rejected with 422; the sentence records that confirmation as a clarification, not a new decision, and adds no approval text.
- Overlap judgment (Step 2): the publication-boundary Plan (adrr002, one component-list line in "Implementation References") and the invariant coverage Plan (adrr003, Automated Tests table) also edit this ADR; the edits are in different sections, a sequencing dependency; this procedure is implemented first.

## Design decisions
- Append the sentence to DD12 rather than add a new Decision Detail, so numbering and cross-references (DD13 to DD18) are unchanged.

## Alternatives considered
N/A: one-sentence clarification.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Append to DD12 a sentence such as: a body that carries no `consumer_authorization` (only `expected_generation` or `ttl_seconds`) is also rejected with HTTP 422 and changes nothing; an explicitly present but unchanged `consumer_authorization` remains HTTP 200 with `changed: false`.

### Method
- Keep the DD12 numbering and bold lead-in; use MUST/MUST NOT style consistent with the neighbouring details; English only.

### Details
- Do not change DD13; its statement that an invalid `ttl_seconds` is rejected before the `expected_generation` comparison already matches the new code.
- Do not edit the Automated Tests table or the matrix here (adrr003).

## Compatibility considerations
N/A: wording clarification with no decision change.

## Security considerations
N/A: no credential or trust-boundary content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_invariant_matrix.py`.
- `uv run python tools/run_validation_gates.py` (documentation checkers per `rules/tool-gates.md`); `uv run python tools/generate_reference_table.py --check`.
- Deploy hand-off for the Plan: `scripts/` changed (procedure 01), so commit and push first, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision.

## Completion criteria
- DD12 states the metadata-only 422 and the unchanged-explicit-mapping 200 (`REQ-005`); no other decision text changed; the ADR checkers report no findings.

## Out of Scope
- The Automated Tests table, the index matrix, and the component list (adrr002 and adrr003); code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the clarifying sentence to Decision Detail 12 in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Pending | — | — | |
| 2 | Run the ADR and documentation checkers named in `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (ADR wording for the metadata-only rejection)
- **Source issue**: issues/20261125-103307_adrr001_admin-ttl-precedence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172318_adrr001_admin-ttl-precedence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173757
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
