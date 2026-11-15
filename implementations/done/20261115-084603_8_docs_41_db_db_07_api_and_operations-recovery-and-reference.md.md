## Goal
- State the read-only probe semantics and the `missing_database` action in the recovery contract docs.

## Scope
**Release unit**: N/A: not part of a release unit (plan Phase 4 docs; lands after the unit's code/test documents)

- In scope: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — `DbCondition` enumeration text, probe semantics, and the result-contract action/state additions (REQ-007).

## Assumptions
- Content anchors, not line numbers: Plan 002's docs procedure (`20261115-080732_3`) and Plan 003's docs procedure (`20261115-082016_4`) land first and have already edited the diagnosis bullets and the recovery-contract bullets (re-read the landed wording before editing; the pre-landing citations `:41` enum sentence, `:45-52` diagnosis bullets, `:65-66` result contract are reference points only) (plan Correction 1).
- Plans 008/009 edit this file later in the batch (008 section-12 lifecycle text, 009 section 12 drill artifacts) — 004 keeps its edits in the diagnosis/contract sections (plan overlap record: 004 owns the probe/dry-run sections).

## Design decisions
- One new diagnosis bullet for the missing-file condition plus one probe-semantics sentence, instead of a new subsection: keeps the shared file's bullet structure stable for the three other plans' disjoint edits (same rationale as Plan 003's docs procedure).

## Alternatives considered
- Documenting MISSING only in the action contract: rejected — `db_07:41` states the enum is the classification contract ("callers distinguish outcomes by the `DbCondition` value"); omitting `MISSING` there would leave the enumeration wrong even with the action added.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Enum sentence (currently `:41`): extend "The enum distinguishes: `HEALTHY`, ... `UNKNOWN`." with `MISSING` (REQ-007/AC-4).
2. Diagnosis bullets (currently `:45-52`): add a bullet stating a missing database file is its own condition — the integrity probe checks existence before opening, a missing path reports `DbCondition.MISSING` with a path-carrying detail, and probing never creates the file (REQ-007/AC-2).
3. In the same diagnosis region, state probe semantics: the integrity check, domain-identity check, backup usability probe, and logical-verification stage open their subject read-only (URI `mode=ro`; only a busy timeout is applied) and do not create files, apply write pragmas, or convert journal modes; the staged restore candidate is verified read-write so candidate-side WAL recovery remains available (REQ-003/REQ-005 wording, AC-1/AC-3).
4. Result-contract bullets (currently `:65-66`): add the action `missing_database` — a missing live database yields `action="missing_database"` with `active_db_state="missing"` and no restore attempt, identical under `dry_run=True`; extend the `active_db_state` value set with `missing` (documented as paired with the `missing_database` action) (REQ-004/REQ-007/AC-2).

### Method
- Direct markdown edits after the code/test documents and the 002/003 docs edits have landed.

### Details
- Vocabulary check: two new tokens only — `MISSING` (enum member) and `missing_database`/`"missing"` (action/state values); they must match the landed code exactly (`check_docs_consistency.py` cross-checks symbol references).
- Do not restate Plan 003's retention/whole-unit wording in the same bullets; keep adjacent-but-disjoint additions (plan overlap record).

## Compatibility considerations
- Docs-only; `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain db` gates apply.

## Security considerations
- N/A: documentation text only.

## Rollback considerations
- Checkout revert; revert with the unit's code/test documents if the whole unit rolls back.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` → no findings (AC-4).
- Read-back: the enum sentence, probe-semantics sentence, and contract bullets match the landed behavior asserted by companions `_5`/`_6` tests.

## Completion criteria
- `db_07` lists `MISSING`, `missing_database`, `active_db_state="missing"`, and side-effect-free probe semantics consistent with ADR-008 (companion `_7`).

## Out of Scope
- ADR-008 edits (companion `20261115-084603_7`).
- Section 12 lifecycle/drill text (Plans 008/009).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-113615 | 20261115-113615 | 4 edits: MISSING enum, missing-file diagnosis bullet, probe-semantics bullet (incl. sidecar-residue cleanup landed by _1), missing_database/active_db_state=missing contract; db_07 ceiling entry added 24576->25553 |
| 2 | Add or update tests per Validation plan | Completed | 20261115-113615 | 20261115-113615 | N/A: docs-only; behavior asserted by companion _5/_6 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-113615 | 20261115-113615 | consistency clean, structure green after ceiling re-record, quality exit 0; stale_detector pre-existing '/session recover' false positive left untouched (present at HEAD) |
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
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md