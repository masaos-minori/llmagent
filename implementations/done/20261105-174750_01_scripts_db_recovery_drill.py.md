## Goal
Extend the recovery drill's per-domain verification with real consistency checks on
the isolated restored copy, and replace the single mislabeled `rpo_window_seconds`
metric with three correctly-defined measurements (`backup_duration_seconds` (new),
`rpo_seconds` (new), `rto_seconds`) each backed by a named, recorded event timestamp.

## Scope
**Release unit**: drill metric rename and assertions (shared with
`tests/db/test_recovery_drill.py` — land together)

## Assumptions
- The drill keeps its current isolation model: the recovery point is a read-only
  backup-API copy and every check runs against an isolated copy under the drill
  directory. The live database file is never opened for write.
- `SQLiteHelper` (already imported at `scripts/db/recovery_drill.py` L33),
  `run_integrity_check`, `verify_domain_identity`, and `DbCondition` (L34) remain
  the integrity/identity primitives; consistency is layered on top, not a
  replacement.
- `check_rag_consistency` and `check_session_consistency` are the post-`ragverify001`
  / post-`sessmoke001` read-only entry points. `check_session_consistency` already
  reports `read_smoke_test_ok` (the read-only smoke test), not a write probe.
- The pass/fail aggregation in `run_drill` keys off every value in
  `artifact["verification"]`, so additive verification keys feed the verdict
  automatically.

## Design decisions
- **Verification extension beside integrity + identity.** `_verify_rag_session`
  (`L91-L98`) gains a consistency stage. Open the isolated copy with
  `SQLiteHelper(domain, db_path=str(isolated)).open()` exactly as
  `_verify_workflow` (`L103`) and `_verify_eventbus` (`L121`) already do. For
  `rag` call `check_rag_consistency(db)` then `rag_is_consistent(report)`; for
  `session` call `check_session_consistency(db)` then `session_is_consistent(report)`.
  Add keys `"rag_consistent"` / `"session_consistent"` to the returned dict. Keys
  are additive; existing consumers of `integrity` and `required_table_*` keep
  working unchanged.
- **Import name collision.** Both `db.rag_consistency` and `db.session_consistency`
  export a module-level `is_consistent`. Import both with aliases to avoid a
  shadowing clash:
  `from db.rag_consistency import check_rag_consistency, is_consistent as rag_is_consistent` (new)
  and
  `from db.session_consistency import check_session_consistency, is_consistent as session_is_consistent` (new).
- **Unavailable dimension must not count as a pass.** `sqlite-vec` may be absent in
  some environments (UNK-02). A missing extension surfaces through
  `check_rag_consistency` as `diagnostic_errors` and can flip `rag_is_consistent` (new)
  to `False`. Do not let that silently fail a drill whose only problem is a missing
  optional extension. Decide the mechanism (UNK-02) and, once decided, fold it into
  the aggregation in `run_drill` (`L282-L284`) so an unavailable dimension neither
  passes nor fails: skip `None` markers,
  `all(v for v in artifact["verification"].values() if v is not None)`. Existing
  all-boolean values are unaffected by the filter.
- **Metric rename.** `rpo_window_seconds` → `backup_duration_seconds` (new) (REQ-003). The
  value today (`L185`, `L214`) is the archive elapsed time; rename keeps the number,
  fixes the label.
- **Named event timestamps (REQ-004).** Record numeric epoch anchors in the artifact
  so a test can recompute every metric: `drill_start_ts` (new), `archive_ts` (epoch
  variant), `archive_ts_epoch` (new), `restore_start_ts` (new), `restore_end_ts` (new)
  and derive
  `backup_duration_seconds = archive_ts - drill_start_ts`,
  `rto_seconds = restore_end_ts - restore_start_ts`, and
  `rpo_seconds = assumed_failure_ts - archive_ts`.
- **Assumed-failure event (UNK-05).** RPO needs an "assumed failure time". Default is
  a documented decision; see UNK-05. Do not invent an objective RPO value.

## Alternatives considered
- **Fold consistency into `integrity` instead of a new key.** Rejected: widening
  `integrity` conflates physical integrity with logical consistency and hides which
  dimension failed. Additive keys keep `integrity` meaning "PRAGMA integrity_check
  passed" and expose `rag_consistent` (new) / `session_consistent` (new) separately.
- **Keep `time.time()` locals and parse `format_timestamp()` strings for tests.**
  Rejected: parsing ISO strings reintroduces rounding/locale fragility. Record
  numeric epoch anchors directly; tests recompute from the same numbers the artifact
  stores.
- **Make unavailable dimensions fail the drill.** Rejected: a missing optional
  `sqlite-vec` is an environment gap, not a damaged backup. Fail-closed applies to
  logical damage in a loadable copy (AC-002), not to a missing extension.

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
**Phase 2 — Consistency verification in the drill (REQ-001)**

