# Fix AttributeError and chunk loss in Japanese sentence merging

## Goal
- Make `ChunkSplitter` chunk Japanese documents longer than `max_chunk` reliably: `_merge_ja_sentence_pairs` and its buffer helpers share one result accumulator so every emitted chunk is returned and no `AttributeError` is raised.

## Priority
High

## Scope
- **In-Scope**: accumulator state in `_merge_ja_sentence_pairs`, `_emit_and_start_new`, `_merge_tail_into_last`; removal of test fixture compensation; regression and end-to-end tests.
- **Out-of-Scope**: English and Markdown chunking paths; overlap length tuning or config changes; Sudachi tokenizer behavior.
- **Dependencies**: N/A: none

## Background
Commit 37f020f39 ("refactor(chunk_japanese): extract buffer management helpers") moved the intermediate `result.append(...)` calls into the extracted helpers as `self._result.append(...)` while `_merge_ja_sentence_pairs` kept a local `result` list and returns it. `_result` is only a bare class annotation on `ChunkJapaneseMixin`; no production code assigns it. Verified in this cycle: `ChunkSplitter.process_file` on a 1400-char Japanese payload with `max_chunk = 1000` raises `AttributeError: 'ChunkSplitter' object has no attribute '_result'`; `ChunkSplitter.process_all` catches only `(OSError, RuntimeError, ValueError)`, so the exception aborts the whole chunk stage.

## Problem
Any Japanese document longer than the configured `max_chunk` crashes the chunk stage. With the test-style compensation (`chunker._result = []` pre-initialization), the same payload writes 1 chunk of 456 of 1300 content characters — emitted chunks stay in `self._result` and are discarded, silently losing content from the RAG index.

## Reason for Change
Normal production Japanese documents exceed `max_chunk`, so the crash hits the normal crawl path, not an edge case; a compensation-only patch would silently corrupt the index.

## Implementation Intent
Restore a single source of truth for the chunk accumulator inside `_merge_ja_sentence_pairs`: pass a caller-owned result list into the helpers that currently append to `self._result`, and delete the never-initialized `_result` annotation. Preserve `_chunk_japanese` public behavior: same overlap semantics, same min/max constraints, same `normalized_content` handling (empty normalized maps to None).

## Requirements
- `REQ-001`: `_merge_ja_sentence_pairs` and its emit/tail-merge helpers operate on one accumulator owned by the merge method; every emitted chunk (overlap-carrying emits and the merged short tail) is returned in order; no uninitialized instance state.
- `REQ-002`: Remove the test-fixture compensation (`mixin._result` in `_make_ja_mixin`, `chunker._result = []` in `test_process_file_end_to_end_japanese`) and strengthen the end-to-end assertions so silently dropped chunks fail the test.
- `REQ-003`: Regression tests drive `_merge_ja_sentence_pairs` with multi-emit input (overlap > 0 and overlap == 0, plus a short-tail merge) and an end-to-end `ChunkSplitter.process_file` test with Japanese text longer than `max_chunk` and no compensation.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-093438 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Unify the local `result` and `self._result` state in `_merge_ja_sentence_pairs`, `_emit_and_start_new`, `_merge_tail_into_last`; remove the uninitialized `_result` annotation | REQ-001; AC-1, AC-2 | `_emit_and_start_new` and `_merge_tail_into_last` append to `self._result` while `_merge_ja_sentence_pairs` returns the local `result`; `rg '_result' scripts/rag/ingestion` finds only the annotation (checked in Step 2); `AttributeError` reproduced via `ChunkSplitter.process_file` | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Remove `_result` compensation in `_make_ja_mixin` and `test_process_file_end_to_end_japanese`; add multi-emit `_merge_ja_sentence_pairs` regression tests; strengthen the Japanese end-to-end assertions | REQ-002, REQ-003; AC-3 | `_make_ja_mixin` assigns `mixin._result`; `test_process_file_end_to_end_japanese` pre-initializes `chunker._result = []` and passes while losing content — reproduced: 1 chunk, 456 of 1300 chars written (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Sole production importer of `ChunkJapaneseMixin`; `_build_text_triples` dispatches `lang == "ja"` to `_chunk_japanese`; `process_all`'s except tuple shows `AttributeError` is uncaught | REQ-001 target `scripts/rag/ingestion/chunk_japanese.py` |
| `scripts/rag/ingestion/chunk_utils.py` | `start_next_buf` overlap helper called by `_emit_and_start_new`; its semantics must be preserved unchanged | REQ-001 |
| `config/chunk_splitter.toml` | Holds the production `min_chunk`/`max_chunk`/`chunk_overlap` values that bound the affected path; read-only | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): `_merge_ja_sentence_pairs` returns every emitted chunk in order, including overlap-carrying emits and the merged short tail (covered by a test).
- AC-2 (REQ-001): A Japanese document longer than `max_chunk` chunks successfully via `ChunkSplitter.process_file` without `AttributeError`, with no compensation in the test (covered by a test).
- AC-3 (REQ-002): No test pre-initializes internal state that production does not initialize; the end-to-end assertions fail if any chunk is dropped.
- AC-4 (REQ-001..003): `uv run pytest tests/rag/ingestion` passes and changed lines reach the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-003: unit regression test through `_merge_ja_sentence_pairs` with multi-emit input (overlap > 0 and overlap == 0 cases, plus a short-tail merge), asserting all emitted chunks are returned in order.
- REQ-003: end-to-end `ChunkSplitter.process_file` test with Japanese text longer than `max_chunk`, no compensation, asserting the reassembled chunk content covers the source content.
- REQ-002: existing `TestJapaneseChunkOverlap` characterization tests keep their assertions after the helper-signature update.

