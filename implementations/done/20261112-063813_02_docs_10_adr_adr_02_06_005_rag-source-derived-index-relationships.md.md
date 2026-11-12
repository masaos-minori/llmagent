## Goal

Bring ADR-005 into line with `rag_05_07`: set the `orphan_vec_count > 0` remediation to `rebuild_vec`, remove the "never aborts / skips it" startup-check claim, drop the Decision-11 sentence that the MCP path issues the SQL itself, and add a pending maintainer approval record for the decision-text edits (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Decision 10 (line 79) currently says "`orphan_vec_count > 0`: re-ingest the target documents".
- The startup-check paragraph (line 182) currently says "does not abort startup; a timeout or an unexpected failure of the check skips it".
- Decision 11 (line 81) currently says "The MCP path issues the same statements itself rather than calling the shared helper".
- Decision-text edits require a maintainer approval record in the same change (`governance_05`); the record is marked pending, never fabricated (`UNK-05`).
- Gate resolved 2026-11-12: the identity-gate removal landed (`b217f999b`); the frozen rmcompat001 Plan (`plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`) lists `rag_05_07` as a reference file only, not a target; `tools/plan_dependency_order.py` reports this Plan Ready with no gate.

## Design decisions
- Change Decision 10's `orphan_vec_count > 0` line to `rebuild_vec` (matching `rag_05_07`).
- Reword the startup-check paragraph (line 182) so it states what ADR-005 owns and references `rag_05_07` for severity/startup behavior instead of asserting it never aborts.
- In Decision 11, drop the sentence about the MCP path issuing the statements itself (the MCP path now calls the helper per the seq 07 procedure).

## Alternatives considered
- Leaving Decision 10 on "re-ingest": rejected by `REQ-002`; ADR-005 must agree with the single policy source.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`

### Procedure
1. Edit Decision 10 (line 79): `orphan_vec_count > 0` → `rebuild_vec`.
2. Reword the startup-check paragraph (line 182): remove "does not abort startup; a timeout or an unexpected failure of the check skips it"; state the owned behavior and reference `rag_05_07` for severity and startup handling.
3. Edit Decision 11 (line 81): delete the sentence that the MCP path issues the statements itself.
4. Add a pending maintainer approval record for the Decision 10/11 text changes.

### Method
Evidence checked: line 79 ("re-ingest the target documents"), line 182 ("does not abort startup; a timeout or an unexpected failure of the check skips it"), line 81 (Decision 11 second sentence). Apply the three edits above; keep INV-02/INV-05 (deletion order) intact.

### Details
- The startup-check reword states current behavior (code warns and continues) without approving a fail-open ADR-004 does not allow (`UNK-01`).
- Approval record is marked pending and reported, never written as a maintainer statement (`UNK-05`).
- Verified 2026-11-12: the three evidence lines (79, 81, 182) match the current file. Record pattern (adrrev016 precedent): a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record; approver, date, and scope are not recorded and no reviewer name is written. Overlap: `implementations/20261112-123653_04_docs_10_adr_adr_02_06_005_rag-source-derived-index-relationships.md.md` (adrrev016) adds its own separate pending line for Decision 8; different decisions, compatible.

## Compatibility considerations
- N/A: ADR decision-text clarification; cross-checked against the invariant matrix and index.

## Security considerations
- N/A: no behavioral change; the deletion-order invariant (INV-02/INV-05) is preserved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` — pass (preservation reports only the intended ADR-005 text changes).

## Completion criteria
- ADR-005 Decision 10 gives `rebuild_vec` for `orphan_vec_count > 0`; the startup-check paragraph no longer asserts it never aborts or is skipped; Decision 11 no longer records the duplicated SQL; INV-02/INV-05 still hold; a pending approval record is added (`AC-2`, `AC-3`, `AC-4`).

## Out of Scope
- Any change to the deletion order or the shared helper (handled by the seq 07 procedure); other ADRs.

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
- **Requirement ID**: `REQ-002` (`orphan_vec_count > 0` → `rebuild_vec`), `REQ-003` (startup-check no longer claims it never aborts), `REQ-004` (Decision 11 drops the duplicated-SQL sentence)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