1. Add imports above the existing `db.recovery` import (`L34`):
   ```python
   from db.rag_consistency import check_rag_consistency, is_consistent as rag_is_consistent (new)
   from db.session_consistency import check_session_consistency, is_consistent as session_is_consistent (new)
   ```
2. Rewrite `_verify_rag_session` (`L91-L98`) to add a consistency stage beside
   integrity + identity, opening the isolated copy the same way
   `_verify_workflow` does:
   ```python
   def _verify_rag_session(domain: str, isolated: Path) -> dict:
       """Per-domain checks for the recreate-only rag/session domains."""
       condition, _ = run_integrity_check(isolated, domain)
       identity_ok, _ = verify_domain_identity(isolated, domain)
       result = {
           "integrity": condition == DbCondition.HEALTHY,
           f"required_table_{domain}": identity_ok,
       }
       if domain == "rag":
           with SQLiteHelper("rag", db_path=str(isolated)).open() as db:
               report = check_rag_consistency(db)
               result["rag_consistent"] = rag_is_consistent(report)
       elif domain == "session":
           with SQLiteHelper("session", db_path=str(isolated)).open() as db:
               report = check_session_consistency(db)
               result["session_consistent"] = session_is_consistent(report)
       return result
   ```
   Keep the function signature and the integrity/identity keys identical so the
   workflow/eventbus callers and the artifact schema are untouched.
3. Resolve UNK-02 before running tests. Inspect how
   `check_rag_consistency` reports a missing `sqlite-vec`: whether it raises
   `sqlite3.Error` (caught into `diagnostic_errors`) or returns a report with a
   detectable "unavailable" signal (e.g. a non-empty `diagnostic_errors` tied to the
   vec/fts path). Then choose the unavailable representation and wire it into the
   `run_drill` aggregation (step 5) so it is skipped, not failed. Document the choice
   in this doc's Assumptions.

**Phase 3 — Metric rename and event timestamps (REQ-003, REQ-004)**

4. In `_drill_one_domain` (`L137-L233`):
   - Record numeric epoch anchors alongside the display timestamps. `drill_start`
     (`L155`) becomes `drill_start_epoch = time.time()`; store
     `artifact["drill_start_ts"] = drill_start_epoch`. The archive display
     `archive_ts` (`L184`, `format_timestamp()`) keeps its ISO string; add
     `artifact["archive_ts_epoch"] = time.time()` next to it. Set
     `restore_start_epoch = time.time()` where `started` is captured (`L193`) and
     store `artifact["restore_start_ts"]`; set `restore_end_epoch` (new) in the `finally`
     block (`L211`) and store `artifact["restore_end_ts"]`.
   - Rename the artifact field. Replace `artifact["rpo_window_seconds"]` in the
     initial dict (`L163`) with `"backup_duration_seconds": None`, and replace the
     assignment at `L214` with:
     ```python
     artifact["backup_duration_seconds"] = round(archive_ts_epoch - drill_start_epoch, 6)
     ```
   - Derive RTO from the recorded anchors (replace the `round(rto, 6)` at `L213`):
     ```python
     artifact["rto_seconds"] = round(restore_end_epoch - restore_start_epoch, 6)
     ```
   - Derive RPO. Resolve UNK-05 for `assumed_failure_ts` (new); a safe default that stays
     non-negative is `restore_end_epoch` (new) (the moment the restored copy is ready),
     giving `rpo_seconds = restore_end_epoch - archive_ts_epoch`. Store it:
     ```python
     artifact["rpo_seconds"] = round(assumed_failure_ts - archive_ts_epoch, 6)
     ```
     Do not invent an objective RPO/RTO value (Assumptions).
5. Update the `run_drill` verdict aggregation (`L282-L284`) to skip `None`
   availability markers decided in step 3:
   ```python
   ok = bool(artifact.get("integrity")) and all(
       verdict for verdict in artifact["verification"].values() if verdict is not None
   )
   ```
   This preserves the existing all-boolean behavior while letting an unavailable
   dimension neither pass nor fail.
6. Keep `artifact["integrity"] = bool(verification.get("integrity", False))`
   (`L222`) unchanged; physical integrity still gates the verdict independently of
   logical consistency.

### Method
- Additive verification keys + renamed metric field land together so the drill suite
  cannot pass in either direction (release-unit cohesion).
- Every derived metric is recomputable from artifact-stored epoch anchors, so tests
  assert relationships rather than magic numbers.