## Documentation Impact
N/A: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` already describes the intended Japanese chunking behavior (Sudachi pairs, `normalized_content`); the fix restores code to the documented behavior, so no doc change is required.

## Assumptions
- The tail-merge semantics for multi-emit input are the ones the current `_merge_tail_into_last` implements (short tail merged into the last emitted chunk); the fix preserves them.
- Changing `_emit_and_start_new` and `_merge_tail_into_last` to take the accumulator as a parameter is internal-only: the only importers of `ChunkJapaneseMixin` are `scripts/rag/ingestion/chunk_splitter.py` and `tests/rag/ingestion/test_chunk_splitter.py` (checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the production RAG DB holds Japanese documents partially chunked during the crash window (37f020f39 onward) | Live RAG DB inspection, out of reach for this planning phase | Post-fix operational check: force re-chunk/re-ingest affected Japanese sources and compare chunk counts | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Decision: caller-owned accumulator — `_merge_ja_sentence_pairs` owns the local result list and passes it to `_emit_and_start_new` and `_merge_tail_into_last`; the `_result` class annotation is deleted. Rejected alternative (initialize `self._result` at merge start): keeps cross-method instance state that leaks across `process_file` calls — the reproduction shows `self._result` still holding the previous document's chunk after a run.
- `scan_change_consumers.py` not run: this changes no persisted schema, public API, or shared constant; Step 3's import scan enumerated every consumer (`chunk_splitter.py`, `test_chunk_splitter.py`).
- Validation quality baseline (Step 5): `radon cc scripts/rag/ingestion/chunk_japanese.py -s` — highest grade B (10) for `_merge_ja_sentence_pairs`, no C or worse; `vulture scripts/ --min-confidence 80` — no findings in the target files (pre-existing findings elsewhere are out of scope); `bandit -r scripts/ -c pyproject.toml` — 0 medium/high findings. Diff-cover current number not measured in this cycle (no code change yet); the Plan's validation requires ≥ 90% on changed lines at implementation per `rules/toolchain.md` Completion checklist.

## Implementation steps
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Add `_merge_ja_sentence_pairs` multi-emit regression tests (overlap > 0, overlap == 0, short-tail merge) and a compensation-free Japanese `process_file` end-to-end test (REQ-003; `tests/rag/ingestion/test_chunk_splitter.py`)
2. **Phase 2: Single-accumulator fix and compensation removal (GREEN)**
   - [ ] Refactor the accumulator handling so helpers operate on the merge method's result list; delete the `_result` annotation (REQ-001; `scripts/rag/ingestion/chunk_japanese.py`) — minimal change only: do not rewrite the English mixin or the splitter I/O layer; keep the mixin attribute-declaration pattern for type checkers for the remaining buffer attributes
   - [ ] Remove `_result` compensation from `_make_ja_mixin` and `test_process_file_end_to_end_japanese`; strengthen the end-to-end content-coverage assertions (REQ-002; `tests/rag/ingestion/test_chunk_splitter.py`)
3. **Phase 3: Verification & deploy hand-off**
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted + `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%) (REQ-001..003; `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via `skills/deploy/SKILL.md` is the user's decision (approval gate) (REQ-001)

### Release units
**Unit**: ja-chunk-fix | **Phases**: 1, 2 | **Reason**: Phase 1 adds failing regression tests; the suite is green only after Phase 2's production fix, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Unit + end-to-end | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | New regression and end-to-end tests pass; previously crash/loss behavior now returns all chunks |
| `scripts/rag/ingestion/chunk_japanese.py` | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| `tests/rag/ingestion/test_chunk_splitter.py` | Regression suite | `uv run pytest tests/rag/ingestion` | All ingestion tests pass with no `_result` compensation anywhere |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: changing helper signatures alters overlap semantics → **Mitigation**: `TestJapaneseChunkOverlap` characterization tests call these helpers directly; keep their assertions identical while updating call sites in the tests.
- **Risk**: removing compensation hides a remaining hidden initialization dependency → **Mitigation**: Phase 1 end-to-end test exercises the production class with no compensation before the fix exists (it must fail first, then pass).
- **Risk**: production data already chunked by the defective path keeps lost chunks → **Mitigation**: UNK-01 resolution path — force re-chunk/re-ingest Japanese sources after the fix ships.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add failing regression + end-to-end tests in `tests/rag/ingestion/test_chunk_splitter.py` | Completed | 2026-11-06 | 2026-11-06 | REQ-003 3 regression tests added (RED confirmed pre-fix) + e2e assertions strengthened |
| 2 | Single-accumulator fix in `scripts/rag/ingestion/chunk_japanese.py`; remove test compensation | Completed | 2026-11-06 | 2026-11-06 | REQ-001, REQ-002 single-accumulator fix applied; test compensation removed |
| 3 | Gate sequence + deploy hand-off | Completed | 2026-11-06 | 2026-11-06 | REQ-001..003 gate sequence passed 2026-11-06; deploy hand-off (UNK-01 re-chunk) remains an operational decision for the owner |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-114129_01_scripts_rag_ingestion_chunk_japanese.py.md` | 1, 2 | Procedure | Completed | 2026-11-06 | 2026-11-06 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging001_japanese-chunk-merge-crash.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-093438
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem/Implementation Intent; `AttributeError` reproduction and `self._result` usage (checked in Step 2) | `scripts/rag/ingestion/chunk_japanese.py` | Phase 2 | AC-1, AC-2 | Phase 1 regression + end-to-end tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes; `_make_ja_mixin` and e2e compensation found and reproduction showed masked chunk loss (checked in Step 2) | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 2 | AC-3 | `uv run pytest tests/rag/ingestion` | Confirmed by repository evidence |
| REQ-003 | Issue Testing Expectations | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-2, AC-4 | New regression + end-to-end tests | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-114129 -->