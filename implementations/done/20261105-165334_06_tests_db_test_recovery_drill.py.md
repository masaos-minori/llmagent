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
  call `_run_logical_verification` (seq 03). Since `drillmetrics001`,
  `_verify_rag_session` (`scripts/db/recovery_drill.py` L101-L111) also runs a
  fail-closed `check_rag_consistency` check and records a `rag_consistency` bool
  in the rag artifact's `verification` dict; a logically inconsistent fixture is
  surfaced as `rag_consistency: False` (or `required_table_<domain>: False` via
  `verify_domain_identity`). (Verified 2026-11-05.)
- Cross-plan: `drillmetrics001` is already implemented (commit `de1a85a06`,
  batch archived): the artifact fields are already `rto_seconds` /
  `rpo_window_seconds`, and this test file already asserts them (current
  L116-L117, L270-L271), already uses production-equivalent `{domain}.sqlite`
  fixture names (current L175), and already covers the rag fail-closed pass/fail
  paths (current L296, L319-L360). This row therefore narrows to confirming
  alignment with the seq 02/03 contract; the remaining work is in the Procedure
  steps. (Verified 2026-11-05.)
- Cross-plan: `sessmoke001` (sequenced before this Plan) is already implemented:
  it removed the write-smoke trigger; the drill does not construct
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

1. Confirm the drill fixture databases already use production-equivalent
   `<domain>.sqlite` names (e.g. `rag.sqlite`, `session.sqlite`; current L175,
   L370, L415) — landed by `drillmetrics001`. Rename only any fixture that still
   lacks it.
2. Confirm the existing rag fail-closed tests (current L319-L360: healthy path
   `rag_consistency` True; unverified-dimension path `rag_consistency` False)
   cover a logically inconsistent rag copy. If they do not cover a real
   broken-FTS/index fixture (core table present, consistency report
   inconsistent), add a test that builds that fixture and asserts the drill's
   `rag` artifact `verification` reports `rag_consistency: False`, i.e. the drill
   does not report a clean pass for an unusable restored copy.
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
`{"integrity": bool, "required_table_rag": bool, "rag_consistency": bool}` (see
`_verify_rag_session`, current L93-L112). A broken-FTS/index fixture drives
`rag_consistency` to `False`; a missing core table drives
`required_table_rag` to `False`. Assert accordingly. Do not add assertions
referencing `verification_unavailable`, `logical_verify_failed`, or
`active_db_state` — those belong to `test_db_recovery.py` (seq 05), not the drill.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-203200 | 20261105-203800 | Fixture naming and sweep/immutability/CLI assertions confirmed already aligned (drillmetrics001); added real broken-FTS fixture test |
| 2 | Add or update tests per Validation plan | Completed | 20261105-203200 | 20261105-203800 | Companion test row seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-203200 | 20261105-203800 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-203200 | 20261105-203800 | N/A: docs updated by seq 07 |

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