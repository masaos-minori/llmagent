## Goal
- Give the EventBus database three mutually exclusive lifecycle paths — create a fresh canonical database, validate an existing canonical database without any mutation, upgrade a legacy database only through a registered forward migration — and define the canonical schema-identity contract (version plus fingerprint coverage) so incompatible structures are rejected before any write and fresh and migrated databases converge on one fingerprint.

## Priority
High

## Scope
- **In-Scope**:
  - Split `create_eventbus_schema` into the three paths; no `executescript` against any existing database; rejection leaves schema and `user_version` unchanged.
  - Version and fingerprint validation before any mutation on the existing-database path (new `validate_canonical` entry in the shared fingerprint module).
  - Remove the apply-then-reset-version behavior for `user_version == 0` databases; unstamped databases are validated column-for-column and only stamped.
  - Fingerprint contract decision, implemented: triggers stay in scope (already covered); views and partial-index predicates are added; `PRAGMA user_version` is validated by the canonical validation entry point (kept out of the fingerprint tuple); a full normalized-DDL hash stays out of the contract.
  - Deduplicate the `dlq_outbox.event_id` foreign key through a newly registered step `eventbus_dlq_outbox_fk_dedup` (5 -> 6) that rebuilds `dlq_outbox` with a single inline FK; canonical `schema.sql` moves to `PRAGMA user_version = 6` with the duplicate table-level `FOREIGN KEY` clause removed; the frozen 4 -> 5 step SQL is not edited.
  - Fresh-versus-migrated fingerprint convergence at version 6.
  - Docs: correct the stale eventbus schema-version and ADR statements in the eventbus persistence document, and update the migration-chain facts in the db migration document.
