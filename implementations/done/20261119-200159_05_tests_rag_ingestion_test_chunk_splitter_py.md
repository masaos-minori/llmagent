## Goal

Rework the chunker construction helpers `_make_splitter` / `_make_ja_mixin` to build chunkers from the settings value object (row 1) and a stub tokenizer (row 2) without `object.__new__`, so tests no longer fabricate a host and assign a private attribute set (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `_make_splitter(md_index_enable=False)` (lines 25–28) currently does `object.__new__(ChunkSplitter)` and sets only `_md_index_enable`; it relies on mixin host attributes being present for any method that reads them. After rows 1–2 the splitter needs a `ChunkSettings` object and a tokenizer adapter.
- `_make_ja_mixin(**kwargs)` (lines 175–186) currently does `object.__new__(ChunkJapaneseMixin)` and assigns `_max_chunk`, `_min_chunk`, `_chunk_overlap`, `_ja_stop_pos`, `_sd_tkn=None`, `_split_c=None`, `_orig_buf=""`, `_norm_buf=""`. These are exactly the fabricated private attributes the plan removes.
- `TestJapaneseChunkOverlap` (from line 195) directly sets `mixin._orig_buf` / `mixin._norm_buf` and calls `_emit_and_start_new` / `_reset_buffer` (which mutate those instance buffers). Because row 4 removes those buffers and routes state through the per-call collaborator, these direct-mutation assertions must be updated to the new per-call contract.
- Scope boundary (UNK-03, Out-of-Scope): only the construction seam (`_make_splitter` / `_make_ja_mixin`) and the tests that break as a direct consequence of rows 2–4. The broader test-construction fragility cleanup is owned by `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` — do not touch it.
- Cross-plan overlap: `test_chunk_splitter.py` is also referenced by `ragcrv007` (sequencing dependency, verified compatible — different concerns).

## Design decisions
- `_make_splitter` constructs a real `ChunkSplitter` (or a minimal test double) seeded with a `ChunkSettings` value object and a stub tokenizer, instead of `object.__new__` + manual attr assignment. The exact construction strategy (real instance with a stub Sudachi vs. a lightweight double) is a design decision; choose the one that keeps the existing test behaviors valid.
- `_make_ja_mixin` builds a `ChunkJapaneseMixin` seeded with the settings value object and a stub tokenizer implementing the row-2 `Protocol`, replacing the `object.__new__` + private-attr pattern.
- `TestJapaneseChunkOverlap` assertions are rewritten to drive the collaborator / per-call contract rather than reading mutated `_orig_buf`/`_norm_buf`.

## Alternatives considered
- Keeping `object.__new__` + attr assignment vs. real construction: the plan forbids `object.__new__` (`REQ-005`) because it hides the missing-contract coupling; chosen.
- Reworking all test-construction helpers vs. only the construction seam: scoped to `_make_splitter`/`_make_ja_mixin` plus the directly-broken tests to avoid colliding with ragcrv009 (`UNK-03`); chosen.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Rewrite `_make_splitter` to construct the splitter from a `ChunkSettings` object and a stub tokenizer instead of `object.__new__(ChunkSplitter)`; keep the `md_index_enable` parameter.
2. Rewrite `_make_ja_mixin` to construct a `ChunkJapaneseMixin` from the settings value object and a stub tokenizer implementing the row-2 `Protocol`; drop `_sd_tkn`/`_split_c`/`_orig_buf`/`_norm_buf` assignment.
3. Update `TestJapaneseChunkOverlap` (and any other test that reads/writes `_orig_buf`/`_norm_buf` or depends on the old construction) to the new per-call collaborator contract.
4. Do not alter unrelated helpers, fixtures, or tests outside the construction seam and the directly-broken assertions.

### Method
- Preserve each existing test's intent (overlap tail carry, fresh-start, below-min reset, consecutive-overlap preservation) while expressing it through the new construction + per-call API.
- Introduce a small stub tokenizer fixture implementing the row-2 `Protocol` so no real Sudachi dictionary is needed in unit tests.

### Details
- Grep the whole file for `object.__new__`, `_orig_buf`, `_norm_buf`, `_sd_tkn`, `_split_c` to enumerate every site that must change; confirm the list equals the construction seam plus the directly-broken assertions before editing.
- Keep changes minimal: do not fold in the broader fragility cleanup (ragcrv009).

## Compatibility considerations
- This is a test-only change; production code is untouched by this row (`REQ-004`).
- Must stay compatible with `ragcrv007`'s references to `test_chunk_splitter.py` (sequencing dependency).

## Security considerations
N/A: test construction only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `uv run mypy --no-namespace-packages tests/rag/ingestion/test_chunk_splitter.py` clean; zero `Any` in the tokenization path (`REQ-006`).
- `rg "object\.__new__" tests/rag/ingestion/test_chunk_splitter.py` returns no matches (`REQ-005`).
- Regression: `uv run pytest tests/rag/ingestion/` green (`REQ-004`).

## Completion criteria
- `_make_splitter` / `_make_ja_mixin` construct from the settings object and a stub tokenizer with no `object.__new__`; no `_orig_buf`/`_norm_buf` reads/writes remain; suite green.

## Out of Scope
- The value object definition — row 1.
- The tokenizer `Protocol` definition and `__init__` injection — row 2.
- Buffer removal in the mixins — rows 3–4.
- The broader test-construction cleanup — `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | |

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
- **Requirement ID**: `REQ-005` (construct from settings object + stub tokenizer, no `object.__new__`), `REQ-006` (no `Any`)
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-190454_ragcrv006_chunk-mixin-state-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-200159
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
