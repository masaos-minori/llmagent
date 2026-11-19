## Goal
Make the chunker's size-rule discard observable through a per-file structured log summary (discarded count, combined length, and reason) without changing which content is kept or discarded.

## Priority
Medium

## Scope
- **In-Scope**: Record and log a per-file discard summary in `chunk_english.py` and `chunk_splitter.py`; cover it with logger-capture unit tests in `test_chunk_splitter.py`; document the new record shape in the RAG logging reference and error-handling reference.
- **Out-of-Scope**: Changing the discard thresholds (`min_chunk`/`max_chunk`); changing English stopword behavior (issue `ragcrv002`); adding a quarantine directory for discarded sources; deciding whether a zero-chunk source is a run failure (needs confirmation with `ragcrv007`).
- **Dependencies**: Sibling issue `ragcrv003` removes the misconfiguration path that produces the most common zero-chunk case; this observability change is independent and can land first.
  - **Depends on**: N/A: no blocking ordering dependency

## Background
The chunker is the only pipeline stage that sees the crawled text. Every chunking path silently drops content that fails a size rule, and the run reports only the number of chunks written. An operator therefore cannot tell "the source produced nothing" from "the source was discarded", and corpus completeness can only be checked by re-running the splitter manually and comparing files.

## Problem
- `ChunkEnglishMixin._chunk_english` discards every merged chunk shorter than `min_chunk` after stopword filtering (`scripts/rag/ingestion/chunk_english.py`, measured on the post-filter length).
- `ChunkSplitter._chunk_markdown_by_heading` skips empty sections and sections shorter than `min_chunk`, and logs nothing (`scripts/rag/ingestion/chunk_splitter.py`).
- `ChunkSplitter._chunk_code` delegates to `chunk_utils.merge_text_items`, which drops a short block only when it cannot be merged into anything else.
- Reproduced at head `6bdced7bb` with `min_chunk=40`, `max_chunk=120`: a two-heading Markdown document produced 0 chunks and a code block shorter than `min_chunk` produced 0 chunks; in both cases the only log line was INFO `chunked 0 chunks from x.json`.

## Reason for Change
The chunker is the only stage that sees the crawled text, so the discard decision must be observable at the point where it happens rather than inferred by re-running the splitter.

## Implementation Intent
Report the discard decision where it is made: a per-file summary of discarded items with the reason and their total size, using the structured fields the ingestion loggers already use (`url`, `source_type`, `stage_name`). Keep the discard behavior unchanged; only its observability changes.

## Requirements
- `REQ-001`: For each source file, record the count and combined length of items discarded by a size rule.
- `REQ-002`: Log the summary at WARNING when a source yields zero chunks, and at INFO when it yields chunks but also discards some.
- `REQ-003`: Include the rule that caused the discard (`below_min_chunk`) and the source identity in the structured fields.
- `REQ-004`: Keep log volume bounded to one summary per file, and never log document text content.
- `REQ-005`: Document the new log record shape in the logging reference and state in the error-handling reference that a size-rule discard is not an error.

