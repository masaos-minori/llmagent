## Goal
Replace the chunk mixins' undeclared host-attribute and `Any`-typed-tokenizer coupling with explicit collaborators — a chunk-settings value object and a tokenizer adapter behind a local `Protocol` — so the chunkers can be constructed, tested, and reused without fabricating a private attribute set, while leaving chunk output and `ChunkSplitter`'s public API unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - Define a chunk-settings value object holding `min_chunk`, `max_chunk`, `chunk_overlap`, `md_snippet_max_chars`, `md_index_enable`, and the two stopword collections, constructed once in `ChunkSplitter.__init__`.
  - Define a tokenizer adapter `Protocol` for the Sudachi call used by `_normalize_ja_sentence` and inject it instead of the `Any`-typed `_sd_tkn` / `_split_c`.
  - Remove `_orig_buf`, `_norm_buf`, and `_buf` as instance attributes; buffer state becomes per-call (owned by the accumulator from `ragcrv005`).
  - Keep `ChunkSplitter` as the single public entry point so external callers are unchanged.
  - Update the chunker construction helpers in the test suite to build chunkers from the settings object and a stub tokenizer without `object.__new__`.
- **Out-of-Scope**:
  - Changing chunk selection rules or output.
  - The broader test-construction cleanup (`issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` owns that).
  - Extracting the accumulation loop (`issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md` owns the accumulator this plan's buffer removal depends on).
- **Dependencies**:
  - **Depends on**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md` | phase `all` | the `_buf`/`_orig_buf`/`_norm_buf` removal (Acceptance Criteria) requires `ragcrv005` to have routed the accumulation loops through its accumulator first, so the fields are unused. The settings-value-object and tokenizer-`Protocol` work is independent and may proceed before it.

## Background
- `ChunkJapaneseMixin` declares `_max_chunk`, `_min_chunk`, `_chunk_overlap`, `_ja_stop_pos`, `_orig_buf`, `_norm_buf`, and `_sd_tkn: Any` / `_split_c: Any`, documented as coming from `ChunkSplitter.__init__`. `ChunkEnglishMixin` declares four host attributes but assigns `self._buf`, which it never declares.
- `ChunkSplitter(ChunkEnglishMixin, ChunkJapaneseMixin)` sets those attributes in `__init__`, builds the Sudachi dictionary there (`sudachi_dict.Dictionary(dict=resolve_sudachi_dict_path()).create()`), and calls the mixin methods. Nothing enforces that a host supplies them; a missing attribute fails at call time with `AttributeError`.
- The only way to use a mixin is to fabricate the host: `tests/rag/ingestion/test_chunk_splitter.py` builds objects with `object.__new__(ChunkSplitter)` / `object.__new__(ChunkJapaneseMixin)` and assigns private attributes directly (`_make_splitter`, `_make_ja_mixin`), and several tests read/write `_orig_buf` / `_norm_buf` as if they were state.
- `Any` on `_sd_tkn` and `_split_c` keeps `mypy` clean while removing all checking of `tokenize(text, mode)` and part-of-speech access.
- No code outside `ChunkSplitter` and the tests references `ChunkEnglishMixin` / `ChunkJapaneseMixin`; the mixins are internal to the chunking path.
- Import-layer contract from `skills/DESIGN.md` is satisfied (`lint-imports`: 6 contracts kept), so this is a module-boundary problem, not a layer violation.

## Problem
The chunkers cannot be constructed, tested, or reused without knowing a private attribute set, and the tokenization boundary is unchecked. Buffer state that lives on the instance also outlives a failed call.

## Reason for Change
The chunking paths are about to be restructured (`issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`). Doing that on top of an implicit mixin contract would carry the coupling into the new design.

## Implementation Intent
Replace the mixin-plus-declared-host-attributes pattern with explicit collaborators that receive their inputs as constructor parameters: a chunk-size/overlap value object, a tokenizer adapter behind a local `Protocol` (so the Sudachi type is not `Any`), and per-call buffer state owned by the accumulator rather than the instance. Keep `ChunkSplitter` as the single public entry point.

## Requirements
- `REQ-001`: A chunk-settings value object holds `min_chunk`, `max_chunk`, `chunk_overlap`, `md_snippet_max_chars`, `md_index_enable`, and the two stopword collections, constructed once in `ChunkSplitter.__init__`.
- `REQ-002`: A tokenizer adapter `Protocol` describes the Sudachi call used by `_normalize_ja_sentence`; it is injected instead of the `Any`-typed `_sd_tkn` / `_split_c`.
- `REQ-003`: `_orig_buf`, `_norm_buf`, and `_buf` are removed as instance attributes; buffer state is per-call.
- `REQ-004`: `ChunkSplitter`'s public API (`process_all`, `process_file`, `publish_chunk_files`, `cleanup_chunk_files`) and the chunk file format are unchanged.
- `REQ-005`: The chunker unit tests construct chunkers from the settings object and a stub tokenizer without `object.__new__`.
- `REQ-006`: No `Any` remains in the tokenization call path; `mypy` passes.

## Implementation Target Files
**Freeze status**: Frozen (Step 8: all five rows `Verified`, `audit_plan_target_paths.py` reports 0 findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/models_data.py` | Modify | Add the chunk-settings value object (data class / `TypedDict`) constructed once in `ChunkSplitter.__init__` | REQ-001 | Holds domain data classes (`ChunkDocument`, `ChunkRecord`, `PreparedChunk`, …); issue candidate home | `test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Construct the settings object and inject the tokenizer adapter; keep public API and chunk file format | REQ-001, REQ-004, REQ-006 | `__init__` sets host attrs inline and builds Sudachi via `sudachi_dict.Dictionary().create()` in Step 2 | `test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_english.py` | Modify | Receive settings via the collaborator; drop the undeclared `self._buf` | REQ-003, REQ-006 | Assigns `self._buf` without declaring it; declares 4 host attrs in Step 2 | `test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Receive settings + injected tokenizer `Protocol`; remove `_orig_buf`/`_norm_buf` and `Any` fields | REQ-002, REQ-003, REQ-006 | Declares `_orig_buf`/`_norm_buf`/`_sd_tkn: Any`/`_split_c: Any` in Step 2 | `test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Rework `_make_splitter` / `_make_ja_mixin` to construct from the settings object and a stub tokenizer, no `object.__new__` | REQ-005, REQ-006 | Helpers use `object.__new__` + private-attr assignment; tests read/write `_orig_buf`/`_norm_buf` in Step 2 | `test_chunk_splitter.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Owns the accumulator (`ragcrv005`) that will own per-call buffer state; read to align the buffer-handling contract | REQ-003 |
| `scripts/rag/ingestion/chunk_preparation.py` | Feeds `_chunk_english` / `_chunk_japanese`; read to preserve feeding semantics when the constructor changes | REQ-004 |
| `tests/rag/ingestion/test_ingester.py` | Regression anchor around the chunkers | REQ-004 |
| `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Regression anchor for end-to-end chunk output | REQ-004 |

## Acceptance Criteria
- Neither mixin nor chunker class declares attributes it does not set itself (`REQ-001`, `REQ-003`; AC: code review).
- `mypy` passes with the tokenizer adapter `Protocol` and no `Any` in the tokenization call path (`REQ-002`, `REQ-006`; AC: `mypy` on `chunk_*.py`).
- `grep` finds no `_orig_buf`, `_norm_buf`, or `_buf` instance attribute in `scripts/rag/ingestion/` (`REQ-003`; AC: `grep`).
- `ChunkSplitter`'s public API and the chunk file format are unchanged (`REQ-004`; AC: `test_rag_ingestion_pipeline.py`).
- Chunkers are constructed with an explicit settings object and a stub tokenizer, no `object.__new__` (`REQ-005`; AC: `test_chunk_splitter.py`).

## Tests
- Unit: chunkers built with an explicit settings object and a stub tokenizer; no `object.__new__` (`REQ-005`).
- Static: `uv run mypy --no-namespace-packages scripts/rag/ingestion/chunk_*.py` clean; any remaining `Any` reported with its justification (`REQ-006`).
- Regression: the whole `tests/rag/ingestion/` chunk suite stays green (`REQ-004`).

## Documentation Impact
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` and `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (index keys `rag_02_07_n` / `rag_02_03`): replace the "mixed in via multiple inheritance" description with the collaborator ownership and the injected tokenizer boundary. Coordinate with `issues/20261119-112022_ragcrv010_chunking-docs-max-chunk.md` and with `ragcrv005` so both doc updates describe one design. Driven by `REQ-006`.

## Assumptions
- The chunk-settings value object belongs in `scripts/rag/models_data.py` alongside the other domain data classes; if the next phase prefers a dedicated module, it moves there — the plan constrains only that it is a single, importable value object.
- The tokenizer `Protocol` captures exactly the two operations actually used: `tokenize(text, mode)` returning a sequence of tokens and each token exposing `part_of_speech()[0]` and `normalized_form()`.
- `ragcrv005` and `ragcrv006` are complementary and sequenced (`ragcrv005` first): they share `chunk_english.py`, `chunk_japanese.py`, and `chunk_splitter.py` without contradicting each other on those files. The shared-file overlap is a sequencing dependency, not a conflict.
- The settings-value-object and tokenizer-`Protocol` work can proceed independently of `ragcrv005`; only the `_buf`/`_orig_buf`/`_norm_buf` removal waits for it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the existing mixins should remain as thin facades for compatibility with any external caller | No caller outside `ChunkSplitter` and the tests was found (Step 2); confirm no runtime/dynamic usage | Confirm via import scan at implementation; facades kept if any caller exists | False |
| UNK-02 | Exact placement of the chunk-settings value object (`models_data.py` vs a new module) | Module-organization convention | Decide at implementation; single importable value object either way | False |
| UNK-03 | Test-construction changes here vs the broader cleanup owned by `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` | Scope boundary between the two plans | Keep changes minimal to the construction seam here; hand the broader cleanup to `ragcrv009` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/models_data.py` | Modify | rag models consumers | N/A: tool unavailable | N/A: tool unavailable | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | ingestion entry point | 14 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_english.py` | Modify | `ChunkSplitter` English path | 2 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | `ChunkSplitter` Japanese path | 7 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | chunker unit tests | N/A | N/A | not applicable (rsynced) |

## Design
This is a behavior-preserving structural refactor (Path B: five target files, a new value object, a new `Protocol`, and a runtime-facing constructor contract). Execute under `python-refactoring`: behavior locked before and after; no intended behavior change.

### Current coupling (evidence)
`ChunkSplitter.__init__` sets `_min_chunk`, `_max_chunk`, `_chunk_overlap`, `_en_stopwords`, `_ja_stop_pos`, `_md_index_enable`, `_md_snippet_max_chars`, `_sd_tkn`, `_split_c` inline, and builds Sudachi via `sudachi_dict.Dictionary(dict=resolve_sudachi_dict_path()).create()`. The mixins then read these undeclared instance attributes. `ChunkEnglishMixin` assigns `self._buf` without declaring it; `ChunkJapaneseMixin` holds `_orig_buf`/`_norm_buf` and `_sd_tkn: Any`/`_split_c: Any`. Tests fabricate hosts with `object.__new__` and assign private attributes, and read/write the buffer fields directly.

### Settings value object
A single value object (data class or `TypedDict` in `scripts/rag/models_data.py`) aggregates the seven settings currently spread across `__init__`. `ChunkSplitter.__init__` validates once (existing range checks) and constructs it; the mixins receive it instead of reading host attributes. This collapses the undeclared-attribute coupling and gives tests one seam to inject.

### Tokenizer `Protocol`
A local `Protocol` describing exactly the two Sudachi operations used — a `tokenize(text, mode)` method returning token-like objects, and each token exposing `part_of_speech()` and `normalized_form()` — replaces `_sd_tkn: Any`. `_normalize_ja_sentence` is typed against the `Protocol`, restoring static checking of the tokenization boundary. Sudachi stays injectable so unit tests use a stub (no dictionary).

### Buffer-state removal
With `ragcrv005` routing accumulation through its accumulator, the mixin buffer fields become unused; remove `_buf`, `_orig_buf`, `_norm_buf` and make any remaining buffer handling per-call. This is the portion that depends on `ragcrv005`.

### Public-contract constraint
`ChunkSplitter`'s public methods and the chunk file output format are external contracts; the refactor rewrites only construction and internal ownership (`REQ-004`).

### importlinter
The `rag` package forbids importing `agent`/`mcp_servers`; the `Protocol` and value object stay within `rag`, so no package-boundary contract changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit when a phase breaks existing callers or tests until another phase lands.

1. **Phase 1: Settings value object**
   - [ ] Add the chunk-settings value object to `scripts/rag/models_data.py` (`REQ-001`).
   - [ ] Construct it once in `ChunkSplitter.__init__` from the existing validation; keep the public API (`REQ-001`, `REQ-004`).
2. **Phase 2: Tokenizer `Protocol`**
   - [ ] Define the local tokenizer `Protocol` and type `_normalize_ja_sentence` against it; inject the adapter (`REQ-002`, `REQ-006`).
   - [ ] Confirm `mypy` is clean on the tokenization path (`REQ-006`).
3. **Phase 3: Route the English mixin**
   - [ ] Receive settings via the collaborator and drop the undeclared `self._buf` (`REQ-003`).
4. **Phase 4: Route the Japanese mixin**
   - [ ] Remove `_orig_buf`/`_norm_buf` and the `Any` fields; use the injected tokenizer (`REQ-002`, `REQ-003`).
   - [ ] NOTE: this phase depends on `ragcrv005` having removed the accumulation loops so the fields are truly unused.
5. **Phase 5: Test construction seam**
   - [ ] Rework `_make_splitter` / `_make_ja_mixin` to build from the settings object and a stub tokenizer, no `object.__new__` (`REQ-005`).
6. **Phase 6: Verify**
   - [ ] Run `mypy` on `chunk_*.py` and the full `tests/rag/ingestion/` suite; assert zero regressions and no `Any` in the tokenization path (`REQ-004`, `REQ-006`).

### Release units
N/A: no release unit — each phase lands in a testable state (mypy clean after Phase 2; regression green after Phase 6).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Settings value object | Static typing | `uv run mypy --no-namespace-packages scripts/rag/models_data.py` | Clean |
| Tokenizer `Protocol` | Static: no `Any` in tokenization path | `uv run mypy --no-namespace-packages scripts/rag/ingestion/chunk_*.py` | Clean; `Any` count 0 in path |
| Buffer removal | `grep` for removed fields | `rg "_orig_buf|_norm_buf|self\._buf" scripts/rag/ingestion/` | No matches |
| Public API / output | Regression | `uv run pytest tests/rag/ingestion/` | Green |
| Construction seam | Unit: no `object.__new__` | `rg "object\.__new__" tests/rag/ingestion/test_chunk_splitter.py` | No matches |

## Risks
- **Risk**: Removing `_buf`/`_orig_buf`/`_norm_buf` while `ragcrv005` has not yet removed the loops leaves dead-but-live state or a broken call. → **Mitigation**: sequence the field removal after `ragcrv005`; Phase 4 records the dependency explicitly.
- **Risk**: Changing the constructor signature breaks `ChunkSplitter` callers. → **Mitigation**: keep `ChunkSplitter.__init__(config)` unchanged externally; the settings object is an internal construction detail (`REQ-004`).
- **Risk**: Overlapping `test_chunk_splitter.py` with `ragcrv009`'s broader cleanup. → **Mitigation**: keep changes here minimal to the construction seam; hand the broader cleanup to `ragcrv009` (`UNK-03`).
- **Risk**: The `Protocol` omits an operation actually used elsewhere. → **Mitigation**: scope it to the two verified operations (Step 2 evidence) and let `mypy` catch any miss.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Settings value object | In Progress | — | — | |
| 2 | Phase 2: Tokenizer `Protocol` | In Progress | — | — | |
| 3 | Phase 3: Route the English mixin | In Progress | — | — | |
| 4 | Phase 4: Route the Japanese mixin | In Progress | — | — | Depends on ragcrv005 |
| 5 | Phase 5: Test construction seam | In Progress | — | — | |
| 6 | Phase 6: Verify | In Progress | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261119-200159_01_scripts_rag_models_data.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261119-200159_02_scripts_rag_ingestion_chunk_splitter_py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261119-200159_03_scripts_rag_ingestion_chunk_english_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261119-200159_04_scripts_rag_ingestion_chunk_japanese_py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261119-200159_05_tests_rag_ingestion_test_chunk_splitter_py.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-190454
- **Related target files**: `scripts/rag/models_data.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (settings value object) | `scripts/rag/models_data.py`, `scripts/rag/ingestion/chunk_splitter.py` | Step 1 | No undeclared host attrs | code review | Confirmed by repository evidence |
| REQ-002 | Required Changes (tokenizer protocol) | `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_splitter.py` | Step 2 | No `Any` in tokenization path | `mypy` on `chunk_*.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (remove buffer fields) / AC | `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_japanese.py` | Steps 3–4 | No `_buf`/`_orig_buf`/`_norm_buf` | `grep` + code review | Confirmed by repository evidence |
| REQ-004 | Constraints (public API / format) | `scripts/rag/ingestion/chunk_splitter.py` | Steps 1, 6 | Public API / format unchanged | `test_rag_ingestion_pipeline.py` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations (construction) | `tests/rag/ingestion/test_chunk_splitter.py` | Step 5 | No `object.__new__` | `rg "object.__new__"` | Confirmed by repository evidence |
| REQ-006 | Constraints (mypy) / Testing Expectations (static) | `scripts/rag/ingestion/chunk_*.py` | Steps 2, 6 | `mypy` clean, no `Any` | `mypy --no-namespace-packages` | Confirmed by repository evidence |
