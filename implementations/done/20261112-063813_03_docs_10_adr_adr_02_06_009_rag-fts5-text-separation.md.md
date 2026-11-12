## Goal

Resolve the overlapping invariant pair and the mismatched failure label in ADR-009: merge INV-09 into INV-04, state the normalization-failure result and existing-chunk behavior, relabel the "Fail-Fast" condition to match the code (skip the file, continue), and add a pending maintainer approval record (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- INV-04 (line 161) and INV-09 (line 166) both describe non-normalized text having `normalized_content = NULL` and being indexed by `content`; they overlap.
- The Failure Policy "Fail-Fast Conditions" block (lines 172-175) lists a file-level skip as Fail-Fast, but `ChunkSplitter.process_all()` catches the error and continues (`scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_japanese.py` raises `TokenizationError`).
- Stored chunks of a re-normalization-failed file are left unchanged (the failure precedes the force prune).
- Folding INV-09 into INV-04 keeps the other invariant numbers stable; the index cites invariants by number (`UNK-04`).
- Decision-text edits need a pending maintainer approval record, never fabricated (`UNK-05`).
- Gate resolved 2026-11-12: the identity-gate removal landed (`b217f999b`); the frozen rmcompat001 Plan (`plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`) lists `rag_05_07` as a reference file only, not a target; `tools/plan_dependency_order.py` reports this Plan Ready with no gate.

## Design decisions
- Delete INV-09 and fold its content into INV-04 (extend INV-04 to cover Markdown heading chunks explicitly). Do not renumber the remaining invariants.
- Reword the "Fail-Fast Conditions" entry: state the result (no chunks for the failed file, remaining files processed, stored chunks of that file unchanged) and relabel the condition so it no longer reads as Fail-Fast.
- Update the Verification table and the no-dedicated-test line for the merged invariant.

## Alternatives considered
- Renumbering INV-09 out of existence and shifting later numbers: rejected by `UNK-04`; the ADR index cites invariants by number, so other numbers must stay stable.

## Implementation
### Target file
`docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`

### Procedure
1. Merge INV-09 (line 166) into INV-04 (line 161): keep one invariant covering non-normalized text (`normalized_content = NULL`, indexed by `content`), naming Markdown heading chunks.
2. Reword the "Fail-Fast Conditions" block (lines 172-175): state the file-skip-and-continue result and existing-chunk behavior; remove the "Fail-Fast" label.
3. Update the Verification table and the no-dedicated-test line for the merged invariant.
4. Add a pending maintainer approval record for the decision-text edits.

### Method
Evidence checked: INV-04 line 161, INV-09 line 166, Failure Policy lines 172-175. Confirm the ADR index (`docs/10_adr/adr_01_index.md`) cites INV-04/INV-09; if the merge leaves a dangling citation, add the index through `tools/amend_plan.py` (fallout, `UNK-04`).
- Verified 2026-11-12: the index cites only ADR-009 INV-07 and INV-10, so folding INV-09 leaves no dangling citation (`UNK-04`; the checkers confirm). The cross-reference near line 187 ("see Fail-Fast Conditions") must be updated to the relabeled section name.

### Details
- The relabel documents current code behavior; changing that behavior is out of scope.
- After the edit, run `check_adr_invariant_matrix.py` and `check_adr_structure.py`; if the index needs the merged invariant, amend it (`UNK-04`).

## Compatibility considerations
- N/A: ADR structural clarification; the invariant matrix and index are re-checked after the edit.

## Security considerations
- N/A: no behavioral change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` — pass (preservation reports only the intended ADR-009 text changes).

## Completion criteria
- ADR-009 has no overlapping invariants (INV-09 folded into INV-04, other numbers stable), states the normalization-failure result and existing-chunk behavior, the failure label matches the code, and a pending approval record is added (`AC-6`).

## Out of Scope
- Changing the normalization-failure behavior itself; other ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-12 | 2026-11-12 | Gate resolved 2026-11-12 (see Blocker Log) implemented 2026-11-12 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-12 | 2026-11-12 | Gate resolved 2026-11-12 (see Blocker Log) implemented 2026-11-12 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | rmcompat001 phase-all gate (`rag_05_07` startup-paragraph rewrite) | Yes | 2026-11-12 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (merge INV-04/INV-09, state normalization-failure result and existing-chunk behavior, relabel the Fail-Fast condition)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
