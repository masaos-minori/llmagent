## Goal
Give the drill test production-equivalent rag/session fixtures with canonical FTS and
vector structures, add one negative fixture per damage class (FTS gap, missing vec,
orphaned message, orphaned memory), rename the artifact-key assertions to
`backup_duration_seconds`, and assert the timestamp-derivation relationships and
live-database immutability.

## Scope
**Release unit**: drill metric rename and assertions (shared with
`scripts/db/recovery_drill.py` — land together).

## Assumptions
- Fixtures are built under `tmp_path`; no production DB or archive path is opened.
- `scripts/db/schema_sql.py` is the DDL SSOT: `build_rag_schema_sql(dims)` and
  `build_session_schema_sql(dims)` produce the canonical rag/session schemas
  including `chunks_vec`/`chunks_fts` and `memories_vec`/`memories_fts`.
- `check_rag_consistency` detects an FTS gap and missing/orphaned vec rows;
  `check_session_consistency` detects orphaned messages and orphaned memory links.
- `sqlite-vec` may be unavailable in some environments (UNK-02). Building a
  production-equivalent fixture that contains `vec0` virtual tables requires the
  extension at `CREATE` time; if it cannot load, the healthy-path test reports an
  "unavailable" outcome and the negative tests are skipped, not failed.

## Design decisions
- **Production-equivalent fixtures from the DDL SSOT.** Replace the minimal
  `_RAG_DDL` / `_SESSION_DDL` constants with builders that run
  `build_rag_schema_sql(dims)` / `build_session_schema_sql(dims)` for a concrete
  dimension, then insert sample rows so FTS and vec tables actually contain data.
  This makes the fixture structurally identical to production, which is what the
  consistency checks inspect.
- **Negative fixtures mutate a healthy baseline.** Each damage case starts from the
  same healthy fixture and deletes exactly one element, so a failing drill is
  provably caused by the damage and not the fixture (plan Risk mitigation).
- **Renamed key set.** `_COMMON_ARTIFACT_KEYS` (`L68-L79`) drops `rpo_window_seconds`
  and adds `backup_duration_seconds`, `rpo_seconds`, `rto_seconds`, and the epoch
  anchors `drill_start_ts`, `archive_ts_epoch`, `restore_start_ts`, `restore_end_ts`.
- **Relationship assertions replace `> 0` / `>= 0`.** `test_each_domain_artifact_carries_schema_fields`
  (`L226-L228`) asserts ordering and derivation instead of sign-only bounds.
- **Verdict dict grows one key.** `test_verify_per_domain_reports_expected_verdicts`
  (`L250-L257`) expects `rag_consistent` / `session_consistent` alongside the
  existing integrity/identity keys.

## Alternatives considered
- **Keep the minimal core-table DDL and only add FTS/vec conditionally.** Rejected:
  a fixture without FTS/vec can never fail a consistency check, so AC-002 is
  unprovable. The fixture must carry the real structures.
- **Assert exact metric values.** Rejected: wall-clock durations vary per run.
  Assert relationships derivable from the stored epoch anchors within a tolerance.

## Implementation
### Target file
`tests/db/test_recovery_drill.py`

### Procedure
**Phase 1 — Fixture foundation (REQ-002)**

1. Import the DDL SSOT builders at the top:
   ```python
   from db.schema_sql import build_rag_schema_sql, build_session_schema_sql
   ```
2. Add a module-level sqlite-vec availability probe (resolve UNK-02 here) and helper
   builders. Replace the minimal `_RAG_DDL` / `_SESSION_DDL` blocks with:
   ```python
   EMBED_DIMS = 128  # concrete production-like embedding dimension for fixtures

   def _has_vec_extension() -> bool:
       """True when the sqlite-vec extension loads in this environment."""
       conn = sqlite3.connect(":memory:")
       try:
           conn.execute("CREATE VIRTUAL TABLE t USING vec0(a INTEGER)")
           return True
       except sqlite3.Error:
           return False
       finally:
           conn.close()

   def _build_rag_prod(path: Path) -> None:
       conn = _connect(path)
       try:
           conn.executescript(build_rag_schema_sql(EMBED_DIMS))
           conn.commit()
       finally:
           conn.close()

   def _build_session_prod(path: Path) -> None:
       conn = _connect(path)
       try:
           conn.executescript(build_session_schema_sql(EMBED_DIMS))
           conn.commit()
       finally:
           conn.close()
   ```
   Keep the old `_build_rag` / `_build_session` helpers for the workflow/eventbus
   sweep only where a core table suffices; the rag/session paths now use the
   production-equivalent builders when the extension is available.
3. In `_domain_dbs` (`L129-L137`), build rag/session with the production builders
   when `_has_vec_extension()` is True; otherwise fall back to the minimal core
   DDL and record that the sweep ran without FTS/vec.
4. Add four damage builders, each returning a mutated copy of a healthy fixture:
   - FTS gap: after building the healthy rag DB, delete an FTS row
     (`DELETE FROM chunks_fts WHERE rowid = ?`) so a chunk has no FTS entry.
   - Missing vec: delete the `chunks_vec` row for a chunk so its vector is absent.
   - Orphaned message: delete a parent session row leaving a child `messages`
     reference (session schema FK).
   - Orphaned memory link: delete a `memories` row leaving a dangling
     `memories_fts`/`memory_links` reference.
   Each builder asserts against the same healthy baseline in the same test run.

**Phase 2 — Negative-fixture tests (REQ-001, REQ-002, AC-002)**

