## Goal

Make `_merge_ja_sentence_pairs` and its buffer helpers share one caller-owned result accumulator so every emitted Japanese chunk is returned and no `AttributeError` is raised (REQ-001: single-accumulator fix).

## Scope
**Release unit**: ja-chunk-fix

## Assumptions

- Tail-merge semantics stay as currently implemented in `_merge_tail_into_last` (short tail merged into the last emitted chunk).
- The helper signature change is internal-only: the only consumers of `ChunkJapaneseMixin` are `scripts/rag/ingestion/chunk_splitter.py` and `tests/rag/ingestion/test_chunk_splitter.py` (re-verified via import scan in this cycle).

## Design decisions

- Caller-owned accumulator: `_merge_ja_sentence_pairs` keeps its local `result` list and passes it into `_emit_and_start_new` and `_merge_tail_into_last`; the never-initialized `_result` annotation (chunk_japanese.py:37) is deleted.
- Buffer attributes `_orig_buf` / `_norm_buf` remain instance state (mixin attribute-declaration pattern kept for type checkers); only the result accumulator moves to the caller.

## Alternatives considered

- Initialize `self._result` at merge start: rejected — it keeps cross-method instance state that leaks across `process_file` calls (the reproduction shows stale chunks surviving a run).

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`
### Procedure

- Give `_emit_and_start_new` (chunk_japanese.py:110) and `_merge_tail_into_last` (chunk_japanese.py:129) an extra `result` parameter typed `list[tuple[str, str | None]]`; replace `self._result.append` (chunk_japanese.py:112) and `self._result[-1]` read/rewrite (chunk_japanese.py:131-134) with `result.append` / `result[-1]`.
- Update the two call sites in `_merge_ja_sentence_pairs` (chunk_japanese.py:93 and chunk_japanese.py:102) to pass its local `result` list.
- Delete the `_result: list[tuple[str, str]]` annotation (chunk_japanese.py:37).

### Method

- Minimal refactor only: keep append semantics byte-identical (`result.append((self._orig_buf, self._norm_buf))`), so `TestJapaneseChunkOverlap` characterization assertions stay unchanged; do not normalize helper-emitted empty `norm` to `None` — the existing `None` mapping stays where it is (chunk_japanese.py:99, final emit only).
- Do not touch `_append_to_buffer`, `_reset_buffer`, `start_next_buf` usage, or the min/max chunk constraints.

### Details

- `start_next_buf` (chunk_utils.py:12) semantics must remain unchanged; the helpers call it exactly as today.
- `_chunk_japanese` public behavior is preserved: same overlap semantics, same min/max constraints, empty normalized result surfaced as `None` on the final emit.

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: Remove `_result` compensation — the `mixin._result` assignment in `_make_ja_mixin` (test_chunk_splitter.py:89) and `chunker._result = []` in `test_process_file_end_to_end_japanese` (test_chunk_splitter.py:651-653, with the two adjacent buffer assignments); add multi-emit `_merge_ja_sentence_pairs` regression tests (overlap > 0, overlap == 0, short-tail merge) asserting every emitted chunk is returned in order; strengthen the Japanese end-to-end assertion so reassembled chunk content covers the source content (REQ-002, REQ-003).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` — new tests must fail before the target fix and pass after it; then `uv run pytest tests/rag/ingestion`.

## Compatibility considerations

- Helper signatures change, but nothing outside the mixin and its tests calls them (`chunk_splitter.py` uses only `_chunk_japanese` via `_build_text_triples`).
- `tests/rag/ingestion/test_chunk_splitter.py` is co-targeted by plans `20261106-101257_raging004_force-rechunk-stale-chunks.md` and `20261106-103229_raging007_markdown-japanese-chunk-bypass.md` — implement this procedure before both to avoid rebase friction (recorded in the Plan's Related row).

## Security considerations

N/A: internal list accumulation change; no I/O, parsing, or credential handling.

## Rollback considerations

N/A: revert the single commit. Post-fix re-chunk of production Japanese sources (Plan UNK-01) is an operational check, not part of rollback.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Regression + end-to-end | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | Multi-emit tests fail pre-fix, pass post-fix; all emitted chunks returned |
| Ingestion suite | `uv run pytest tests/rag/ingestion` | All pass, no `_result` compensation anywhere |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| Coverage | `uv run coverage run -m pytest tests/` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Completion criteria

- AC-1: `_merge_ja_sentence_pairs` returns every emitted chunk in order (overlap emits + merged short tail), test-covered.
- AC-2: Japanese document longer than `max_chunk` chunks via `ChunkSplitter.process_file` without `AttributeError`, no compensation in the test.
- AC-3: No test pre-initializes internal state production does not; e2e assertions fail if any chunk is dropped.
- AC-4: `uv run pytest tests/rag/ingestion` passes and changed lines reach the ≥ 90% diff-cover threshold (`rules/toolchain.md`).

## Out of Scope

- English and Markdown chunking paths; overlap length tuning or config changes; Sudachi tokenizer behavior (Plan Scope).
- Documentation: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` already describes the intended behavior — no doc change required (Plan Documentation Impact).
- UNK-01 operational re-chunk of production data (post-deploy, user decision).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after step 2 tests exist (RED first, Plan Phase 1 → 2) |
| 2 | Add or update tests per Validation plan (companion `tests/rag/ingestion/test_chunk_splitter.py`) | Pending | — | — | Plan Phase 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes diff-cover ≥ 90% |

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
- **Requirement ID**: `REQ-001` (single-accumulator fix); companion procedure covers `REQ-002` (compensation removal) and `REQ-003` (regression tests)
- **Source issue**: `issues/20261106-073538_raging001_japanese-chunk-merge-crash.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114129
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`
