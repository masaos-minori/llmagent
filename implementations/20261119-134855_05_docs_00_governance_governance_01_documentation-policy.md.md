## Goal

- Prepare — do not merge — the Resolution Matrix owner-list change for `mcp.component-mandatoriness` in `docs/00_governance/governance_01_documentation-policy.md` per the Plan (`REQ-017`), citing ADR-004 Group 3 item 13 and ADR-017.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the prepared proposal text for the Matrix `security-policy` row (line 134), the approval-gate record, and the reconciliation with adrchk011.
- Out of scope: applying the Matrix edit before approval; any change to the registry row `mcp.component-mandatoriness` (`config/documentation_canonical_sources.toml` lines 66–71), which stays byte-identical (`AC-13`).

## Assumptions

- No maintainer approval record exists (UNK-02); merge requires an explicit owner decision recorded in the Blocker Log.
- adrchk011 (`issues/20261117-123011_adrchk011_adr-approval-governance.md`) has no plan yet; its governance scope may cover the same Matrix change (UNK-01) — adrchk011 must be processed first.
- Verified 2026-11-19: registry lines 66–71 register `mcp.component-mandatoriness` as `security-policy` with `registry/component_mandatoriness.yaml` as source; the Matrix `security-policy` row (governance_01 line 134) names only Accepted security ADRs `adr_02_??_007_*.md`, `adr_02_??_012_*.md`, `adr_02_??_013_*.md`; ADR-004 Group 3 item 13 cites `registry/component_mandatoriness.yaml` as the component-mandatoriness authority.

## Design decisions

- Proposal form: a prepared diff recorded in this document (below), not an applied edit — the target file changes only after maintainer approval (Plan Phase 3; `AC-13`).
- Proposed content: extend the `security-policy` row's canonical-source-kind list to include the ADR-004 and ADR-017 ADR files (`adr_02_??_004_*.md`, `adr_02_??_017_*.md`), so the registry row's cited yaml file is backed by owners that actually authorize it.

## Alternatives considered

- Apply the Matrix edit now and file a follow-up approval issue — rejected: the Plan's Out-of-Scope explicitly forbids applying the owner change without approval.

## Implementation
### Target file
`docs/00_governance/governance_01_documentation-policy.md`
### Procedure
1. Draft the proposed replacement for the Resolution Matrix `security-policy` row (line 134): canonical source kind becomes "Accepted security ADRs (`docs/10_adr/adr_02_??_004_*.md`, `adr_02_??_007_*.md`, `adr_02_??_012_*.md`, `adr_02_??_013_*.md`, `adr_02_??_017_*.md`)", with the Notes column citing ADR-004 Group 3 item 13 (component mandatoriness registry) and ADR-017.
2. Record the proposal and the approval gate (UNK-02) in this document's Blocker Log; keep the target file unchanged until the decision is recorded.
3. After adrchk011 is planned, reconcile: if adrchk011's plan covers the same row, merge the proposals rather than duplicating edits (Plan dependency bullet, Phase 3).
4. Only on maintainer approval: apply the drafted row edit and re-run the consumers listed in Compatibility.

### Method
- Proposal-only phase: the deliverable is the exact proposed row text plus citations, gated by the Blocker Log; no file edit ships in this phase.

### Details
- Proposed row (prepared, unapplied):
  - `| security-policy | Security Constraints | Security constraints and mandates | Accepted security ADRs (\`docs/10_adr/adr_02_??_004_*.md\`, \`adr_02_??_007_*.md\`, \`adr_02_??_012_*.md\`, \`adr_02_??_013_*.md\`, \`adr_02_??_017_*.md\`) | Audit Evidence | Known Issues | Component mandatoriness: ADR-004 Group 3 item 13 names \`registry/component_mandatoriness.yaml\`; ADR-017 |`

## Compatibility considerations

- Resolution Matrix consumers: `tools/check_canonical_source_registry.py`, `tools/check_canonical_source_conflicts.py`, adr_authority docs; after an approved merge, re-run both checkers plus `tools/check_canonical_document_prose.py` (all exit 0) and `tools/generate_adr_authority.py --check`.
- The registry row stays untouched until approval, so no checker behavior changes in the proposal phase (`AC-13`).

## Security considerations

- N/A: governance document proposal; no code or trust-boundary change.

## Rollback considerations

- Proposal phase: nothing applied, nothing to roll back. Post-approval merge: single-commit revert of the Matrix row; registry row untouched throughout.

## Validation plan

- `git diff docs/00_governance/governance_01_documentation-policy.md` is empty and `config/documentation_canonical_sources.toml` lines 66–71 are byte-identical before approval (`AC-13`).
- Blocker Log entry exists with the approval gate (Plan Phase 3 step).
- Post-approval (future): both checkers and `generate_adr_authority.py --check` exit 0; full sequence per `rules/toolchain.md`.

## Completion criteria

- `AC-13` holds: the proposal exists as prepared Matrix edit text with citations, is not merged without approval, and the registry row is unchanged; the approval gate is recorded in the Blocker Log.

## Out of Scope

- Applying the edit without approval; GV-code renumbering (adrchk011); the registry row itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Draft the proposed `security-policy` Matrix row with citations (`REQ-017`) | Pending | — | — | |
| 2 | Record the approval gate in the Blocker Log; reconcile with adrchk011's plan when it exists | Pending | — | — | UNK-01/UNK-02 |
| 3 | Apply the edit only after maintainer approval, then re-run consumers | Blocked | — | — | Awaiting maintainer decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | `REQ-017` merge requires explicit maintainer approval (UNK-02); adrchk011 plan must be checked first (UNK-01) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-017` (approval-gated Matrix owner proposal)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `docs/00_governance/governance_01_documentation-policy.md`
