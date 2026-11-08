## Goal
Clarify ADR-008 without changing migration behavior, ownership, or recovery policy: compatible Scope and Out of Scope, automatic versus manual recovery wording, authoritative file versus canonical and derived tables, per-amendment approval mapping, and a file size at or below the ceiling (REQ-001 to REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit
Edits ADR-008 only: Context > Constraints migration sentence, Out of Scope migration line, Decision Details item 1, INV-01, the Recovery Policy Matrix wording for the workflow and eventbus databases, the historical migration Amendment pointers, the Approval Record, and condensation of historical text.

## Assumptions
- The forward-only premise in the Issue is stale: the migration machinery was removed, so all four databases follow the current-only schema policy (verified against the ADR superseded notice and the db_03 current-schema section).
- ADR-008 is the sole target of this Plan, but the adrver001 Plan later edits the same ADR (invariant verification wording in its matrix row and verification text). Sequencing dependency, not a conflict: this procedure runs first; adrver001 starts from the condensed file.
- The file is 34604 bytes against a 34206-byte ceiling in `tools/check_docs_structure.py`, so the structure check already fails before editing; REQ-006 requires the result to be at or below the ceiling.
- Rewording INV-01 makes `check_adr_preservation.py` report an ERROR; this is intended and is explained, not suppressed. `tools/check_db_separation.py` must still pass.

## Design decisions
- Describe the authoritative database file, the canonical tables (documents, chunks) and the derived indexes (FTS5, Vector Index rebuilt from chunks) in one consistent sentence reused in INV-01, item 1 and the matrix cell.
- Cite superseded plans by identifier only (no done/ paths, no requirement identifiers, no Traceability heading); active-document quality rules reject those markers.

## Alternatives considered
N/A: Plan decisions already fix the approach (condense, do not move content).

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Phase 1: Align the Constraints migration sentence and the Out of Scope migration line: current-only schema policy in scope; migration mechanism design and schema-version mappings out of scope; forward-only machinery historical.
2. Phase 2: In the matrix replace "none" with "no automated ..." for the workflow and eventbus diagnosis and recovery-source cells, leaving the restore allowed/prohibited rows unchanged; reword INV-01, item 1 and the System of record cell for the RAG database.
3. Phase 3: Replace the stale plan path in the Amendment with the dbmig001 identifier; describe db_03 sections 8a and 8b as they are now or mark them superseded; add the per-amendment approval mapping to the Approval Record, stating where no per-amendment record exists.
4. Phase 4: Condense superseded or duplicated historical text until `wc -c` reports at most 34206 bytes without dropping any decision, invariant, reference or approval evidence; read the whole ADR afterwards.

### Method
Documentation edit of one file in four passes; measure the size after each pass and keep a record of what was condensed.

### Details
- If the size ceiling cannot be met without removing a decision, invariant, reference, or approval evidence, stop and report; do not raise the ceiling (out of scope).
- Keep the H2 sequence, invariant identifiers and anchors.
- Do not invent approval status; map only evidence that exists in the source plans and the index.

## Compatibility considerations
Documentation only; no schema, recovery, or ownership behavior changes.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` (no size finding for this file), `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_adr_preservation.py`: only the intended INV-01 finding; `check_adr_structure.py`, `check_adr_invariant_matrix.py`: pass
- `uv run python tools/check_db_separation.py` and `uv run pytest tests/tools/test_check_db_separation.py`: pass

## Completion criteria
- Out of Scope and the Constraints sentence agree; matrix cells say "no automated" where they said "none".
- INV-01, item 1 and the matrix cell name file, canonical tables and derived indexes consistently.
- The Approval Record maps each amendment to existing evidence or states that none exists.
- The file is at most 34206 bytes.

## Out of Scope
- Schema or migration implementation changes; recovery tooling.
- The size ceiling constant; cross-file verification updates (adrver001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply Phases 1 to 3 of Implementation > Procedure | Pending | — | — |  |
| 2 | Condense historical text to the size ceiling (Phase 4) | Pending | — | — |  |
| 3 | Run the documentation checkers named in the Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` to `REQ-006` (scope wording, recovery wording, canonical versus derived, approval mapping, pointers, size)
- **Source issue**: issues/20261107-050703_adrdb001_clarify-adr-008-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092007_adrdb001_clarify-adr-008-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111456
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