## Implementation Target Files
**Freeze status**: Frozen. All five rows are `Verified` (Exists, Requires modification, concrete Repository Evidence, linked to a defined Requirement/Acceptance criterion); no file appears in both `Implementation Target Files` and `Reference Files`; no directory/glob/group/v-phrase rows. Validated against current repo state at plan generation.

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_english.py` | Modify | `_chunk_english` discards sub-`min_chunk` chunks silently (line 33-37); add discard count/length tracking | REQ-001, REQ-003; AC-001 | Confirmed by reading source in Step 2 | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | `_chunk_markdown_by_heading` (line 265-273) and `_chunk_code`/`merge_text_items` discard silently; `process_file` must aggregate and log the per-file summary | REQ-001, REQ-002, REQ-003; AC-001, AC-002 | Confirmed by reading source in Step 2 | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Capture the module logger and assert the structured discard fields for below-`min_chunk` English, Markdown, and short-code inputs | REQ-001, REQ-002, REQ-003; AC-001, AC-002, AC-003 | `_ListHandler` pattern confirmed in `tests/rag/ingestion/test_chunk_grouping.py` (Step 2) | new test methods | Verified |
| `docs/21_rag/rag_05_03-logging.md` | Modify | Document the new discard-summary log record and when it appears | REQ-005; AC-004 | Current table (line 18) documents only INFO chunk count / ERROR; no discard record | none | Verified |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify | State that a size-rule discard is not an error and how it is reported | REQ-005; AC-004 | ChunkSplitter table (line 34-38) lists errors only, no discard note | none | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Understand `merge_text_items` discard semantics (merges short tails; drops only when nothing to merge into) to measure code-path discard | `scripts/rag/ingestion/chunk_splitter.py` (REQ-001) |
| `scripts/rag/utils.py` | `LOG_KEY_SOURCE_TYPE` / `LOG_KEY_STAGE_NAME` constants used by the ingestion loggers | `scripts/rag/ingestion/chunk_splitter.py` (REQ-003) |
| `tests/rag/ingestion/test_chunk_grouping.py` | `_ListHandler` logger-capture pattern to reuse in the new tests | `tests/rag/ingestion/test_chunk_splitter.py` |
| `scripts/rag/ingestion/chunk_japanese.py` | Confirm the Japanese path is out of scope and its discard behavior is unchanged | `scripts/rag/ingestion/chunk_splitter.py` (REQ-004) |

## Acceptance Criteria
- `AC-001`: A source whose content is entirely below `min_chunk` produces a WARNING naming the file and the reason (`below_min_chunk`) (REQ-001, REQ-002, REQ-003).
- `AC-002`: A source with both kept and discarded content reports the discarded count and combined length at INFO (REQ-001, REQ-002).
- `AC-003`: Existing log-based and chunking tests stay green (REQ-004).
- `AC-004`: The logging reference documents the new record shape and the error-handling reference states a discard is not an error (REQ-005).

## Tests
- `T-001`: Capture the module logger (`_ListHandler`) and assert the structured fields for a below-`min_chunk` English document (REQ-001, REQ-003).
- `T-002`: Assert the same for a below-`min_chunk` Markdown document (REQ-001, REQ-003).
- `T-003`: Assert the same for a short code block (REQ-001, REQ-003).
- `T-004`: Assert a mixed (kept + discarded) source logs the discarded count and length at INFO (REQ-002).

## Documentation Impact
`docs/21_rag/rag_05_03-logging.md`: add the discard-summary record and when it appears (REQ-005). `docs/21_rag/rag_05_04-error-handling-reference.md`: state that a size-rule discard is not an error and how it is reported (REQ-005). Both are RAG-domain docs; run `uv run python tools/check_docs_consistency.py --domain rag` after editing.

## Assumptions
- The only size rule that discards is `below_min_chunk`; the `discard_reason` field is therefore always `below_min_chunk`.
- Combined length is measured on each discarded item's length (post-filter length for English, raw section length for Markdown, character difference for code).
- The code path (`merge_text_items`) merges short tails rather than discarding them, so its discard is measured by character difference (sum of input block lengths minus sum of output chunk lengths); the item count uses the number of input blocks that survive in no output chunk.
- The discard summary is additive to the existing INFO `chunked N chunks from X` line; that line is not removed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact per-item discard count for the code path after `merge_text_items` merges blocks | Merging makes block-level attribution ambiguous; no per-block discard signal exits `merge_text_items` | Design decision in the implementation phase: report character-difference length and a best-effort block count; accept an approximate count. Non-blocking because the acceptance criteria only require count + length, not exact block accounting | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_english.py` | Modify | Low | Low | N/A (git-fame not available; single-owner check not conclusive) | None |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Low | Medium (10 commits in last 60 days) | N/A (git-fame not available; single-owner check not conclusive) | None |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | Low | N/A | None |
| `docs/21_rag/rag_05_03-logging.md` | Modify | Low | Low | N/A | None |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify | Low | Low | N/A | None |

## Design
**Discard locations.** Discard happens in three places, two explicit and one implicit:
- `ChunkEnglishMixin._chunk_english` filters `raw_chunks` by `len(stripped) >= min_chunk` (line 33-37). The discarded set is exactly the dropped rows; count and length are computed directly.
- `ChunkSplitter._chunk_markdown_by_heading` appends a section only when `min_chunk <= len(section) <= md_snippet_max_chars` (line 265-273). Sections shorter than `min_chunk` are dropped; count and length are computed directly. Oversized sections fall back to the language chunker and are not discarded.
- `ChunkSplitter._chunk_code` → `chunk_utils.merge_text_items` merges a short tail into the last chunk when a prior chunk exists, and drops a short block only when it cannot be merged (empty result, or a buffer below `min_chunk` that the next oversized block cannot absorb). Per-block attribution is ambiguous, so the discard is measured by character difference.

**Summary aggregation.** `process_file` calls `_build_chunk_list`, which fans out to the text and code paths. The discard summary must be aggregated across both before logging. Two viable mechanisms: (a) each chunker returns `(items, discarded_count, discarded_chars)` and the tuple threads up through `_build_text_triples`/`_build_code_triples`/`_build_chunk_list`; (b) an instance accumulator reset at the start of `process_file` and appended by each chunker. Preserve all existing public and internal return signatures under either mechanism so existing callers and tests are not broken.

**Structured record shape.** One record per file, carrying the fields the ingestion loggers already use plus the discard fields:
- Context: `url`, `source_type="file"`, `stage_name="chunk"` (constants from `scripts/rag/utils.py`).
- Discard: `discard_reason="below_min_chunk"`, `discarded_count`, `discarded_chars`.
- Message carries the human-readable count/length; never the document text.

**Log level.** `process_file` logs WARNING when the written count is 0 (source yielded nothing) and INFO when the written count is > 0 but `discarded_count > 0`. No discard record when nothing was discarded.

**No blast radius beyond logging.** No schema, API, config, or public-interface change. `merge_text_items` behavior is unchanged; only its discard is measured, not its output.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands:

