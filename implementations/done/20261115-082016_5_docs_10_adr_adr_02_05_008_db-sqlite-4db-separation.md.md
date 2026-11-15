## Goal
- Record the restore-sidecar handling and quarantine-retention decision in ADR-008.

## Scope
**Release unit**: whole-unit-rollback-retention (Phase 4 of the plan; lands with the db_07 document `_4`)

- In scope: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` — one new Decision Detail after #20 and two Recovery Policy Matrix row edits (REQ-001, REQ-002).

## Assumptions
- The new Decision Detail number is #21: the Decision Details list ends at #20 (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md:129`, verified this cycle).
- Decision Detail #19 (corrupt DB set aside as diagnostic copy; retention/deletion left to operator manual judgment) is the policy anchor this addition extends to sidecars.

## Design decisions
- One numbered Decision Detail (#21) covering the whole restore-sidecar policy (quarantine-before-swap, candidate-sidecar discard on success, retention after success, whole-unit rollback), plus matrix rows that only cross-reference it — keeps the claim in one normative place.
- Matrix wording stays policy-level (what must hold), matching the existing row style.

## Alternatives considered
- Editing only the matrix `Rollback condition` row: rejected — the matrix alone would not record the retention decision the plan requires in Decision Details (plan target-file row for ADR-008).

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. After Decision Detail #20 (`:129`), append Decision Detail #21: restore-flow sidecar handling — at swap preparation the corrupt DB's sidecar files (`-wal`/`-shm`) and the live DB's existing sidecars are moved into the quarantine directory together with the corrupt DB file; staged candidate sidecars are moved into the target location and the candidate's originals discarded only after a successful swap; a failure after the swap removes the swapped-in candidate and its sidecars and moves the quarantined original DB and its sidecars back to their original paths (whole-unit rollback, REQ-002/AC-4); the quarantine directory and its contents are retained after a successful restore and never automatically deleted — removal is operator manual judgment, consistent with Decision Detail #19 (REQ-001/AC-4).
2. Recovery Policy Matrix (`:84-104`): add a `Restore sidecar handling` row — `rag.sqlite` and `session.sqlite` cells state quarantine-before-swap, candidate-sidecar discard on success, and operator-retained quarantine (cross-reference Decision Detail #21); `workflow.sqlite`, `eventbus.sqlite`, `mcp_dedup.sqlite` cells read `not applicable (no automated restore)`.
3. Update the `Rollback condition` row (`:102`): `rag.sqlite` cell adds that a failure after the swap triggers whole-unit rollback via the quarantine (cross-referencing Decision Detail #21); the `session.sqlite` cell keeps `same`.
4. Re-read the landed db_07 wording from companion `_4` before finalizing; align wording so the two documents state one consistent policy.

### Method
- Direct markdown edit; numbered-list and table formats identical to the existing Decision Details #14-#20 and matrix rows.

### Details
- Vocabulary check: no new action/state tokens; policy prose only, no code identifiers beyond existing `-wal`/`-shm` file-suffix vocabulary.
- Do not touch the Implementation References section: the existing `scripts/db/recovery_restore.py` row ("staging, quarantine, swap, rollback, and staging cleanup helpers") remains accurate after the code procedures land — verify, do not rewrite.

## Compatibility considerations
- Docs-only; `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py --strict`, and `tools/check_docs_consistency.py --domain db` gates apply.
- `check_docs_content_policy.py --strict` blocks implementation-detail leakage: keep sentences at policy level (no function names, no line numbers).

## Security considerations
- N/A: documentation text only. Audit-record content rules already covered by the matrix `Audit requirement` row; the retention decision adds no row-level DB content disclosure.

## Rollback considerations
- Checkout revert; revert together with the code documents when the whole unit rolls back.

## Validation plan
- `uv run python tools/check_docs_quality.py` → exit 0 (table/heading rules).
- `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` → no findings (link reachability, table rules).
- `uv run python tools/check_docs_content_policy.py --strict` → no new warnings.
- `uv run python tools/check_docs_consistency.py --domain db` → no findings (AC-4 cross-doc consistency with the db_07 edits from `_4`).

## Completion criteria
- Decision Detail #21 present in the same list format as #14-#20; matrix rows cross-reference it consistently with db_07's landed wording; all four docs checkers clean.

## Out of Scope
- db_07 text edits (companion `_4`).
- Implementation References section changes (verify-only; see Details).
- Invariants, Consequences, Security Consequences sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-104412 | 20261115-104412 | Decision Detail #21 + 'Restore sidecar handling' matrix row + extended 'Rollback condition' row landed; wording aligned with landed db_07 text (step 4) |
| 2 | Add or update tests per Validation plan | Completed | 20261115-104412 | 20261115-104412 | N/A: docs-only validation plan (checkers) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-104412 | 20261115-104412 | structure (after ceiling re-record 37175), content-policy --strict, consistency --domain db all exit 0 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-104412 | 20261115-104412 | N/A: this file is the documentation |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md