- **Out-of-Scope**: New EventBus tables or columns; the generic runner's backup behavior (owned by the dbmigsafe001 Plan); editing the text of the already-registered 4 -> 5 outbox step; a registered upgrade path from the pre-ledger version 1/2 era (remains recreate-per-policy pending owner decision).
- **Dependencies**: The source issue lists `issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md`: both touch `scripts/eventbus/migrations.py`; apply in either order but re-verify the ledger change against the migration registry.
  - **Depends on**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md | phase all | reason: dbmigsafe001 lands first (memo cycle order 5 before 6) and changes the spec callback contract (`postcondition` -> `pre_commit_verification` for both eventbus steps), the durable-archive wiring, the ledger `seq` ordering used by `read_ledger`, and the eventbus passages of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`; this Plan's new registry step, registry-pinning tests, and doc rows must be written against that post-change state.

## Background
Adversarial verification against current source (2026-11-04) confirmed the issue's core claims, resolved its open items, and added one production fact:

- Confirmed: `create_eventbus_schema` runs `db.executescript(build_eventbus_schema_sql())` for every existing database whose version is `0` or the current version (`scripts/db/create_schema.py` L149-L150); for `user_version == 0` it then re-stamps 0 (`db.execute("PRAGMA user_version = 0")`, L154-L158) without undoing objects the `IF NOT EXISTS` DDL added; for an existing database at the current version the fingerprint `assert_matches` runs only after the DDL (L164).
- Confirmed: `dlq_outbox.event_id` carries the foreign key twice — inline `PRIMARY KEY REFERENCES events(event_id)` (`scripts/eventbus/schema.sql` L57) plus table-level `FOREIGN KEY (event_id) REFERENCES events(event_id)` (L65) — and identically in `_DLQ_OUTBOX_SQL` (`scripts/eventbus/migrations.py` L59, L67).
- Resolved (issue recorded it as a definition task): the fingerprint (`scripts/shared/eventbus_schema_fingerprint.py`) currently covers tables, columns, indexes (name, unique flag, partial flag, key columns — not the partial WHERE text), table-level `UNIQUE/PRIMARY KEY/CHECK` clauses, the full `PRAGMA foreign_key_list` (so the duplicate FK is inside the fingerprint), and triggers; it does not cover `PRAGMA user_version` or views.
- Located (issue left it Unknown): the EventBus open/initialization path is `_init_schema` in `scripts/eventbus/schema.py` L74-L121. It already validates before mutating (version gate, `assert_matches`, column-match stamping, or the registered runner path) and needs no change in this Plan.
- Stale docs found: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` L32 still says the current version is 3 and cites "ADR-008: no migration mechanism", but `schema.sql` stamps 5, the registry has two steps, and ADR-008 itself was already amended (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` L75) to adopt registered forward-only migrations for `workflow.sqlite`/`eventbus.sqlite`.
- Resolved: the `dlqbox001` requirements location — the archived issue `issues/done/20261029-104501_dlqbox001_dlq-sqlite-outbox.md` and commit `6c0afd96a` introduced the outbox DDL and the 4 -> 5 step.
- New production fact (read-only inspection 2026-11-04): `/opt/llm/db/eventbus.sqlite` is at `user_version = 1` with only `events`, `consumer_delivery`, `consumer_offsets` — no `dlq_outbox`, no `schema_migrations`. Per the documented policy (eventbus_06 L32) a version-1 database is a recreate database under the current registry; this Plan does not register a pre-ledger upgrade path.
- Layering fact: `.importlinter` places `db -> shared` and keeps `eventbus` isolated; `scripts/db/create_schema.py` therefore must not import `eventbus.*`. The three-path split is implemented with the shared fingerprint module and shared refusal semantics, and legacy upgrades remain the job of the eventbus CLI (`scripts/eventbus/migrate.py`) and the startup path (`scripts/eventbus/schema.py`).

## Problem
Rejecting an incompatible existing EventBus database can still leave it mutated (`IF NOT EXISTS` objects survive the version reset), the schema-identity contract is undefined for views, partial-index predicates, and the version stamp, and the duplicate foreign key makes `PRAGMA foreign_key_list(dlq_outbox)` return two entries that the fingerprint treats as canonical.

## Reason for Change
Data-integrity risk on the startup/initialization path of a persisted database; one canonical-schema lifecycle must keep the expected fingerprint, fresh schema, and migration destination synchronized before the version-6 contract moves.

## Implementation Intent
Three explicit, mutually exclusive paths in `create_eventbus_schema`: fresh creation (no events table) applies canonical DDL once; existing databases are validated (version + shape) with zero DDL, stamped only in the unstamped column-match case, and otherwise refused unchanged with guidance to the registered migration CLI. Canonical identity = `PRAGMA user_version` checked by the validation entry point + the structural fingerprint extended with views and partial-index predicates. The foreign-key dedup is a shape change and therefore travels the registered forward-only path as a new 5 -> 6 rebuild step; the frozen 4 -> 5 step text stays byte-identical.

## Requirements
- `REQ-001`: `create_eventbus_schema` never executes DDL against an existing database; fresh creation applies the canonical schema exactly once.
- `REQ-002`: For an existing database, version and fingerprint checks run before any mutation; a refusal leaves `sqlite_master` and `user_version` unchanged.
- `REQ-003`: The apply-then-reset behavior for `user_version == 0` is removed; an unstamped existing database is stamped only when its tables match `schema.sql` column for column, mirroring `scripts/eventbus/schema.py` L98-L100; databases at unregistered versions are refused with a recreate/CLI message; upgrades happen only through registered migration steps.
- `REQ-004`: Fingerprint contract decided and implemented: triggers in scope; views and partial-index predicate text added to `build_fingerprint`; `PRAGMA user_version` validated by a new `validate_canonical(conn)` entry (version compared against the stamp in `schema.sql`, kept outside the fingerprint tuple); a full normalized-DDL hash is explicitly excluded from the contract.
- `REQ-005`: `dlq_outbox` carries exactly one foreign key in canonical DDL (`schema.sql`, version stamped 6); a new registered step `eventbus_dlq_outbox_fk_dedup` (5 -> 6) rebuilds `dlq_outbox` (create-copy-drop-rename, `disable_foreign_keys` opt-in with the runner's `PRAGMA foreign_key_check`, index `idx_dlq_outbox_status` recreated, `PRAGMA user_version = 6`) using `pre_commit_verification` for its integrity checks; the text of the registered 4 -> 5 step is unchanged.
- `REQ-006`: A fresh version-6 database and a database migrated `3 -> 4 -> 5 -> 6` produce the same fingerprint, and `PRAGMA foreign_key_list(dlq_outbox)` returns one entry on both.
- `REQ-007`: Docs record the three paths, the fingerprint contract, the version-6 chain (`3 -> 4 -> 5 -> 6`), and the corrected version/ADR statements.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/create_schema.py | Rewrite `create_eventbus_schema` into the three paths; delete the existing-database `executescript` and the version-reset branch; validate (version + shape) before any stamp; refuse unchanged otherwise | L149-L150 runs DDL on every existing current/0-version database; L154-L158 resets the stamp without undoing added objects; L164 checks the fingerprint only after DDL | REQ-001, REQ-002, REQ-003 / AC-001, AC-003 | `scripts/db/create_schema.py` L137-L172 | tests/db/test_create_schema.py | Verified |
| scripts/eventbus/schema.sql | Remove the duplicate table-level `FOREIGN KEY (event_id)` clause; keep the inline `PRIMARY KEY REFERENCES`; bump `PRAGMA user_version` to 6 | Duplicate FK at L57 and L65 makes `foreign_key_list` return two entries and pins them into the fingerprint | REQ-005, REQ-004 / AC-004, AC-005, AC-006 | `scripts/eventbus/schema.sql` L56-L75 | tests/eventbus/test_eventbus_schema_version.py, tests/db/test_eventbus_schema_equivalence.py | Verified |
| scripts/eventbus/migrations.py | Register `eventbus_dlq_outbox_fk_dedup` (5 -> 6) rebuilding `dlq_outbox` with one FK, `disable_foreign_keys=True`, integrity checks as `pre_commit_verification`; do not edit the frozen 4 -> 5 `_DLQ_OUTBOX_SQL` text | FK-dedup is a shape change; rules item 2 requires a version-stamped registered step and rules item 5 forbids editing the 4 -> 5 SQL | REQ-005, REQ-006 / AC-003, AC-005, AC-006 | `scripts/eventbus/migrations.py` L55-L72 (frozen step SQL), L153-L172 (registry) | tests/eventbus/test_eventbus_migrations.py | Verified |
| scripts/shared/eventbus_schema_fingerprint.py | Extend `build_fingerprint` with views and partial-index predicate text; add `validate_canonical(conn)` combining the `user_version` gate and `assert_matches` | Contract items the issue requires defining: current coverage is L70-L101/L111-L136 and excludes version and views | REQ-004, REQ-002 / AC-004 | `scripts/shared/eventbus_schema_fingerprint.py` L21-L30, L70-L101, L111-L136, L177-L183 | tests/db/test_eventbus_schema_equivalence.py, tests/eventbus/test_eventbus_migrations.py | Verified |
| tests/db/test_create_schema.py | Negative tests snapshotting `sqlite_master` + `user_version` before/after each refusal (differing version, unstamped mismatching shape); fresh-creation tests at version 6; no-DDL-on-existing assertions | The changed branches of `create_eventbus_schema` need per-branch coverage | REQ-001, REQ-002, REQ-003 / AC-001, AC-003 | `tests/db/test_create_schema.py` L189-L193 (eventbus config hook), L761-L780 (eventbus ledger/baseline tests), L1046+ | — | Verified |
| tests/db/test_eventbus_schema_equivalence.py | Fresh-versus-migrated convergence at version 6 (fingerprint equality, one FK entry in `foreign_key_list`); equivalence under the extended fingerprint | AC-006 convergence is acceptance for the shape change | REQ-005, REQ-006 / AC-006 | `tests/db/test_eventbus_schema_equivalence.py` L32 (bootstrap equivalence), L43 (unchanged-on-restart) | — | Verified |
| tests/eventbus/test_eventbus_migrations.py | Update the registry pin to the three-step list; add 5 -> 6 step tests: rebuild preserves rows and index, pre-commit failure rolls back schema/version/ledger, `foreign_key_list` single entry after the step | rules item 6: registry-pinning tests must move with the registration | REQ-005, REQ-006 / AC-003, AC-005, AC-006 | `tests/eventbus/test_eventbus_migrations.py` L114 (registry pin `["eventbus_ledger_baseline", "eventbus_dlq_outbox"]`) | — | Verified |
| tests/eventbus/test_eventbus_schema_version.py | Move the contract lock from `PRAGMA user_version = 5` to 6 | The pin fails the moment canonical moves to 6 (rules item 6) | REQ-005 / AC-006 | `tests/eventbus/test_eventbus_schema_version.py` L75 | — | Verified |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Correct "version 3" and the "ADR-008: no migration mechanism" statement; document the three paths, the fingerprint contract, the version-6 chain, and the FK change | L32-L36 are stale against `schema.sql` L75 and amended ADR-008 L75 | REQ-007 / AC-007 | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` L32-L36 | — | Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Update the eventbus migration passage from two steps to the version-6 three-step chain and reference the fingerprint contract | dbmigsafe001 will have rewritten this passage for two steps; the new step makes it stale again | REQ-007 / AC-007 | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` L52, L76-L77 | — | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/schema.py | `_init_schema` L74-L121 is the located open/init path and the model for column-match stamping and the runner delegation; it must stay behaviorally consistent with the new `create_eventbus_schema` refusal messages | scripts/db/create_schema.py, REQ-002, REQ-003 |
| scripts/eventbus/migrate.py | The registered-upgrade CLI the refusal message points operators to; its exit-code mapping comes from the dbmigsafe001 Plan | scripts/db/create_schema.py, REQ-003 |
| scripts/db/schema_sql.py | `build_eventbus_schema_sql`/`eventbus_schema_version` read `schema.sql` verbatim (L276-L290) — no duplicate DDL copy to update | scripts/eventbus/schema.sql, REQ-005 |
| scripts/shared/db_migrations.py | Runner contract the new step uses (`disable_foreign_keys`, `pre_commit_verification`, ledger row in-transaction) as amended by the dbmigsafe001 Plan | scripts/eventbus/migrations.py, REQ-005 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Amended ADR L75 is the authority for eventbus registered forward-only migrations cited in the doc updates | docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md, REQ-007 |
| issues/done/20261029-104501_dlqbox001_dlq-sqlite-outbox.md | The resolved `dlqbox001` requirements source defining `dlq_outbox` semantics preserved by the rebuild | scripts/eventbus/migrations.py, REQ-005 |
| .importlinter | Layer contract: `db` must not import `eventbus`; constrains the three-path implementation | scripts/db/create_schema.py, REQ-001 |

## Acceptance Criteria
- `AC-001` (REQ-001, REQ-002): Rejecting an existing database (differing version, or unstamped with non-matching shape) leaves `sqlite_master` and `user_version` byte-identical to the pre-call snapshot.
- `AC-002` (REQ-001): Fresh creation produces the canonical version-6 schema with the `schema_migrations` baseline row.
- `AC-003` (REQ-003, REQ-005): Legacy upgrades execute only registered migration steps; an unregistered version is refused with a recreate/CLI message and no mutation.
- `AC-004` (REQ-002, REQ-004): Validation detects version mismatches and the partial-index predicate/view deviations required by the contract.
- `AC-005` (REQ-005): `PRAGMA foreign_key_list(dlq_outbox)` returns exactly one entry on canonical fresh and migrated databases.
- `AC-006` (REQ-005, REQ-006): A fresh version-6 database and a `3 -> 4 -> 5 -> 6` migrated database produce the same fingerprint.

## Tests
- `REQ-001/002/003` unit (`tests/db/test_create_schema.py`): snapshot `sqlite_master` rows and `user_version` before and after each refusal branch; assert no added object and no stamp change; fresh-creation test asserts version-6 stamp and baseline row; unstamped matching-shape database is stamped without any DDL call (assert via a spy that `executescript` is never invoked on an existing database).
- `REQ-004` unit (`tests/db/test_eventbus_schema_equivalence.py`, `tests/eventbus/test_eventbus_migrations.py`): fingerprint detects an added view, an altered partial-index predicate on a scratch database, and a version mismatch via `validate_canonical`; canonical fingerprint unchanged for the existing canonical shape (no false positives).
- `REQ-005/006` integration (`tests/eventbus/test_eventbus_migrations.py`, `tests/db/test_eventbus_schema_equivalence.py`): 5 -> 6 rebuild preserves all `dlq_outbox` rows, status CHECK vocabulary, and `idx_dlq_outbox_status`; pre-commit verification failure rolls back schema, `user_version`, and ledger together; fresh-vs-migrated fingerprint equality; `foreign_key_list` single entry; registry pin updated to the three-step list.
- `REQ-007`: docs checked by `tools/check_docs.py` and the ADR reference/preservation checkers.
- Issue-mandated command: `uv run pytest tests/db/test_create_schema.py tests/db/test_eventbus_schema_equivalence.py tests/eventbus/test_eventbus_migrations.py tests/eventbus/test_eventbus_schema_version.py -q`, then full suite, ruff, and mypy per `rules/toolchain.md`.

## Documentation Impact
Docs update required, driven by REQ-007. Via `docs/00_index.md`'s task-scope mapping: the eventbus persistence document (`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`) records the three paths, the fingerprint contract, the version-6 chain, and the FK change (its current version-3/"no migration mechanism" text contradicts amended ADR-008); the db migration document (`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`) records the three-step eventbus chain and the fingerprint contract reference. No ADR change is required: ADR-008 already covers registered forward-only migrations (its L75 amendment).

## Assumptions
- No deployed EventBus database is currently at version 4 or 5: read-only inspection of `/opt/llm/db/eventbus.sqlite` shows version 1 (recreate-class database); the fingerprint coverage extension compares the same physical shape, so it is safe for versions 4/5 if any exist (UNK-01).
- `build_eventbus_schema_sql()` and `eventbus_schema_version()` read `schema.sql` verbatim (`scripts/db/schema_sql.py` L276-L290), so editing `schema.sql` propagates to every consumer without code changes.
- The 4 -> 5 outbox step is treated as released/frozen (merged in commit `6c0afd96a`, documented in db_03 sections 8a/8b and ADR-008's amendment); the FK fix therefore travels as a new step, not an edit.
- Startup behavior of `_init_schema` (auto-migrating registered lower versions) stays as is; only `create_eventbus_schema` gains the validate-first contract.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any staging/secondary EventBus database is deployed at version 4 or 5 (the 5 -> 6 rebuild and the extended fingerprint must be rehearsed against such a database) | Only `/opt/llm/db` was inspectable (read-only, version 1); other hosts not visible from the repository | Scratch-database recipe (`rules/persisted-schema-change.md`) with a seeded version-5 database is part of the Plan's test work; production rollout requires the owner to inventory live EventBus databases first | True for deployment, False for implementation |
| UNK-02 | Policy for the production version-1 `eventbus.sqlite`: recreate (documented policy, eventbus_06 L32) or register a pre-ledger upgrade step | No owner decision on record; the issue's Out-of-Scope excludes new steps beyond the FK fix | Recreate-per-documentation is the implemented default; the owner decides separately whether a 1 -> 6 registered path is ever worth building | False |
| UNK-03 | Fingerprint compatibility policy for deployed databases | None on record | Resolved by this Plan's decision: coverage extension that preserves the compared physical shape needs no step; any shape change requires a registered version-stamped step (rules items 2/5). Recorded in Design; doc states it | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/create_schema.py | Refactor | high (init_db.sh and all four-database creation entry) | 8 commits | 1 | Verify: `init_db.sh` calls create_schema; the new refusal must not fire on fresh production initialization (Phase 6 check) |
| scripts/eventbus/schema.sql | Feature | high (canonical identity for fresh creation, fingerprint, startup gate) | 9 commits | 1 | N/A: not executed by deploy.sh directly; consumed via create_schema/schema.py |
| scripts/eventbus/migrations.py | Feature | medium (registry gains a step; shared with dbmigsafe001 Plan) | 3 commits | 1 | N/A |
| scripts/shared/eventbus_schema_fingerprint.py | Feature | medium (consumed by create_schema, eventbus startup, eventbus migrations) | 1 commits | 1 | N/A |
| tests/db/test_create_schema.py | Test | low | 19 commits | 1 | N/A |
| tests/db/test_eventbus_schema_equivalence.py | Test | low | 3 commits | 1 | N/A |
| tests/eventbus/test_eventbus_migrations.py | Test | low | 3 commits | 1 | N/A |
| tests/eventbus/test_eventbus_schema_version.py | Test | low | 6 commits | 1 | N/A |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | Docs | low | 15 commits | 1 | N/A |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Docs | low | 22 commits | 1 | N/A |

## Design
1. **Three paths in `create_eventbus_schema` (no cross-layer import).** Path selection mirrors `scripts/eventbus/schema.py` `_init_schema` semantics but with the db-layer rule respected: no `eventbus.*` import from `scripts/db/create_schema.py`. (a) No `events` table -> fresh: `executescript(build_eventbus_schema_sql())` + baseline row. (b) Existing at the stamped version -> `validate_canonical(conn)` first (shape + version), then baseline stamp if absent; zero DDL. (c) Existing unstamped (version 0) -> column-for-column match against canonical (`_matches_current_schema`-equivalent local helper): stamp on match, refuse unchanged otherwise. (d) Existing at any other version -> refuse unchanged with a message naming the registered CLI (`scripts/eventbus/migrate.py --apply`) or the recreate procedure. `MigrationRunner` delegation from `create_schema` is not used because the registry lives in the isolated `eventbus` layer; upgrades belong to the eventbus CLI and startup paths. The refusal message carries no row content (constraint).
2. **Fingerprint contract (decision).** In contract: tables, columns, indexes with partial-predicate text (extracted from the index's normalized `sqlite_master` SQL), table-level `UNIQUE/PRIMARY KEY/CHECK` clauses, the full `PRAGMA foreign_key_list`, triggers (already covered), and views (compared against canonical; canonical defines none, so any view in a target database is a deviation). Out of contract: normalized full-DDL hash (formatting-fragile; per-object comparison already covers semantics). `PRAGMA user_version` is validated by the new `validate_canonical(conn)` entry that composes the version gate with `assert_matches`; `build_fingerprint` stays purely structural so existing callers (startup gate, step verification) keep their current version handling. The coverage extension changes no comparison result for already-deployed canonical shapes (UNK-03 resolution), so it needs no migration step.
3. **FK dedup as registered step 5 -> 6.** `eventbus_dlq_outbox_fk_dedup`: `from_version=5`, `to_version=6`, `disable_foreign_keys=True`, `preconditions` (version 5, `dlq_outbox` present exactly with the two-FK fingerprint, `events` parent present), `mutation_sql`: create `dlq_outbox_new` with the canonical columns/CHECK and only the inline `PRIMARY KEY REFERENCES events(event_id)`, `INSERT INTO dlq_outbox_new SELECT ... FROM dlq_outbox`, drop the old table, rename, recreate `idx_dlq_outbox_status`, `PRAGMA user_version = 6`; `pre_commit_verification` (per the dbmigsafe001 Plan's callback contract): row-count equality, index present, `PRAGMA foreign_key_list(dlq_outbox)` length 1, shape equals canonical-minus-version. The runner's existing `PRAGMA foreign_key_check` after the FK switch covers dangling references; `dlq_outbox` is a child table, so the drop cannot cascade to parents (rules item 3 verified by the seeded-children recipe in reverse: parent `events` rows untouched). Frozen 4 -> 5 step text untouched (rules item 5). `schema.sql`: delete L65, stamp 6.
4. **Registry and pins move together (rules item 6).** `tests/eventbus/test_eventbus_migrations.py` L114 pin becomes the three-id list; `tests/eventbus/test_eventbus_schema_version.py` L75 contract lock becomes 6; `tests/db/test_eventbus_schema_equivalence.py` gains the fresh-6 vs `3->4->5->6` convergence case using the scratch-database recipe with seeded `dlq_outbox` rows in all three statuses plus NULL optionals.
5. **Version-store coherence (rules item 1).** The version is stored in exactly the same two places as today — `schema.sql`'s `PRAGMA user_version` stamp (read dynamically by `eventbus_schema_version()` and `_expected_schema_version()`) and each step's stamp — so bumping 5 -> 6 in `schema.sql` and the new step is sufficient; no map table to update. Fresh and migrated convergence is acceptance AC-006.
6. **Doc corrections are facts, not new policy.** eventbus_06 currently contradicts amended ADR-008; the update records the implemented contract (three paths, fingerprint inclusions, version-6 chain) and keeps the recreate policy for pre-ledger versions as documented policy pending UNK-02.

`rules/persisted-schema-change.md` item outcomes: item 1 — applies: version stores identified (`schema.sql` stamp, step stamps, `eventbus_schema_version()`, `_expected_schema_version()`); this Plan changes their value 5 -> 6 in both synchronized places. Item 2 — applies: the FK removal is a fingerprint-moving shape change and is registered as the 5 -> 6 step with the version stamp; verified via scratch-database fingerprint comparison and `tools/check_db_separation.py` re-run. Item 3 — applies: the step rebuilds `dlq_outbox` (child of `events`); recipe seeded parent rows must be untouched, `PRAGMA foreign_key_check` empty, child rows preserved; `disable_foreign_keys` used per the runner contract. Item 4 — does not apply: no new `NOT NULL` column. Item 5 — applies as the central constraint: the 4 -> 5 step SQL stays byte-identical; the new step's SQL applied over the chain must equal canonical DDL (convergence tests). Item 6 — applies: pins named and updated in the same change (`tests/eventbus/test_eventbus_migrations.py` L114, `tests/eventbus/test_eventbus_schema_version.py` L75, equivalence tests). Item 7 — applies narrowly: `dlq_outbox` rows keep their meaning through the rebuild; the recipe seeds `pending`/`done`/`failed` rows and NULL `last_error`/`completed_at` to prove value preservation.

## Implementation steps
1. **Phase 1: Fingerprint contract extension (REQ-004)**
   - [ ] Add views and partial-index predicate text to `build_fingerprint`; add `validate_canonical(conn)` composing the version gate with `assert_matches` (scripts/shared/eventbus_schema_fingerprint.py)
   - [ ] Unit tests: view deviation, predicate deviation, version mismatch via `validate_canonical`, and no-false-positive on the current canonical shape (tests/db/test_eventbus_schema_equivalence.py, tests/eventbus/test_eventbus_migrations.py)
2. **Phase 2: Canonical DDL move to version 6 (REQ-005)**
   - [ ] Remove the table-level duplicate FK clause and stamp `PRAGMA user_version = 6` (scripts/eventbus/schema.sql)
   - [ ] Move the version contract lock from 5 to 6 (tests/eventbus/test_eventbus_schema_version.py)
3. **Phase 3: Registered 5 -> 6 rebuild step (REQ-005, REQ-006)**
   - [ ] Implement `eventbus_dlq_outbox_fk_dedup` with the Design 3 contract, using `pre_commit_verification` per the dbmigsafe001 Plan's callback contract (scripts/eventbus/migrations.py)
   - [ ] Registry pin update + step tests (row/index preservation, pre-commit rollback, single FK entry) (tests/eventbus/test_eventbus_migrations.py)
   - [ ] Fresh-versus-migrated convergence test at version 6 with seeded `dlq_outbox` rows (tests/db/test_eventbus_schema_equivalence.py)
4. **Phase 4: Three-path `create_eventbus_schema` (REQ-001, REQ-002, REQ-003)**
   - [ ] Implement paths (a)-(d) of Design 1 with `validate_canonical`; delete the existing-database `executescript` call and the version-0 reset branch; refusal messages name the CLI/recreate route and contain no row content (scripts/db/create_schema.py)
   - [ ] Snapshot-based negative tests for each refusal branch + no-DDL-on-existing spy test (tests/db/test_create_schema.py)
5. **Phase 5: Documentation (REQ-007)**
   - [ ] Rewrite the stale version/ADR passage and add the three paths, fingerprint contract, version-6 chain, and FK change (docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md)
   - [ ] Update the eventbus migration passage to the three-step version-6 chain (docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md)
6. **Phase 6: Full verification and operational checks**
   - [ ] Run the issue-mandated pytest selection, then full suite, ruff, mypy, `lint-imports` (no new cross-layer imports), `tools/check_db_separation.py`, and the docs/ADR checkers per `rules/toolchain.md`
   - [ ] Scratch-database recipe rehearsal (rules/persisted-schema-change.md) of the 5 -> 6 step against a seeded version-5 database; record results here before deployment; confirm `init_db.sh` fresh-path behavior is unchanged (scripts/eventbus/migrations.py, scripts/db/create_schema.py — inspection/tests only)

### Release units
**Unit**: canonical-version-6 | **Phases**: 2, 3 | **Reason**: `scripts/eventbus/schema.sql` stamping 6 while the 5 -> 6 registry step does not yet exist leaves migrated version-5 databases refused by both the startup gate and the equivalence tests; the two phases must be validated together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/create_schema.py | Unit with sqlite_master/user_version snapshots | `uv run pytest tests/db/test_create_schema.py -q` | Every refusal branch leaves the database byte-unchanged; fresh path stamps 6 with baseline row |
| scripts/eventbus/schema.sql + scripts/eventbus/migrations.py | Integration: chain 3->4->5->6 on scratch DB, seeded rows | `uv run pytest tests/eventbus/test_eventbus_migrations.py tests/db/test_eventbus_schema_equivalence.py -q` | Registry pin = 3 steps; convergence equal; `foreign_key_list(dlq_outbox)` length 1 |
| scripts/shared/eventbus_schema_fingerprint.py | Unit: view/predicate/version deviations | `uv run pytest tests/db/test_eventbus_schema_equivalence.py tests/eventbus/test_eventbus_migrations.py -q` | `validate_canonical` refuses version mismatch; coverage extension shows no false positive on current canonical |
| scripts/eventbus/schema.py (unchanged) | Regression: startup gate behavior | `uv run pytest tests/eventbus/ -q` | Startup paths green without modification |
| whole change | Static + layer + docs + separation | `uv run ruff check . && uv run mypy scripts/ && uv run pytest && lint-imports && uv run python tools/check_db_separation.py` | Clean; no new `db -> eventbus` import |
| docs rows | Docs/ADR checkers | `uv run python tools/check_docs.py` and the ADR checkers named in `routing.md` | No findings |

## Risks
- **Risk**: A deployed version-4/5 EventBus database somewhere unseen fails the extended fingerprint or the 5 -> 6 rebuild rehearsal. → **Mitigation**: UNK-01 blocks production rollout until the owner inventories databases; the scratch-DB rehearsal (Phase 6) is required evidence before deployment.
- **Risk**: The rebuild silently changes `dlq_outbox` semantics (CHECK vocabulary, defaults). → **Mitigation**: step tests seed all three status values plus NULL optionals and compare row-for-row after the rename; recipe step 3 comparisons.
- **Risk**: `create_eventbus_schema` refusals break `init_db.sh` flows on existing databases. → **Mitigation**: the fresh path (no events table) is unchanged; the refusal branches already refused before (differing version raised at L144-L148 today), so only the 0/current-version branches change from mutation to validation; Phase 6 verifies init_db.sh-path tests.
- **Risk**: Fingerprint extension makes error messages surface long predicate texts. → **Mitigation**: `_raise_first_difference` already prints expected/actual tuples; predicate text is normalized DDL, never row content (constraint satisfied — schema, not data).
- **Risk**: Two Plans edit `scripts/eventbus/migrations.py`, `tests/eventbus/test_eventbus_migrations.py`, and db_03 in adjacent cycles. → **Mitigation**: Depends-on on the dbmigsafe001 Plan (Scope); this Plan implements after it and re-verifies every shared row against the post-change file before editing.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Fingerprint contract extension | Pending | — | — | |
| 2 | Phase 2: Canonical DDL move to version 6 | Pending | — | — | |
| 3 | Phase 3: Registered 5 -> 6 rebuild step | Pending | — | — | |
| 4 | Phase 4: Three-path create_eventbus_schema | Pending | — | — | |
| 5 | Phase 5: Documentation | Pending | — | — | |
| 6 | Phase 6: Full verification and operational checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-234502
- **Related target files**: scripts/db/create_schema.py, scripts/eventbus/schema.sql, scripts/eventbus/migrations.py, scripts/shared/eventbus_schema_fingerprint.py, tests/db/test_create_schema.py, tests/db/test_eventbus_schema_equivalence.py, tests/eventbus/test_eventbus_migrations.py, tests/eventbus/test_eventbus_schema_version.py, docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| REQ | Source issue line | Acceptance criteria | Implementation target file | Test | Phase |
|---|---|---|---|---|---|
| REQ-001 | Required Changes bullets 1, 3 | AC-001, AC-002 | scripts/db/create_schema.py | tests/db/test_create_schema.py | 4 |
| REQ-002 | Required Changes bullet 2 | AC-001, AC-004 | scripts/db/create_schema.py, scripts/shared/eventbus_schema_fingerprint.py | tests/db/test_create_schema.py | 4 |
| REQ-003 | Required Changes bullet 3 | AC-003 | scripts/db/create_schema.py | tests/db/test_create_schema.py | 4 |
| REQ-004 | Required Changes bullet 4 | AC-004 | scripts/shared/eventbus_schema_fingerprint.py | tests/db/test_eventbus_schema_equivalence.py, tests/eventbus/test_eventbus_migrations.py | 1 |
| REQ-005 | Required Changes bullet 5 | AC-003, AC-005, AC-006 | scripts/eventbus/schema.sql, scripts/eventbus/migrations.py | tests/eventbus/test_eventbus_migrations.py, tests/eventbus/test_eventbus_schema_version.py | 2, 3 |
| REQ-006 | Constraints / AC-006 | AC-006 | scripts/eventbus/migrations.py | tests/db/test_eventbus_schema_equivalence.py | 3 |
| REQ-007 | Documentation Impact | AC-007 | docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | docs/ADR checkers | 5 |
