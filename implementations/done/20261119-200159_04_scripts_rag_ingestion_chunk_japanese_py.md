## Goal

Route the Japanese mixin through the injected tokenizer `Protocol` and remove `_orig_buf`/`_norm_buf` and the `Any`-typed `_sd_tkn`/`_split_c` fields, so the mixin holds no undeclared host attributes and no unchecked `Any` in the tokenization path (`REQ-002`, `REQ-003`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ragcrv005` has already routed the accumulation loops through its accumulator, so `_orig_buf`/`_norm_buf` are truly unused and safe to remove (`REQ-003`; plan Phase 4 dependency).
- `_normalize_ja_sentence` (lines 58–76) is the sole consumer of the tokenizer: `morphemes = self._sd_tkn.tokenize(text, self._split_c)` (line 63); each token exposes `m.part_of_speech()[0]` (line 70) and `m.normalized_form()` (line 73). The `Protocol` must capture exactly these two operations.
- `_merge_ja_sentence_pairs` (lines 78–128) and its helpers `_append_to_buffer`, `_emit_and_start_new`, `_reset_buffer`, `_merge_tail_into_last` all read/mutate `self._orig_buf` / `self._norm_buf`; after removal these drive the collaborator (ragcrv005) instead of instance state.
- The mixin still declares `_max_chunk`, `_min_chunk`, `_chunk_overlap`, `_ja_stop_pos` — received via the settings value object (rows 1–2), not as undeclared host attributes.
- Cross-plan overlap: `chunk_japanese.py` is not targeted by `ragcrv007`; no cross-plan interaction here.

## Design decisions
- Define the local `Tokenizer` `Protocol` (co-located with the one in `chunk_splitter.py`, or import it) describing `tokenize(text, mode) -> Iterable[_Token]` where `_Token` exposes `part_of_speech() -> list[str]` and `normalized_form() -> str`; type the injected adapter against it so no `Any` remains in the path (`REQ-006`).
- Store the adapter as a single typed field (e.g. `self._tokenizer: Tokenizer`) assigned in `ChunkSplitter.__init__` from `sd_dict.create()` (row 2), replacing `self._sd_tkn: Any` / `self._split_c: Any`.
- Remove `_orig_buf`/`_norm_buf` declarations and all assignments; buffer state becomes per-call, owned by the ragcrv005 accumulator. Rewrite the four helpers to operate on collaborator return values rather than mutating instance buffers.

## Alternatives considered
- Keeping `Any` on `_sd_tkn` vs. a `Protocol`: the `Protocol` restores static checking of the Sudachi boundary (`REQ-006`); chosen.
- Keeping `_orig_buf`/`_norm_buf` as declared attributes vs. removing them: the plan removes them because the accumulator owns per-call state (`REQ-003`); chosen.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`

### Procedure
1. Remove the `_orig_buf: str` / `_norm_buf: str` declarations (lines 36–37) and the `Any`-typed `_sd_tkn`/`_split_c` declarations (lines 32–35).
2. Replace `self._sd_tkn.tokenize(text, self._split_c)` in `_normalize_ja_sentence` with the typed adapter `self._tokenizer.tokenize(text, mode)`, preserving the `RuntimeError -> TokenizationError` mapping (lines 64–67) and the `part_of_speech()[0]` / `normalized_form()` logic unchanged.
3. In `_merge_ja_sentence_pairs` and `_append_to_buffer` / `_emit_and_start_new` / `_reset_buffer` / `_merge_tail_into_last`, remove every `self._orig_buf` / `self._norm_buf` read/write; route accumulation through the ragcrv005 collaborator instead of instance buffers.
4. Keep `_chunk_japanese` and `_split_into_ja_sentences` semantics intact (NFKC normalization, `。！？\n` split, empty-normalized → `None`).

### Method
- Preserve output byte-for-byte: `(original, normalized)` pairs, `max_chunk` segmentation via `_split_overlong`, short-buffer retention, tail merge, and `None` preservation. Only the storage mechanism changes (instance buffer → per-call collaborator).
- The exact mechanism (passing the collaborator into each helper vs. a thin accessor) is a design decision — apply it consistently and record it in the procedure's Method.

### Details
- Confirm no other method in `chunk_japanese.py` references `_orig_buf`/`_norm_buf` beyond the five identified before removing the declarations.
- The `mode` argument (`sudachi_tok.Tokenizer.SplitMode.C`, set in `chunk_splitter.py` line 136) is supplied by the adapter/collaborator, not read from a host attribute.

## Compatibility considerations
- `_chunk_japanese`'s signature and return type (`list[tuple[str, str | None]]`) are unchanged; chunk output is unchanged (`REQ-006`).
- Test helpers that directly set `_orig_buf`/`_norm_buf` (`TestJapaneseChunkOverlap`) must be reworked in row 5 to match the new per-call contract.

## Security considerations
N/A: morphological analysis typing and buffer ownership only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `uv run mypy --no-namespace-packages scripts/rag/ingestion/chunk_japanese.py scripts/rag/ingestion/chunk_splitter.py` clean; zero `Any` in the tokenization path.
- `rg "_orig_buf|_norm_buf" scripts/rag/ingestion/` returns no matches (`REQ-003`).
- Regression: `uv run pytest tests/rag/ingestion/` green.

## Completion criteria
- No `_orig_buf`/`_norm_buf`/`Any` fields remain; `_normalize_ja_sentence` typed against the `Protocol`; Japanese chunk output byte-identical.

## Out of Scope
- The value object definition — row 1.
- The tokenizer `Protocol` definition and `__init__` injection — row 2.
- Dropping `self._buf` from the English mixin — row 3.
- Test-construction rework — row 5.

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
- **Requirement ID**: `REQ-002` (tokenizer `Protocol`), `REQ-003` (remove buffer fields), `REQ-006` (no `Any`)
- **Source issue**: `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-190454_ragcrv006_chunk-mixin-state-coupling.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-200159
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`
