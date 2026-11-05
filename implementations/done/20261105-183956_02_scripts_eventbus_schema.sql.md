## Goal

Move canonical EventBus DDL to version 6 and give `dlq_outbox` exactly one foreign key by removing the duplicated table-level `FOREIGN KEY` clause (implement REQ-005 and the version half of REQ-004 / AC-004, AC-005, AC-006).

## Scope
**Release unit**: canonical-version-6

## Assumptions
- `scripts/db/schema_sql.py` reads `schema.sql` verbatim (`build_eventbus_schema_sql()` / `eventbus_schema_version()`, L276-L290), so editing `schema.sql` propagates to every consumer without a code change.
- The inline `PRIMARY KEY REFERENCES events(event_id)` (L57) is the single retained FK; only the table-level `FOREIGN KEY (event_id) REFERENCES events(event_id)` (L65) is removed.
- The frozen 4 -> 5 `_DLQ_OUTBOX_SQL` in `scripts/eventbus/migrations.py` (seq 03) deliberately keeps its two-FK shape as the pre-dedup v5 intermediate; canonical `schema.sql` is the post-dedup v6 shape. They are intentionally different now.
- `assert_matches` compares the structural fingerprint only (not `user_version`), so moving the stamp from 5 to 6 does not itself break the fingerprint comparison; the version half is enforced by `validate_canonical` (new, seq 04).

## Design decisions
- Delete only the table-level clause (L65); keep the inline `PRIMARY KEY REFERENCES` (L57) so `PRAGMA foreign_key_list(dlq_outbox)` returns one entry (AC-005).
- Bump the stamp to 6 in the same edit so fresh creation, the fingerprint source, and the startup gate all move together (release unit canonical-version-6).

## Alternatives considered
- Removing the inline FK and keeping the table-level clause: rejected — the inline `PRIMARY KEY REFERENCES` is what the rest of the DDL and the tests reference; keep the inline form.
- Bumping the version in a separate commit: rejected — the release-unit note requires the stamp and the FK removal to land together so fresh and converged-migrated databases share one fingerprint.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Delete the duplicated table-level foreign-key line (L65): `    FOREIGN KEY (event_id) REFERENCES events(event_id)`.
2. Keep the inline `PRIMARY KEY REFERENCES events(event_id)` on `dlq_outbox.event_id` (L57) unchanged.
3. Change the stamp at L75 from `PRAGMA user_version = 5;` to `PRAGMA user_version = 6;`.

### Method
- The removal is purely structural; the inline FK still enforces the parent reference, so `PRAGMA foreign_key_check` stays clean.
- The version bump is read dynamically by `eventbus_schema_version()` and `_expected_schema_version()`, so no other file needs a literal edit.

### Details
- Pre-change anchors: L56-L66 (`dlq_outbox` definition, inline FK at L57, duplicate table-level FK at L65), L75 (`PRAGMA user_version = 5`).
- After this edit, re-run `tools/check_db_separation.py` and the fingerprint-based tests; the extended fingerprint (seq 04) plus the 5 -> 6 rebuild step (seq 03) make a fresh v6 database and a `3 -> 4 -> 5 -> 6` migrated database fingerprint-equal (AC-006).

### Companion test files
- `tests/eventbus/test_eventbus_schema_version.py`
  - Procedure: (a) `test_schema_version_is_pinned_to_five` (L74-L81) — change `assert eventbus_schema_version() == 5` to `== 6` and update the docstring to the `3 -> 4 -> 5 -> 6` chain; (b) module docstring (L3-L11) — record that version 6 is the FK-dedup rebuild (see seq 03); (c) `test_registered_v3_database_migrates_at_startup` (L118-L153) — the new 5 -> 6 step (seq 03) auto-runs at startup, so expect final `user_version == 6` and three ledger rows `{(eventbus_ledger_baseline,3,4),(eventbus_dlq_outbox,4,5),(eventbus_dlq_outbox_fk_dedup,5,6)}`; (d) `test_future_version_is_refused` (L156-L168) — version 6 is now current, so change the stamped value from `6` to `7` (a genuinely future version) before expecting the recreate refusal.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_schema_version.py -q`.

## Compatibility considerations
- The 4 -> 5 step's frozen `_DLQ_OUTBOX_SQL` in `scripts/eventbus/migrations.py` keeps its two-FK shape; the doc/comment there (L55-L57 "byte-identical in shape to schema.sql") becomes inaccurate and seq 03 updates it. Canonical `schema.sql` is now single-FK; the intermediate v5 is double-FK.
- `test_fresh_baseline_and_migrated_database_are_fingerprint_equal` in `tests/eventbus/test_eventbus_migrations.py` (seq 03) migrates to `target_version=5`; it must migrate to `6` so both sides carry the single FK, otherwise the fingerprint comparison fails on the FK difference.

## Security considerations
- The single inline FK still enforces the `events(event_id)` parent reference; removing the duplicate does not weaken referential integrity.

## Rollback considerations
- Revert the two-line edit to `schema.sql` (re-add L65, restore `= 5`).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_schema_version.py -q` (companion pin + startup/future-version updates).
- `uv run pytest tests/db/test_eventbus_schema_equivalence.py tests/eventbus/test_eventbus_migrations.py -q` (fresh-vs-migrated convergence at v6, single FK entry).
- `lint-imports`, `tools/check_db_separation.py`, full suite.

## Completion criteria
- `schema.sql` stamps `PRAGMA user_version = 6` and `dlq_outbox` carries exactly one FK (the inline `PRIMARY KEY REFERENCES`).
- The companion version tests pass with the v6 pin, the three-step startup migration, and a future-version guard at 7.

## Out of Scope
- The FK-dedup rebuild step and registry change (`scripts/eventbus/migrations.py`, seq 03), the fingerprint contract extension (seq 04), the `create_eventbus_schema` three-path rewrite (seq 01), the equivalence test (seq 06), and the doc corrections (seq 09, seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the duplicate FK and bump `schema.sql` to version 6 | Completed | 20261105-222451 | 20261105-222730 | Verification: anchors match; correction applied - deleting the L65 table-level FK also required removing the trailing comma on L64 to keep the DDL valid. Companion test edits deferred until seq 03 registers the 5->6 step (release unit canonical-version-6). |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-223520 | Companion test_eventbus_schema_version.py updated: pin renamed to pinned_to_six (==6), docstring records 3->4->5->6, startup test expects version 6 + 3 ledger rows, future-version probe moved 6->7. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-223520 | Validation run jointly with seq 03 per release unit canonical-version-6: 42 targeted eventbus tests + 102 create_schema/db_migrations tests passed; lint-imports and check_db_separation clean; full suite at batch end. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-223520 | N/A: doc updates owned by seq 09/seq 10 per Out of Scope. |

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
- **Requirement ID**: `REQ-005`, `REQ-004`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_schema_version.py`