### Details
- Current line map (verify against live source before editing):
  `_verify_rag_session` `L91-L98`; `_drill_one_domain` `L137-L233`; artifact dict
  `L157-L168`, `rpo_window_seconds: None` `L163`; `rpo_window = time.time() -
  drill_start` `L185`; `started = time.time()` `L193`; `rto = time.time() - started`
  `L211`; `artifact["rto_seconds"]` `L213`; `artifact["rpo_window_seconds"]` `L214`;
  `run_drill` aggregation `L282-L284`.
- `SQLiteHelper(...).open()` returns a context-managed handle; use the same
  `with ... as db` pattern as `_verify_workflow`/`_verify_eventbus` so the connection
  closes even on error.
- Live DB immutability (REQ-005) is preserved: consistency checks are read-only
  queries against the isolated copy; no write path is added.

## Compatibility considerations
- The artifact field rename (`rpo_window_seconds` → `backup_duration_seconds` (new)) is a
  breaking artifact change. UNK-01 confirms every in-repo consumer is a target row
  of this Plan (`recovery_drill.py`, `test_recovery_drill.py`, the `db_07` runbook
  table); no external dashboard/cron/artifact reader references it. Land the rename
  inside one release unit with the test and doc updates; no compatibility alias is
  added unless operations require one after shipping.
- `run_drill`'s aggregation change is backward compatible: existing all-boolean
  verification dicts behave identically under the `if verdict is not None` filter.

## Security considerations
- No new network, credential, or filesystem-write paths. The isolated copy lives
  under the drill directory; the live database is never opened for write.

## Rollback considerations
- The change is confined to `scripts/db/recovery_drill.py`. Reverting the two edits
  (verification stage + metric rename/timestamps) restores the prior artifact shape.
  No migration, config, or service change accompanies it.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py` — healthy production-equivalent
  copies pass; each damage fixture fails while `PRAGMA integrity_check` passes
  (AC-001, AC-002).
- `uv run pytest tests/db/test_recovery_drill.py -k "rpo or rto or duration"` —
  timestamp relationships hold; `backup_duration_seconds` (new) present,
  `rpo_window_seconds` absent (AC-003, AC-004).
- `uv run pytest tests/db/test_recovery_drill.py -k "live or checksum"` — live
  database bytes unchanged in success and failure cases (AC-005).
- `uv run pytest tests/db/test_rag_consistency.py` — reused fixture builders stay
  green.
- Full suite + coverage gate per `rules/toolchain.md`; static gates (`ruff`,
  `mypy`, `bandit`, `vulture`) clean.

## Completion criteria
- `AC-001`: `artifact["verification"]` for `rag` and `session` contains
  `rag_consistent` (new) / `session_consistent` (new).
- `AC-002`: an FTS-gap / missing-vec / orphaned-message / orphaned-memory fixture
  fails the drill with integrity still ok.
- `AC-003`: artifact carries `backup_duration_seconds` (new), no longer carries
  `rpo_window_seconds`.
- `AC-004`: artifact records `drill_start_ts` (new), `archive_ts`, `restore_start_ts` (new),
  `restore_end_ts` (new); tests assert the ordering/derivation relationships.
- `AC-005`: live-database checksum identical before/after in both cases.
- `AC-006`: handled by the docs procedure (this file).

## Out of Scope
- Changing the consistency checks themselves (`ragverify001`, `sessmoke001`).
- Setting RPO/RTO objectives (measurements only).
- Test-file and doc-file changes (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_verify_rag_session` with rag/session consistency on the isolated copy | Completed | 20261105-215555 | 20261105-215555 | STEP: proc 01+02 release unit; archived together |
| 2 | Resolve UNK-02 (sqlite-vec unavailability mechanism) | Completed | 20261105-215555 | 20261105-215555 | Decision point STEP: proc 01+02 release unit; archived together |
| 3 | Rename metric, record event timestamps, derive RPO/RTO | Completed | 20261105-215555 | 20261105-215555 | UNK-05 decision point STEP: proc 01+02 release unit; archived together |
| 4 | Update `run_drill` aggregation for unavailable markers | Completed | 20261105-215555 | 20261105-215555 | STEP: proc 01+02 release unit; archived together |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|-----|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-232133_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-174750
- **Related target files**: `scripts/db/recovery_drill.py`
```

## Notes on filling sections

- **Lightweight fill for small rows** — applies when the row is a document
  update or a single small change; keep the Procedure to the exact edits and drop
  speculative sections. This row is a multi-phase refactor, so every section is
  filled substantively.
- **Line numbers are guidance.** Verify against live source before editing; the
  current-line map in Implementation > Details is the reference.
- **Resolve unknowns inline.** UNK-02 (unavailable-dimension mechanism) and UNK-05
  (assumed-failure event) are marked as decision points; record the decided value
  here and in the plan's Unknowns table when resolved.