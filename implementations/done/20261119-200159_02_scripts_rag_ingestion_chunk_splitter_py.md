## Goal

Construct the `ChunkSettings` value object once in `ChunkSplitter.__init__` and inject the tokenizer adapter behind a local `Protocol` in place of the `Any`-typed `_sd_tkn` / `_split_c`, while keeping `ChunkSplitter.__init__(config)`'s public signature and the Sudachi dictionary build intact (`REQ-001`, `REQ-004`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ChunkSplitter.__init__(self, config: dict | None = None)` keeps its signature; the settings object is an internal construction detail (`REQ-004`, `UNK-01`).
- The Sudachi build stays in `__init__`: `sd_dict = sudachi_dict.Dictionary(dict=resolve_sudachi_dict_path()); self._sd_tkn = sd_dict.create()` (lines 134–135) and `self._split_c = sudachi_tok.Tokenizer.SplitMode.C` (line 136), where `sudachi_tok = from sudachipy import tokenizer as sudachi_tok`.
- Validation (lines 96–130) runs before Sudachi construction and is unchanged; the settings object is built from the already-validated values.
- The mixins receive settings through the collaborator; how they consume it (parameter vs. a typed host attribute) is a design decision for `python-refactoring` to resolve against the current call chain (`_build_chunk_list` → `_chunk_english` / `_normalize_ja_sentence`).
- Cross-plan overlap: `chunk_splitter.py` is also targeted by `ragcrv007` (`ChunkRunResult` / `run_all` / narrowed `except`) — a sequencing dependency; the two changes touch disjoint regions (`__init__`/construction vs. `process_all`/`main`). Verify at implementation that the `run_all` refactor (ragcrv007 Phase 1–2) does not disturb the settings-construction edit.

## Design decisions
- Build `ChunkSettings` from the validated locals (`min_chunk`, `max_chunk`, `chunk_overlap`, `md_index_enable`, `md_snippet_max_chars`, `en_stopwords`, `ja_stop_pos`) in one statement after line 131, before the Sudachi block.
- Define a local `Tokenizer` `Protocol` in `chunk_splitter.py` (or co-locate with the settings object) describing exactly the two Sudachi operations used by `_normalize_ja_sentence`: `tokenize(text, mode)` returning an iterable of token-like objects, each exposing `part_of_speech() -> list[str]` (caller reads `[0]`) and `normalized_form() -> str`. Type the injected adapter against this `Protocol` so no `Any` remains in the path (`REQ-006`).

## Alternatives considered
- Keeping `Any` on `_sd_tkn` vs. a `Protocol`: the `Protocol` restores static checking of the Sudachi boundary (`REQ-006`); chosen.
- Injecting the tokenizer via a constructor parameter vs. a host attribute: the plan keeps `__init__(config)` unchanged, so the adapter is stored on the instance behind the `Protocol` type, not passed per call.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. After the validation block (line 131), construct `self._settings = ChunkSettings(...)` from the seven validated values.
2. Replace `self._sd_tkn` / `self._split_c` storage with a single typed adapter field `self._tokenizer: Tokenizer` (the `Protocol`), still assigned from `sd_dict.create()` / `SplitMode.C`.
3. Keep `process_all`, `process_file`, and the rest of the public interface unchanged.

### Method
- Preserve the Sudachi dictionary resolution and `SplitMode.C` selection exactly; only the stored type changes from `Any` to the `Protocol`.
- Do not touch `process_all`'s `except (OSError, RuntimeError, ValueError)` tuple (line 150) — that is ragcrv007's concern.

### Details
- The mixins currently read `self._min_chunk` etc.; the mechanism by which they now read `self._settings.<field>` (thin property accessors vs. passing `self._settings` into mixin methods) is a design decision — record the chosen mechanism in the procedure's Method and apply it consistently across `chunk_english.py` and `chunk_japanese.py`.

## Compatibility considerations
- `ChunkSplitter`'s public API (`process_all`, `process_file`, `publish_chunk_files`, `cleanup_chunk_files`) and the chunk file format are unchanged (`REQ-004`).
- The internal field rename (`_sd_tkn`/`_split_c` → `_tokenizer`) must not be referenced by any test outside this plan's test-row rework.

## Security considerations
N/A: construction typing only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `uv run mypy --no-namespace-packages scripts/rag/ingestion/chunk_splitter.py scripts/rag/models_data.py` clean; zero `Any` in the tokenizer path.
- Regression: `uv run pytest tests/rag/ingestion/` green.

## Completion criteria
- `ChunkSettings` constructed once in `__init__`; tokenizer stored behind the local `Protocol` with no `Any` in the tokenization path; public API and Sudachi build unchanged.

## Out of Scope
- Building the value object's fields — row 1 (`models_data.py`).
- Dropping `self._buf` from the English mixin — row 3.
- Removing `_orig_buf`/`_norm_buf` from the Japanese mixin — row 4.
- Narrowing `process_all`'s except and adding `run_all` — `ragcrv007`.

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
- **Requirement ID**: `REQ-001` (construct settings object), `REQ-004` (public API/format unchanged), `REQ-006` (no `Any` in tokenizer path)
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-190454_ragcrv006_chunk-mixin-state-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-200159
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