5. For each damage class, add a test that drills the damaged copy and asserts the
   drill fails while `PRAGMA integrity_check` still passes:
   ```python
   def test_fts_gap_fails_drill_with_integrity_ok(tmp_path):
       # build healthy rag, apply FTS-gap damage, drill, assert FAIL + integrity True
   ```
   - Rag damage tests assert `artifacts["rag"]["verification"]["rag_consistent"]` is
     `False` and `artifacts["rag"]["integrity"]` is `True`.
   - Session damage tests assert
     `artifacts["session"]["verification"]["session_consistent"]` is `False` and
     `integrity` is `True`.
   - When `_has_vec_extension()` is False, the rag/session negative tests are
     `pytest.mark.skip`ped (a loadable copy is required to prove logical damage).

**Phase 3 — Renamed keys and timestamp relationships (REQ-003, REQ-004)**

6. Update `_COMMON_ARTIFACT_KEYS` (`L68-L79`):
   ```python
   _COMMON_ARTIFACT_KEYS = {
       "domain", "archive_path", "archive_ts", "drill_ts",
       "backup_duration_seconds", "rpo_seconds", "rto_seconds",
       "drill_start_ts", "archive_ts_epoch", "restore_start_ts", "restore_end_ts",
       "integrity", "verification", "policy", "error",
   }
   ```
7. In `test_each_domain_artifact_carries_schema_fields` (`L226-L228`), replace the
   sign-only bounds with relationship assertions:
   ```python
   assert art["integrity"] is True
   assert art["backup_duration_seconds"] >= 0
   assert art["rto_seconds"] > 0
   assert art["restore_start_ts"] >= art["archive_ts_epoch"]
   assert abs(art["rto_seconds"] - (art["restore_end_ts"] - art["restore_start_ts"])) <= 1e-3
   ```
8. In `test_verify_per_domain_reports_expected_verdicts` (`L250-L265`), extend the
   expected rag/session dicts:
   ```python
   assert artifacts["rag"]["verification"] == {
       "integrity": True,
       "required_table_rag": True,
       "rag_consistent": True,
   }
   assert artifacts["session"]["verification"] == {
       "integrity": True,
       "required_table_session": True,
       "session_consistent": True,
   }
   ```
   When the vec extension is unavailable, assert the recorded unavailable marker
   instead of `True` for the consistent key (tied to the UNK-02 decision).

**Phase 4 — Live-database immutability (REQ-005, AC-005)**

9. Keep `test_all_four_domains_drill_passes_and_live_dbs_untouched` (`L190-L203`)
   and `test_missing_ledger_is_an_audited_finding` (`L271-L291`) as-is; they already
   checksum every live DB before/after in success and failure cases. Add one
   explicit assertion that the rag and session live files are byte-identical after a
   drill that now runs consistency checks (the added read-only queries must not
   rewrite the live file).

### Method
- Negative tests share the healthy baseline so failures are attributable to damage.
- All metric assertions derive from stored epoch anchors, not wall-clock values.

### Details
- Current line map: `_COMMON_ARTIFACT_KEYS` `L68-L79`; `_RAG_DDL`/`_SESSION_DDL`
  `L33-L66`; `_domain_dbs` `L129-L137`;
  `test_each_domain_artifact_carries_schema_fields` `L206-L236`;
  `test_verify_per_domain_reports_expected_verdicts` `L239-L265`;
  `test_all_four_domains_drill_passes_and_live_dbs_untouched` `L190-L203`.
- `EMBED_DIMS` (new) must match a value the schema template accepts; keep it small (e.g.
  128) so fixtures stay fast.

## Compatibility considerations
- The key rename is the mirror of the artifact change in
  `scripts/db/recovery_drill.py`; both must land together or the suite fails in
  either direction (release-unit cohesion).
- Existing CLI subprocess tests (`test_cli_exits_zero_on_success`,
  `test_cli_exits_nonzero_on_failure`) exercise the workflow domain and are
  unaffected by the rag/session verification extension.

## Security considerations
- Tests run entirely under `tmp_path`; no production path is opened.

## Rollback considerations
- Reverting the test edits restores the prior key set and assertions. No service or
  config change is involved.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py` — healthy copies pass; each damage
  fixture fails with integrity ok; live DBs unchanged (AC-001..AC-005).
- `uv run pytest tests/db/test_recovery_drill.py -k "rpo or rto or duration"` —
  timestamp relationships hold; `backup_duration_seconds` present,
  `rpo_window_seconds` absent (AC-003, AC-004).
- `uv run pytest tests/db/test_rag_consistency.py` — reused fixture builders stay
  green.
- Full suite + coverage gate and static gates per `rules/toolchain.md`.

## Completion criteria
- `AC-001`: rag/session verification dicts include `rag_consistent` /
  `session_consistent`.
- `AC-002`: all four damage fixtures fail the drill with integrity still ok.
- `AC-003`: `backup_duration_seconds` present, `rpo_window_seconds` absent.
- `AC-004`: timestamp-relationship assertions pass.
- `AC-005`: live-database checksums identical before/after in success and failure.

## Out of Scope
- Changing the consistency check logic (`ragverify001`, `sessmoke001`).
- RPO/RTO objective values (measurements only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Build production-equivalent rag/session fixtures from the DDL SSOT | Pending | — | — | |
| 2 | Add four damage fixtures as failing-expectation tests | Pending | — | — | |
| 3 | Rename keys, assert timestamp relationships, live-database checksum | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-232133_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-174750
- **Related target files**: `tests/db/test_recovery_drill.py`
```

## Notes on filling sections

- **UNK-02 drives fixture availability.** The production-equivalent rag/session
  fixtures contain `vec0` virtual tables that need the sqlite-vec extension at
  `CREATE` time. Probe availability once and gate the healthy and negative tests on
  it; record the unavailable outcome rather than failing.
- **Line numbers are guidance.** Verify against live source before editing; the
  current-line map in Implementation > Details is the reference.
