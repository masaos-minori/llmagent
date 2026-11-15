## Goal
- Record the read-only probe policy and the `missing` DB condition in ADR-008.

## Scope
**Release unit**: N/A: not part of a release unit (plan Phase 4 docs; lands after the unit's code/test documents)

- In scope: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` — condition enumerations (Decision Detail #14, INV-13), the INV-16 dry-run test citation, and the INV-13 test row (REQ-007).

## Assumptions
- Line citations 123/257/308 are the pre-003 tree: Plan 003's docs procedure `implementations/20261115-082016_5_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md` lands first (Decision Detail #21 + one Recovery Policy Matrix row insert lines before them) — anchor by content: the Decision Detail #14 sentence "Physical recovery must classify DB state (healthy/corruption/...", the INV-13 invariant line, and the INV-16 test row whose citation parenthetical ends "is switched to WAL when opened and is not covered" (plan Correction 1).
- The new test IDs referenced in steps 3-4 exist only after Plan 004's Phase 3 test documents land (companions `20261115-084603_5`); docs edits run after them (plan step order), so `check_docs_consistency.py` resolves them.

## Design decisions
- `missing` joins the existing six-way classification enumerations verbatim rather than getting a new invariant: the classification requirement already exists (#14, INV-13); only its domain was incomplete (the Issue's core defect).
- The WAL-conversion caveat is deleted outright rather than annotated: after REQ-001..REQ-003 the behavior it describes no longer exists, and an ADR should not record retired gaps.

## Alternatives considered
- A new Decision Detail for probe purity: rejected — Decision Detail #16 (staged candidate) and #18 (dry-run) already state the write-side boundaries; probe purity is the classification mechanism the existing #14/INV-13 sentences govern, and Plan 004's scope row names exactly these anchors.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Decision Detail #14: extend the classification enumeration "(healthy/corruption/lock contention/permission failure/invalid format/unknown)" with `/missing` (REQ-007/AC-4).
2. INV-13: extend the invariant's classification list "(healthy / corruption / lock contention / permission failure / invalid format / unknown)" with " / missing" (REQ-007/AC-4).
3. INV-13 test row: append `tests/db/test_db_recovery.py::test_recover_missing_live_db_reports_missing_database` (new) to the listed regression citations (REQ-007).
4. INV-16 dry-run row: remove "; a rollback-journal file is switched to WAL when opened and is not covered" from the citation parenthetical and append the now-covered rollback-journal probe test `tests/db/test_db_recovery.py::test_run_integrity_check_keeps_rollback_journal_mode` (new) to the row's citations (REQ-007/AC-4).

### Method
- Four in-place text edits; table column structure unchanged.

### Details
- Vocabulary: the docs gain only the condition token `missing` (new); the action token `missing_database` belongs to `db_07` (companion `_8`) — ADR bodies name conditions, `db_07` carries the action/state contract (per Plan 002 consumer-scan record).
- Do not touch Plan 003's landed Decision Detail #21 or its matrix rows; edits are adjacent-but-disjoint (plan overlap record).

## Compatibility considerations
- Docs-only; `check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain db` gates apply.
- Test-ID citations must match landed test names exactly (`check_docs_consistency.py` cross-checks symbol references).

## Security considerations
- N/A: documentation text only.

## Rollback considerations
- Checkout revert; revert with the unit's code/test documents if the whole unit rolls back.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` → no findings (AC-4).
- `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` → no findings.
- `uv run python tools/check_docs_quality.py` → exit 0.

## Completion criteria
- Both enumerations list `missing`; the INV-13 row cites the MISSING test; the INV-16 row no longer carries the WAL-conversion caveat and cites the rollback-journal invariance test.

## Out of Scope
- `db_07` action/condition text (companion `20261115-084603_8`).
- Plan 003's retention/quarantine additions (already landed).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-113615 | 20261115-113615 | 4 edits: missing in #14/INV-13 enumerations, INV-13/INV-16 test citations, WAL caveat removed; ceiling 37175->37291; (new) markers omitted because tests already landed |
| 2 | Add or update tests per Validation plan | Completed | 20261115-113615 | 20261115-113615 | N/A: docs-only; cited tests landed via companion _5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-113615 | 20261115-113615 | check_docs_consistency --domain db clean, structure green after ceiling re-record, quality exit 0, stale_detector clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-113615 | 20261115-113615 | N/A: this file is the documentation |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md