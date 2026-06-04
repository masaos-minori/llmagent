# Refactoring Instructions for Claude Code

## Overall Policy

* Remove all remaining legacy features, classes, and settings that are kept only for backward compatibility.
* Do not preserve backward-compatibility leftovers unless there is a clear, explicit requirement to keep them.
* Simplify the codebase by eliminating transitional compatibility layers.

***

## `db/helper.py`

* Remove the module-global `_cfg` cache from `_get_cfg()`.

* Do not keep configuration state hidden at module scope.

* The current design makes config reload behavior, test substitution, and in-process consistency unclear.

* Minimize side effects in the connection-management layer.

* Move configuration retrieval to one of the following:
  * explicit dependency injection
  * a dedicated config service

* Split the responsibilities currently concentrated in `SQLiteHelper`.

* Do not let one class own all of the following:
  * connection policy
  * config loading
  * sqlite-vec extension setup
  * WAL / `busy_timeout` setup

* Separate:
  * low-level connection creation
  * DB policy application

***

## `db/migrate.py`

* Refactor `_copy_table()`.

* Do not use a naive `SELECT * -> INSERT OR IGNORE` copy strategy.

* This is too fragile with respect to:
  * column order
  * schema differences
  * future column additions/removals

* Explicitly declare the column list.

* Validate source/destination schema differences before copying.

* Copy by named columns, not by implicit table shape.

* Remove the hard dependency on the `_SESSION_TABLES` hardcoded list.

* This is safe in the short term, but it is too easy to miss schema evolution later.

* Tie migration targets to schema versions instead of maintaining a static table list by hand.

* `memory_vec` is currently treated as “re-embedding required after migration,” but the code does not make the post-migration recovery process explicit.

* Make the migration script produce a structured report that clearly states:
  * what was not migrated
  * what must be rebuilt afterward
  * how completion should be judged
  * what the partial-recovery strategy is

***

## `db/store.py`

* Strengthen the contract between Protocols and concrete implementations.

* The abstraction boundaries exist, but the implementation responsibilities are still too vague.

* Do not rely on Protocol definitions alone to define behavior.

* Explicitly define:
  * transaction boundaries
  * exception contracts
  * return-type guarantees

* Introduce explicit domain result types where needed.

* Remove the hardcoded `EMBEDDING_DIMS = 384` assumption from module-level constants.

* Do not require simultaneous edits across schema, validator, maintenance, and migration whenever the embedding model changes.

* Bind embedding dimensions to one of the following:
  * configuration
  * schema metadata
  * a shared embedding metadata source

***

## `db/maintenance.py`

* Do not silently fall back to `None` or empty collections on DB errors.

* Silent fallbacks make persistence failures hard to detect from user workflows and follow-up logic.

* REPL continuity is important, but you must not allow silent data loss.

* At minimum, add:
  * audit events for failures
  * failure counters / metrics
  * explicit visibility for write failures

* `tool_results` is used under the assumption that full text is stored there instead of in LLM history.

* Failures in this store directly affect the reliability of `/tool show`.

* Apply differentiated failure policy based on importance:
  * fail-open where acceptable
  * fail-closed where required

* Alternatively, leave an explicit hint in history whenever persistence fails.

***

## `db/tool_results.py`

* Remove the same style of global `_cfg` caching used elsewhere.

* Do not let the operational policy layer depend on implicit module-level config state.

* Operational policy must emphasize reproducibility and explicitness.

* Move toward explicit config injection.

* Refactor `prune_old_memories()`.

* Do not keep separate deletion logic for:
  * `memories`
  * `memories_fts`
  * `memories_vec`

* The current design spreads cross-table consistency responsibilities into `maintenance.py`.

* Even if skipping `memories_vec` deletion was added for backward compatibility, that consistency logic should not live in maintenance code.

* Unify deletion through a single store-layer API.

* Add consistency checks as part of that API.

* Refactor `recover_corruption()`.

* The current design intends to perform archive + restore after corruption detection, but the code does not make the following explicit enough:
  * recovery success criteria
  * behavior when no backup is provided
  * side-effect ordering guarantees

* Convert recovery into a structured flow that includes:
  * dry-run mode
  * precheck step
  * structured restore result

***

## `db/create_schema.py`

* Separate initial schema creation from backward migration logic.

* Do not keep `_RAG_SCHEMA_SQL` / `_SESSION_SCHEMA_SQL` tightly coupled with `_RAG_MIGRATE_SQL` / `_SESSION_MIGRATE_SQL` in one file.

* This may be convenient early on, but it becomes increasingly dangerous as schema versions grow.

* Move to versioned migrations.

* Separate:
  * DDL baseline
  * incremental migration steps

* Refactor `_run_migrations()`.

* Do not treat all migration DDL failures as no-ops merely because they might already have been applied.

* Distinguish safe failures from dangerous failures.

* Allow only known idempotent cases such as:
  * duplicate column
  * duplicate trigger

* Treat all other failures as real migration errors.

* Remove the coexistence of old and new memory tables in the session schema.

* Do not keep both:
  * old `memory_entries` / `memory_vec`
  * new `memories` / `memories_fts` / `memory_links` / `memories_vec`

* Drop the old tables.

* Remove dual hardcoding of embedding dimensions.

* Do not hardcode vec0 embedding dimension as `384` in both:
  * the DDL
  * `store.py`

* This creates duplicate fixed assumptions and scatters model-change impact.

* Unify the embedding dimension in one of the following:
  * schema metadata
  * a shared constant source

***

## General Implementation Rules

* Prefer explicit dependency injection over hidden global state.
* Prefer structured reports over implicit success/failure behavior.
* Prefer single-responsibility modules over mixed concerns.
* Eliminate compatibility leftovers instead of preserving them by default.
* Make migration, recovery, pruning, and persistence behavior explicit and machine-readable.
* Do not hide important operational failures behind permissive fallbacks.
