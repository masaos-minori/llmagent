# Implementation Procedure — `tests/db/test_recovery_drill.py`

## Goal

Update the recovery-drill harness tests in `tests/db/test_recovery_drill.py` so
they reflect the atomic, fail-closed protocol produced by seq 01–04:
production-equivalent database naming in the drill fixtures, and a surfacing of
the fail-closed mandatory logical-verification behavior on the drill's
rag/session path.

## Scope
**Release unit**: contract activation

## Assumptions

- The drill exercises `run_drill` (`db.recovery_drill`), which copies a backup to
  an isolated copy and verifies it with `_verify_rag_session` (integrity +
  `verify_domain_identity`) for `rag`/`session`, and integrity + ledger checks
  for `workflow`/`eventbus` (`scripts/db/recovery_drill.py` L91-L98, L101-L134).
- The drill does **not** run `recover_corruption`; it never stages sidecars,
  performs the atomic swap, or rolls back. Therefore the rollback /
  non-serviceable actions (`REQ-004`) and the `active_db_state` contract
  (`REQ-006`) are **not** exercised by this file — they are covered by
  `tests/db/test_db_recovery.py` (seq 05). This row does not claim otherwise.
- The drill's rag/session path verifies integrity + domain identity but does not
  call `_run_logical_verification` (seq 03). A logically inconsistent fixture is
  still surfaced through `verify_domain_identity` as
  `required_table_<domain>: False` in the artifact's `verification` dict.
- Cross-plan: `drillmetrics001` (sequenced after this Plan) renames the artifact
  duration field to `rpo_window_seconds` and adds RPO/RTO metric definitions;
  this row's assertions use the current field names and are
  expected to be re-verified against the post-drillmetrics001 state.
- Cross-plan: `sessmoke001` (sequenced before this Plan) removes the
  `write_smoke_fail` trigger; the drill does not construct
  `SessionConsistencyReport`, so no interaction.

## Design decisions

- Name drill fixtures with production-equivalent `<domain>.sqlite` stems so the
  computed sidecar paths (`Path(str(db_path) + suffix)`) resolve correctly if
  the drill ever stages sidecars; keep every fixture under `tmp_path`.
- Add one test asserting that a logically inconsistent `rag` fixture is reported
  in the artifact's `verification` dict (`required_table_rag` / a consistency
  failure), demonstrating the drill surfaces a non-serviceable restored copy
  rather than reporting a clean pass.
- Preserve the existing assertions: the all-four sweep, per-domain artifact
  keys, live-database immutability, and the audited-failure CLI return codes
  (L315, L339).

## Alternatives considered

- Expanding the drill to call `_run_logical_verification` / `recover_corruption`
  was rejected: `recovery_drill.py` is not a target file of this Plan, and
  introducing a restore into the drill changes its isolation guarantees. The
  drill's role is verify-on-isolated-copy, not restore; the restore protocol is
  tested by `test_db_recovery.py`.

## Compatibility considerations

- No change to `run_drill` or `recovery_drill.py`; only the test file changes.
- Existing fixture helpers keep their signatures; only the filenames they create
  change.

## Security considerations

- N/A: test-only change; all fixtures live under `tmp_path`, no production or
  archive paths are opened.

## Rollback considerations

- Revert the commit; the pre-change tests characterize the pre-protocol drill.

## Implementation

### Target file

`tests/db/test_recovery_drill.py`

### Procedure

1. Rename drill fixture databases to production-equivalent `<domain>.sqlite`
   (e.g. `rag.sqlite`, `session.sqlite`) wherever the fixtures create the live
   database file under `tmp_path`, so sidecar computation matches production.
2. Add a test that builds a logically inconsistent `rag` fixture (core table
   present, FTS/index referential integrity broken) and asserts the drill's
   `rag` artifact `verification` reports the inconsistency
   (`required_table_rag` False or a consistency failure), i.e. the drill does
   not report a clean pass for an unusable restored copy.
3. Confirm the all-four sweep (L200-L236), per-domain artifact keys, and
   live-database immutability (L203) still hold after the rename.
4. Confirm the audited-failure path (L285-L291) and CLI return-code assertions
   (L315, L339) are unchanged.

### Method

- Where a fixture opens a database, open `tmp_path / f"{domain}.sqlite"` and,
  where the drill copies a backup, keep the `{name}_restored{suffix}` isolated
  naming.
- For the inconsistent-fixture test, construct the fixture with the core table
  but a broken FTS/index relationship and assert the verification dict reflects
  it; do not assert any `recover_corruption` action value (the drill does not
  produce one).

### Details

The drill's `verification` dict for `rag` is
`{"integrity": bool, "required_table_rag": bool}` (see
`_verify_rag_session`). An inconsistent fixture drives
`required_table_rag` to `False`; assert that. Do not add assertions referencing
`verification_unavailable`, `logical_verify_failed`, or `active_db_state` —
those belong to `test_db_recovery.py` (seq 05), not the drill.

## Validation plan

- `uv run pytest tests/db/test_recovery_drill.py` — all-four sweep, per-domain
  artifacts, immutability, and audited-failure paths pass; the new
  inconsistent-fixture test reports the verification failure.
- `uv run ruff check . && uv run ruff format --check .`, `uv run lint-imports`
  — clean.

## Completion criteria

- Drill fixtures use production-equivalent `<domain>.sqlite` naming.
- A logically inconsistent restored copy is surfaced in the drill's
  `verification` dict rather than reported as a clean pass.
- Existing sweep, immutability, and audited-failure assertions remain green.

## Out of Scope

- The restore protocol itself (`scripts/db/recovery.py` seq 02,
  `scripts/db/recovery_restore.py` seq 01, `scripts/db/recovery_verification.py`
  seq 03, `scripts/db/models.py` seq 04); rollback / non-serviceable actions are
  covered by `tests/db/test_db_recovery.py` (seq 05).
- `recovery_drill.py` behavior (not a target file of this Plan);
  `drillmetrics001`'s RPO/RTO metric rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion test row seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs updated by seq 07 |

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
- **Requirement ID**: `REQ-007` (drill covers production sidecar layout; fail-closed logical verification surfaced on the drill)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `tests/db/test_recovery_drill.py`
