# Chunk tests bypass the constructor and leave the size rules untested

## Priority
Medium

## Summary
The chunk unit tests fabricate objects with `object.__new__` and assign private attributes, so constructor
validation and the public construction path are untested, and several chunk-size behaviors have no test at
all.

## Background
- `tests/rag/ingestion/test_chunk_splitter.py` uses `_make_splitter` (`object.__new__(ChunkSplitter)` plus
  `splitter._md_index_enable = ...`) and `_make_ja_mixin` for the merge tests; private attribute names are
  hard-coded in the tests.
- Other tests in the same file construct through the public constructor with a `config` dict
  (`TestProcessFileEndToEnd`, `_splitter_config`), so both patterns coexist.
- Verified coverage gaps at head `6bdced7bb` (each reproduced by direct execution, not by reading tests):
  an oversized first Japanese sentence producing an empty chunk; `min_chunk > max_chunk` yielding zero
  chunks; `chunk_overlap >= max_chunk` yielding chunks above `max_chunk`; English stopword filtering effect
  on stored content (every English test uses `en_stopwords: []`); a Markdown section or code block below
  `min_chunk` yielding zero chunks with no warning.
- `tests/rag/ingestion/` chunk suite: 88 tests pass in 1.19 s (`uv run pytest tests/rag/ingestion/test_chunk_splitter.py
  tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py -q`).

## Problem
A test that fabricates the object keeps passing when `__init__` changes or when a private attribute is
renamed, and the size rules that most often cause corpus damage have no regression coverage.

## Reason for Change
The chunk-size findings in this review were all found by manual execution because no test exercises them.
Those fixes need tests that exist before them.

## Implementation Intent
Move chunk tests onto the public construction seam with an injected settings object and a stub tokenizer,
and add the missing size-rule cases as regression tests, one per behavior rather than one per finding.

## Target Files or Areas
- `tests/rag/ingestion/test_chunk_splitter.py`
- `tests/rag/ingestion/test_chunk_utils.py`
- `tests/rag/ingestion/test_chunk_grouping.py` (only where a shared fixture is reused)

## Required Changes
- Replace `object.__new__` construction with the public constructor plus a `config` dict, or with the
  collaborator seam introduced by issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md.
- Inject a stub tokenizer so Japanese tests do not depend on the Sudachi dictionary.
- Add regression tests for: oversized first sentence, `min_chunk > max_chunk`, `chunk_overlap >= max_chunk`,
  English stopword effect on stored `content`, below-`min_chunk` Markdown section, below-`min_chunk` code
  block.
- Share one config-builder fixture instead of repeating config dicts.

## Constraints
- Tests must not touch `/opt/llm` paths; the `tests/conftest.py` isolation guard and the
  `production_paths_allowed` marker stay in force.
- Do not encode private attribute names in new tests.
- Keep tests deterministic: no reliance on Sudachi dictionary availability in unit tests.

## Acceptance Criteria
- No test constructs a chunk object with `object.__new__`.
- Each behavior listed under Required Changes has a named test that fails when the behavior regresses.
- The chunk suite runs without the Sudachi dictionary being loaded in unit-level tests.

## Testing Expectations
- This issue is the test work; verify each added test by breaking the corresponding behavior once and
  confirming the failure names the rule.
- Run `uv run pytest tests/rag/ingestion -q` and confirm no new isolation-guard failures.

## Documentation Impact
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`: link the size-rule behaviors to the tests that
guarantee them, following the existing invariant-matrix style.

## Out of Scope
- Changing production chunking behavior (each fix is filed separately).
- Coverage of the crawler or search layers.

## Dependencies
- Depends on: issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md, issues/20261119-112014_ragcrv002_english-content-stopword-loss.md, issues/20261119-112015_ragcrv003_chunk-config-validation.md for the behaviors being locked
  down; the tests for the defects themselves should land with those fixes, and this issue covers the
  construction and fixture restructuring.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Add the regression tests in the same commit as each behavior fix, not later. Do not assert on private
attribute names.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-009`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112021
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`, `tests/rag/ingestion/test_chunk_utils.py`, `tests/rag/ingestion/test_chunk_grouping.py`
