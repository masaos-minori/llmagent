# Chunk splitter config lacks cross-field and type validation

## Priority
High

## Summary
`ChunkSplitter.__init__` validates only `max_chunk > 0`. Contradictory chunk-size settings are accepted and
produce silently empty or oversized output instead of a configuration error.

## Background
- `ChunkSplitter.__init__` coerces values with `int()` and `bool()` and raises `PipelineValidationError`
  only when `max_chunk <= 0` (the guard added by
  `issues/done/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md`). Nothing relates
  `min_chunk`, `chunk_overlap`, or `md_snippet_max_chars` to `max_chunk`.
- Reproduced at head `6bdced7bb`:
  - `min_chunk=300`, `max_chunk=100` → 0 chunks written, INFO log only, process exits 0.
  - `min_chunk=40`, `max_chunk=100`, `chunk_overlap=150` → chunk lengths `75, 151, 226, 226, 226, 226`,
    i.e. every merged chunk above `max_chunk` and growing.
  - `min_chunk=40`, `max_chunk=120`, `md_snippet_max_chars` unset relation → Markdown sections are
    accepted at any size up to the fallback threshold with no relation to `min_chunk`.
- `rules/coding.md` "Type-coercion policy" prohibits bare `int()` coercion for `*_models.py` config
  loaders; this module loads config directly and is outside that stated scope.

## Problem
An operator can set `min_chunk` above `max_chunk`, or `chunk_overlap` at or above `max_chunk`, and the
pipeline silently produces no chunks or chunks that violate the configured upper bound. Neither the run
nor the logs distinguish a misconfiguration from a genuinely empty corpus.

## Reason for Change
Chunk-size bounds are the main quality control of the ingestion corpus, and the current guard covers one
of four interacting values. Misconfiguration is the most likely operator failure and is currently invisible.

## Implementation Intent
Validate the chunk-size group as one unit at the construction boundary, with clear typed getters that
reject wrong types out of range and raise `PipelineValidationError` naming the offending key and the
relation that failed. Keep validation in the config boundary, not inside the chunkers.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py` (`ChunkSplitter.__init__`)
- `config/chunk_splitter.toml`
- `docs/21_rag/rag_05_01-configuration-reference.md`
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Validate `min_chunk >= 0`, `min_chunk <= max_chunk`, `chunk_overlap >= 0`, and `chunk_overlap < max_chunk`.
- Validate `md_snippet_max_chars` against `min_chunk` and `max_chunk` when `md_index_enable` is used.
- Replace bare `int()`/`bool()` coercion with typed getters that reject the wrong type instead of
  coercing it.
- Report each rejected key with its name, the value read, and the constraint that failed.
- Document the accepted ranges and their relations in the config file and the configuration reference.

## Constraints
- `PipelineValidationError` remains the exception type for configuration faults.
- Existing defaults (`chunk_overlap` 50, `md_snippet_max_chars` 600) must keep working with the current
  `config/chunk_splitter.toml`.
- Must not change chunking behavior for any currently valid configuration.
- Test construction pattern that passes a `config` dict must keep working.

## Acceptance Criteria
- A config with `min_chunk > max_chunk` raises `PipelineValidationError` naming both keys.
- A config with `chunk_overlap >= max_chunk` raises `PipelineValidationError`.
- A config value of the wrong type (for example a string for `max_chunk`) is rejected rather than coerced.
- No valid existing configuration changes its chunk output.

## Testing Expectations
- Unit: `TestMaxChunkValidation` extended with each rejected relation and each wrong-type value.
- Unit: accepted boundary configurations produce the same chunk counts as before.
- Regression: the whole `tests/rag/ingestion/test_chunk_splitter.py` suite stays green.

## Documentation Impact
- `config/chunk_splitter.toml`: document the required relations between the four chunk-size keys.
- `docs/21_rag/rag_05_01-configuration-reference.md`: record valid ranges, relations, and the error raised
  on violation.

## Out of Scope
- Re-tuning the constants themselves (NC-034 was closed as "no rationale found" in
  `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md`).
- Changing any chunking algorithm.
- Config hot-reload or per-source overrides.

## Dependencies
- Sibling: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md covers the silent-discard logging this validation reduces but does not remove.
- Sibling: issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md must add the tests that currently cannot exercise constructor validation.

## Unresolved Questions
- Whether `rules/coding.md` type-coercion policy is intended to cover non-`*_models.py` config consumers
  such as this module — `Needs confirmation`; the policy text names only `*_models.py` loaders.

## AI Implementation Instruction
Validate in the constructor boundary only. Do not add per-chunker guards for the same values. Do not
suppress a type error with a coercion to make an existing test pass.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-003`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112015
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `config/chunk_splitter.toml`, `docs/21_rag/rag_05_01-configuration-reference.md`, `tests/rag/ingestion/test_chunk_splitter.py`