1. **Phase 1: Track discard in the English and Markdown paths**
   - [ ] In `scripts/rag/ingestion/chunk_english.py`, compute `discarded_count` and `discarded_chars` for the sub-`min_chunk` rows dropped in `_chunk_english` (REQ-001, REQ-003).
   - [ ] In `scripts/rag/ingestion/chunk_splitter.py`, compute `discarded_count`/`discarded_chars` for sub-`min_chunk` sections in `_chunk_markdown_by_heading` (REQ-001).
   - [ ] Thread the discard counts up through `_build_text_triples`/`_build_chunk_list` without changing existing return values consumed elsewhere (REQ-001).
2. **Phase 2: Measure code-path discard and aggregate per file**
   - [ ] In `scripts/rag/ingestion/chunk_splitter.py`, measure `_chunk_code` discard by character difference via `chunk_utils.merge_text_items` (do not change its output) (REQ-001).
   - [ ] Aggregate text + code discard into one per-file summary in `process_file` (REQ-001).
3. **Phase 3: Log the per-file summary**
   - [ ] Log WARNING (zero chunks) or INFO (kept + discarded) with `discard_reason`, `discarded_count`, `discarded_chars`, `url`, `source_type`, `stage_name` in `scripts/rag/ingestion/chunk_splitter.py` (REQ-002, REQ-003).
   - [ ] Enforce one summary per file; never log content (REQ-004).
4. **Phase 4: Add logger-capture unit tests**
   - [ ] Add `_ListHandler`-based tests for below-`min_chunk` English, Markdown, and short-code inputs, and a mixed kept+discarded case in `tests/rag/ingestion/test_chunk_splitter.py` (REQ-001, REQ-002, AC-001, AC-002).
5. **Phase 5: Update documentation**
   - [ ] Document the discard-summary record and its trigger in `docs/21_rag/rag_05_03-logging.md` (REQ-005).
   - [ ] State in `docs/21_rag/rag_05_04-error-handling-reference.md` that a size-rule discard is not an error and how it is reported (REQ-005).
6. **Phase 6: Validation**
   - [ ] Run ruff format/check, mypy, bandit, and the RAG test suite; raise diff-cover to the threshold in `rules/toolchain.md` (REQ-003, AC-003).

### Release units
N/A: every phase is independently validatable; the change is observability-only and breaks no existing caller.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py` | Static | `uv run ruff format --check` && `uv run ruff check` | Clean |
| `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py` | Type | `uv run mypy scripts/rag/ingestion/chunk_english.py scripts/rag/ingestion/chunk_splitter.py` | Pass |
| `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py` | Security | `uv run bandit scripts/rag/ingestion/chunk_english.py scripts/rag/ingestion/chunk_splitter.py` | No new findings |
| `tests/rag/ingestion/test_chunk_splitter.py` | Unit | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | New + existing tests pass |
| Whole RAG ingestion suite | Regression | `uv run pytest tests/rag/` | Green |
| Coverage | Coverage gate | `uv run ... diff-cover` (per `rules/toolchain.md` §7) | At or above threshold |

## Risks
- **Risk**: Changing the return signature of `_chunk_english`/`_chunk_markdown_by_heading`/`_chunk_code` breaks existing callers or tests → **Mitigation**: carry discard counts via a separate return value or an instance accumulator; preserve every existing return value currently consumed.
- **Risk**: Code-path discard count is imprecise after merging → **Mitigation**: measure by character difference and accept an approximate count; documented in UNK-01.
- **Risk**: Log volume grows unbounded → **Mitigation**: emit exactly one summary per file, never per discarded item.
- **Risk**: Accidentally logging document text → **Mitigation**: the record carries only count, length, and reason, never content.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Track discard in English and Markdown paths | In Progress | — | — | Touches `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py` |
| 2 | Measure code-path discard and aggregate per file | In Progress | — | — | Touches `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_utils.py` (read) |
| 3 | Log the per-file discard summary | In Progress | — | — | Touches `scripts/rag/ingestion/chunk_splitter.py` |
| 4 | Add logger-capture unit tests | In Progress | — | — | Touches `tests/rag/ingestion/test_chunk_splitter.py` |
| 5 | Update documentation | In Progress | — | — | Touches `docs/21_rag/rag_05_03-logging.md`, `docs/21_rag/rag_05_04-error-handling-reference.md` |
| 6 | Validation | Pending | — | — | ruff/mypy/bandit/pytest/diff-cover |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-170454_01_scripts_rag_ingestion_chunk_english_py.md | 1 | Procedure | Pending | — | — |
| implementations/20261119-170454_02_scripts_rag_ingestion_chunk_splitter_py.md | 1, 2, 3 | Procedure | Pending | — | — |
| implementations/20261119-170454_03_tests_rag_ingestion_test_chunk_splitter_py.md | 4 | Procedure | Pending | — | — |
| implementations/20261119-170454_04_docs_21_rag_rag_05_03_logging_md.md | 5 | Procedure | Pending | — | — |
| implementations/20261119-170454_05_docs_21_rag_rag_05_04_error_handling_reference_md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-164553
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_05_03-logging.md`, `docs/21_rag/rag_05_04-error-handling-reference.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.