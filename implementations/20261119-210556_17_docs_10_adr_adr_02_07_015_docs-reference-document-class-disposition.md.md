## Goal

- Record the manifest contract this plan establishes in ADR-015 - the field set, the new generated document in the generated-document list, and the owner's dated approval (`REQ-003`, `REQ-008`, `REQ-014`, `REQ-015`; `AC-011`, `AC-013`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- The owner approved the field-set change on 2026-11-19 (`D-11`, `D-12`, `D-13`); the approval record states that decision and names this plan.
- The existing `Current Decision Approval (pending)` bullet (line 158) records a different change (the `component_mandatoriness` status correction and the `agent_08_04` addition) tracked by AAL-017, and stays unchanged.

## Design decisions

- ADR-015 is the authority that defines the Generated-class Reference document and its manifest extension, so the new contract is written there rather than only in code comments (`D-02`, `D-12`).
- No gate value, invariant, or authority edge in `docs/10_adr/adr_01_index.md` changes; this document records vocabulary, it does not reclassify anything.

## Alternatives considered

- Leave the ADR describing the old field set and let the code carry the change: rejected - the ADR is the declared contract for this document class, and an unrecorded contract change is the defect UNK-02 named.
- Invent a maintainer approval date: forbidden by the project rule; the record states the owner decision of 2026-11-19 with this plan as its reference.

## Implementation
### Target file
`docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
### Procedure
1. Extend the Contract Manifest Extension section (lines 129-135) with the field set this plan establishes: enumerated `gate` values, the `check_type` field, the route `method` field, the removed `health_contracts` `disposition`, and envelope version 2.
2. Add `docs/23_agent/agent_14_reference-api-subpackages-generated.md` to the generated-document list for the `agent` domain (lines 120-126).
3. Add a dated approval record for this change to the Approval Record section, naming this plan and the 2026-11-19 owner decision, beside the existing pending bullet rather than replacing it.

### Method
- ADR text edits only; the ADR stays `Accepted` and its existing approval history is not rewritten.

### Details
- Generated-document list today names one agent document (line 122); after this row it names both agent indexes.
- The Contract Manifest Extension section also carries the fact-manifest list and the deferred `adr_authority` and `architecture_assumptions` notes, which stay as they are.

## Compatibility considerations

- `tools/check_adr_reference.py` and `tools/check_docs_quality.py` gate this file; `tools/check_adr_preservation.py` reports anything beyond the intended change.
- The record must stay consistent with the schema written by row 03 and the regenerated manifests of rows 18-28.

## Security considerations

- N/A: no credential or approval-authority change; the record names the repository owner decision, per `docs/00_governance/` conventions.

## Rollback considerations

- Revert the commit; the ADR text returns to its previous state.

## Validation plan

- `uv run python tools/check_adr_reference.py && uv run python tools/check_docs_quality.py` — no reference or quality finding (docs: ADR gates)
- `uv run python tools/check_adr_preservation.py` — only the intended edits reported (docs: intended-change check)

## Completion criteria

- ADR-015 states the field set, lists both agent generated indexes, and carries a dated approval record naming this plan.

## Out of Scope

- Any change to `docs/10_adr/adr_01_index.md` gate values.
- Resolving the AAL-017 pending approval item, which belongs to another change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the Contract Manifest Extension section and the generated-document list | Pending | — | — | ADR text |
| 2 | Add the dated approval record | Pending | — | — | owner decision 2026-11-19, names this plan |
| 3 | Run `tools/check_adr_reference.py` and `tools/check_docs_quality.py` | Pending | — | — | documentation gates |

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
- **Requirement ID**: `REQ-003` (the matrix Type-column value is recorded in its own enumerated field (check_type), with a name that matches the column's meaning), `REQ-008` (health_contracts carries no generator-constant disposition), `REQ-014` (the manifest envelope version is bumped once, coordinated with the schema change), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`
