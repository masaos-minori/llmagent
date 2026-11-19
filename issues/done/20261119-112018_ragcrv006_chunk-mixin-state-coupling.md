# Chunk mixins depend on undeclared host state and Any-typed collaborators

## Priority
Medium

## Summary
`ChunkEnglishMixin` and `ChunkJapaneseMixin` are used only through `ChunkSplitter`, and reach their inputs
by declaring attributes that the host constructor owns, including two `Any`-typed Sudachi fields and
mutable buffer fields. The mixins have no contract of their own.

## Background
- `ChunkJapaneseMixin` declares `_max_chunk`, `_min_chunk`, `_chunk_overlap`, `_ja_stop_pos`,
  `_orig_buf`, `_norm_buf`, and `_sd_tkn: Any` / `_split_c: Any` with the comment that values come from
  `ChunkSplitter.__init__`. `ChunkEnglishMixin` declares four host attributes but uses `self._buf`, which
  it never declares.
- `ChunkSplitter(ChunkEnglishMixin, ChunkJapaneseMixin)` sets those attributes in `__init__`, builds the
  Sudachi dictionary there, and calls the mixin methods. Nothing enforces that a host supplies them; a
  missing attribute fails at call time with `AttributeError`.
- Because the only way to use a mixin is to fabricate the host, `tests/rag/ingestion/test_chunk_splitter.py`
  builds objects with `object.__new__(ChunkSplitter)` and assigns private attributes directly
  (`_make_splitter`, `_make_ja_mixin`).
- `Any` on `_sd_tkn` and `_split_c` is what keeps `mypy` clean while removing all checking of the
  tokenization call (`tokenize(text, mode)`) and the part-of-speech access.
- Import-layer contract from `skills/DESIGN.md` is satisfied (`lint-imports`: 6 contracts kept), so this is
  a module-boundary problem, not a layer violation.

## Problem
The chunkers cannot be constructed, tested, or reused without knowing a private attribute set, and the
tokenization boundary is unchecked. Buffer state that lives on the instance also outlives a failed call.

## Reason for Change
The chunking paths are about to be restructured (issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md). Doing that on top of an implicit
mixin contract would carry the coupling into the new design.

## Implementation Intent
Replace the mixin-plus-declared-host-attributes pattern with explicit collaborators that receive their
inputs as constructor parameters: a chunk-size/overlap value object, a tokenizer adapter behind a local
`Protocol` (so the Sudachi type is not `Any`), and per-call buffer state owned by the accumulator rather
than the instance.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_english.py`
- `scripts/rag/ingestion/chunk_japanese.py`
- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/models_data.py` (if a chunk-settings value object belongs there)

## Required Changes
- Define a settings value object holding `min_chunk`, `max_chunk`, `chunk_overlap`, `md_snippet_max_chars`,
  `md_index_enable`, and the two stopword collections, constructed once in `ChunkSplitter.__init__`.
- Define a tokenizer adapter protocol for the Sudachi call used by `_normalize_ja_sentence`, and inject it
  instead of `_sd_tkn` / `_split_c`.
- Remove `_orig_buf`, `_norm_buf`, and `_buf` as instance attributes.
- Keep `ChunkSplitter` as the single public entry point so callers are unchanged.

## Constraints
- `ChunkSplitter`'s public API (`process_all`, `process_file`, `publish_chunk_files`,
  `cleanup_chunk_files`) and the chunk file format must not change.
- The `rag` layer must not import from `agent` or `mcp_servers` (`.importlinter` contract).
- Sudachi must stay injectable so unit tests do not need the dictionary.
- No behavior change to chunk output.

## Acceptance Criteria
- Neither mixin nor chunker class declares attributes it does not set itself.
- `mypy` passes with the tokenizer adapter protocol and no `Any` in the tokenization call path.
- `grep` finds no `_orig_buf`, `_norm_buf`, or `_buf` instance attribute in `scripts/rag/ingestion/`.

## Testing Expectations
- Unit: chunkers constructed with an explicit settings object and a stub tokenizer, no `object.__new__`.
- Static: `uv run mypy --no-namespace-packages scripts/rag/ingestion/chunk_*.py` clean; `Any` usage
  reported with its justification.
- Regression: the whole `tests/rag/ingestion/` chunk suite stays green.

## Documentation Impact
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` and `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`:
replace the "mixed in via multiple inheritance" description with the collaborator ownership and the injected
tokenizer boundary.

## Out of Scope
- Changing chunk selection rules or output.
- Test restructuring beyond what the new constructor makes necessary (issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md owns the broader
  test-construction cleanup).

## Dependencies
- Related: issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md (the accumulator that removes buffer state) and issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md (tests
  that depend on the new construction seam).

## Unresolved Questions
- Whether the existing mixins should remain as thin facades for compatibility with any external caller —
  no caller outside `ChunkSplitter` and the tests was found; needs confirmation before removing them.

## AI Implementation Instruction
Do not type Sudachi objects with `Any` as a shortcut; define the protocol for the calls actually used.
Do not change chunk output while restructuring ownership.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-006`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112018
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/models_data.py`
