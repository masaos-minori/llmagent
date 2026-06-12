Refactor the memory layer according to the high-priority plan below. Follow these instructions strictly. Remove backward-compatibility code instead of preserving it.

# Overall goals

* Remove all backward-compatibility features that remain only for legacy support.
* Standardize the public API boundaries across the memory layer. Do not allow services or facades to depend on private methods or internal attributes of other components.
* Centralize SQLite persistence responsibilities in the store layer. Do not allow the facade or ingestion service to access SQLite directly for housekeeping or link management.
* Unify all retrieval scoring configuration under `ScoringPolicy`. Do not keep duplicated module-level scoring constants in `retriever.py`.

# File-specific instructions

## `layer.py`

* Remove the backward-compatibility constructor contract that preserves the old monolithic `MemoryLayer` signature. Redesign the constructor to match the current sub-service architecture.
* Remove the legacy `_fetch_embedding` re-export used only to keep old patch paths working in tests. Update tests to patch the new dependency path instead.
* Remove internal attribute access such as `self._ingestion._retriever`. Use only explicit public dependencies and public APIs.
* Move `clear()`, `prune()`, `count_prunable()`, and other direct SQLite housekeeping logic out of the facade and into the store layer.

## `types.py`

* Remove the backward-compatibility `SOURCE_TYPES` constant. Use `SourceType` as the only supported API for source type handling.

## `retriever.py`

* Remove all duplicated module-level scoring constants and move all scoring behavior under `ScoringPolicy`.
* Do not let other services call the private `_vec_search()` method. Introduce a public dedup-oriented retrieval API or another explicit public method for near-duplicate lookup.
* Remove the duplicated float-to-BLOB conversion logic and replace it with one shared implementation used by both retrieval and storage code.

## `scoring.py`

* Make `ScoringPolicy` the single source of truth for retrieval scoring parameters. Absorb all score-related constants currently defined in `retriever.py`.

## `ingestion.py`

* Remove `DedupAction.LINK_ONLY` if it exists only for backward compatibility. Keep only dedup behaviors that are still required by the current design.
* Stop calling `MemoryRetriever._vec_search()` directly from the ingestion service. Use a public API instead.
* Move `memory_links` writes into the store layer. Do not access SQLite directly from the ingestion service for duplicate-link persistence.

## `store.py`

* Make `MemoryStore` the single persistence entry point for memory data, duplicate links, housekeeping, and counts.
* Remove any duplicated BLOB packing logic and use one shared implementation across store and retriever.

## `embedding_client.py`

* Make `EmbeddingClient.fetch()` the only supported embedding access path. Do not preserve the module-level `_fetch_embedding()` path for legacy use.

## `injection.py`

* Remove the unused `dedup_window` field if it is still only a future placeholder. Do not keep unimplemented policy fields in the public API.
* Separate retrieval logic from snippet formatting. Do not keep search and UI-oriented string rendering in the same service responsibility.

## `extract.py`

* Move extraction rules out of module-level constants and into an explicit policy or strategy object. This includes thresholds, keyword rules, and importance heuristics.

# Backward-compatibility removals

* Remove `SOURCE_TYPES` from `types.py`.
* Remove the old-constructor compatibility behavior from `layer.py`.
* Remove the legacy `_fetch_embedding` re-export from `layer.py`.
* Remove `DedupAction.LINK_ONLY` from `ingestion.py` if it is only kept for compatibility.
* Remove the unused `dedup_window` field from `injection.py`.

# Priority order

1. Refactor `layer.py` to remove old `MemoryLayer` compatibility and the legacy `_fetch_embedding` re-export.
2. Remove `SOURCE_TYPES` from `types.py` and standardize on `SourceType`.
3. Unify scoring under `ScoringPolicy` across `retriever.py` and `scoring.py`.
4. Refactor dedup handling in `ingestion.py` to use public APIs only, and remove compatibility-only dedup modes.
5. Centralize persistence responsibilities in `store.py` and remove direct SQLite access from `layer.py` and `ingestion.py`.
6. Separate policy and formatting responsibilities in `injection.py` and `extract.py`.

# Output requirements

* For each modified file, report:
  * what changed
  * why it changed
  * which backward-compatibility feature was removed
  * any behavior change or migration note
