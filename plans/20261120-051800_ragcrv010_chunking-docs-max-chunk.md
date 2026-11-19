## Goal
- Correct the one remaining inaccuracy in `rag_02_03` left after the size-rule fixes landed: the doc currently asserts that the English (and Markdown-heading) chunking paths use `chunk_utils._split_overlong`, but production keeps any single sentence longer than `max_chunk` whole via `_split_sentences_en` and never calls `_split_overlong` on the English path. This Plan makes the English per-path size rules match the code, removes the false `_split_overlong` attribution, and confirms the other three items F-010 asked for are already correctly documented.

## Priority
Medium

## Scope
- **In-Scope**:
  - Correct `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` so the English text path's size rules are described accurately: paragraphs accumulate into `<= max_chunk` chunks, oversized paragraphs are split at sentence boundaries via `_split_sentences_en`, and a single sentence longer than `max_chunk` is kept whole (not segmented by `_split_overlong`).
  - Remove/correct the assertion in section 3.1.4 that the English and Markdown-heading paths use `chunk_utils._split_overlong`; keep the correct Japanese `_split_overlong` statement intact.
  - Re-confirm against current source that the other three F-010 items are already accurate and leave them unchanged: English `content`/`normalized_content` (Shape B), the `chunk_overlap` upper bound, and the tuning-constants `Needs Confirmation` / "no rationale" wording.
- **Out-of-Scope**:
  - Any change to production chunking behavior, config values, or the `ChunkSplitter` constructor.
  - Re-opening the tuning-constants rationale decision (`nc034`) or rewriting its `NC-034` / "no measured rationale" wording.
  - Editing `rag_05_01-configuration-reference.md` — its `chunk_overlap < max_chunk` statement is already correct.
  - Re-documenting the Japanese path (already accurate).
- **Dependencies**: The Issue depends on `ragcrv001`/`ragcrv002`/`ragcrv003` for the post-fix behavior being documented. Those three are already implemented and archived in `issues/done/`, and their behavior is now reflected in the doc except for the English `_split_overlong` misattribution, so nothing here waits on them.
  - **Depends on**: `N/A: none`

## Background
- `issue-to-plan` finding F-010 (`ragcrv010`) reported that `rag_02_03` described one uniform `max_chunk` guarantee while the Japanese and English paths keep oversized sentences whole, and that neither the `chunk_overlap` upper bound nor what English `content` contains was documented.
- The three dependency fixes landed and updated the doc: `ragcrv001` documents the Japanese oversized-sentence rule (`cb1ae9a29`), `ragcrv002` documents English `content` = unfiltered original text (Shape B, `634cabf1e`), and `ragcrv003`'s `chunk_overlap < max_chunk` validation is recorded in `rag_05_01`.
- Adversarial re-read of the current doc plus `scripts/rag/ingestion/chunk_english.py` and `chunk_utils.py` shows the English per-path size rule is still misdocumented: section 3.1.4 states the English and Markdown-heading paths use `chunk_utils._split_overlong`, which is false.

## Problem
Readers cannot trust the English size rule in `rag_02_03`: section 3.1.4 says oversized English text is segmented by the shared character-level greedy `_split_overlong`, but production `_split_sentences_en` keeps any single sentence longer than `max_chunk` whole and never calls `_split_overlong`. This contradicts both the code and F-010's own summary ("the English paths keep oversized sentences whole"), so the per-path statement does not match the implementation.

## Reason for Change
A documentation inaccuracy that overstates a `max_chunk` guarantee is exactly the class of defect F-010 exists to close; leaving the false `_split_overlong` attribution hides the real English behavior and defeats the Issue's acceptance criterion that per-path statements match the current implementation for English.

## Implementation Intent
Re-read the English path in `chunk_english.py` and confirm the exact accumulation/oversized-sentence behavior, then correct only section 3.1.4's English (and Markdown-heading) size-rule description and remove the false `_split_overlong` attribution while preserving the correct Japanese statement. No other section changes unless a fresh re-read finds a new inaccuracy; the already-correct English `content`/`normalized_content`, `chunk_overlap` bound, and `NC-034` wording are left untouched.

## Requirements
- `REQ-001`: `rag_02_03` section 3.1.4 describes the English text path's size rules accurately — paragraph accumulation into `<= max_chunk` chunks, oversized paragraphs split at sentence boundaries via `_split_sentences_en`, and a single sentence longer than `max_chunk` kept whole — matching `chunk_english.py::_split_sentences_en`.
- `REQ-002`: `rag_02_03` no longer asserts that the English or Markdown-heading paths use `chunk_utils._split_overlong`; the correct Japanese `_split_overlong` statement is preserved.
- `REQ-003`: The already-correct English `content`/`normalized_content` (Shape B), the `chunk_overlap < max_chunk` bound (in `rag_05_01`), and the tuning-constants `NC-034` / "no measured rationale" wording are left unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Correct section 3.1.4's English/Markdown-heading size-rule description to match `chunk_english.py` (keep oversized sentences whole, do not use `_split_overlong`) and remove the false `_split_overlong` attribution while preserving the correct Japanese statement. | REQ-001, REQ-002 | `chunk_english.py::_split_sentences_en` (line 106 docstring "Oversized sentences are kept as-is"; body starts a fresh buffer with an oversized sentence instead of calling `_split_overlong`); `_split_overlong` callers are only `chunk_japanese.py:130` and `chunk_utils.py:124` (JP path) — never the English path; current doc line 59 claims EN/heading use `_split_overlong` | F-010 summary ("the English paths keep oversized sentences whole"); manual cross-read of the four paths | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_english.py` | Confirm the exact English accumulation and oversized-sentence behavior before correcting `rag_02_03` so the doc matches production, not the Issue's original assumption | REQ-001 |
| `scripts/rag/ingestion/chunk_utils.py` | Confirm `_split_overlong` is called only from the Japanese path (`accumulate_items` / `chunk_japanese`) and never from the English path, so the doc's false attribution can be removed precisely | REQ-002 |
| `scripts/rag/ingestion/chunk_japanese.py` | Confirm the Japanese oversized-sentence rule that the doc already documents correctly, so it is preserved verbatim rather than rewritten | REQ-002 |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Confirm the `chunk_overlap < max_chunk` bound is already stated there so this Plan does not duplicate or re-edit it | REQ-003 |

## Acceptance Criteria
- `rag_02_03` section 3.1.4 states that a single English sentence longer than `max_chunk` is kept whole and that the English path does not use `chunk_utils._split_overlong` — REQ-001, REQ-002, AC-001.
- The correct Japanese `_split_overlong` statement in section 3.1.4 is preserved unchanged — REQ-002, AC-002.
- The English `content`/`normalized_content` (Shape B) statement, the `chunk_overlap < max_chunk` bound in `rag_05_01`, and the tuning-constants `NC-034` / "no measured rationale" wording are unchanged — REQ-003, AC-003.
- Every per-path size statement in the doc matches the current implementation for Japanese, English, Markdown, and code paths — AC-004.

## Tests
- No code test required; behavior is unchanged (F-010 is a documentation-only Issue).
- Manual cross-read of the four chunking paths against `chunk_english.py`, `chunk_japanese.py`, and `chunk_utils.py` confirms every per-path size statement is accurate — REQ-001, REQ-002, AC-004.
- Run the applicable documentation consistency checker listed in `routing.md` and confirm it passes — AC-004.

## Documentation Impact
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` MUST be updated: correct the English/Markdown-heading size-rule description in section 3.1.4 and remove the false `_split_overlong` attribution. This maps to the chunksplitter doc in `docs/00_index.md`'s Document References by Task table. `rag_05_01-configuration-reference.md` needs no change (its `chunk_overlap` bound is already correct).

## Assumptions
- The only remaining inaccuracy from F-010 is the English `_split_overlong` misattribution in section 3.1.4; the other three items (English `content`/`normalized_content`, `chunk_overlap` bound, tuning-constants wording) are already correct and need no change.
- The Markdown-heading path delegates to `_chunk_japanese` (ja) or `_chunk_english` (non-ja), so its size rule follows whichever language mixin it routes to; the doc should not claim a separate heading-level `_split_overlong`.
- Correcting the doc does not require touching `rag_05_01`; its `chunk_overlap < max_chunk` statement already satisfies F-010.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the Markdown-heading path ever calls `_split_overlong` directly (independent of the language mixin) before editing. Resolution: confirm via the heading fallback in `chunk_splitter.py` that heading sections route through `_chunk_japanese`/`_chunk_english` and never call `_split_overlong` directly. | None blocking: the heading fallback delegates to the language mixins today. | Decide during implementation; recommend removing the heading-level `_split_overlong` mention. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Documentation-only; corrects one misattributed size-rule statement. No runtime impact. | Low | High | not applicable (rsynced) |

## Design
- Section 3.1.4 currently has a Japanese-focused paragraph that (a) correctly states a Japanese sentence longer than `max_chunk` is segmented by `chunk_utils._split_overlong`, and (b) incorrectly adds that "the same character-level greedy fill the English and heading paths use". Production shows the English text path accumulates paragraphs into `<= max_chunk` chunks and, for an oversized paragraph, splits at sentence boundaries via `_split_sentences_en`, keeping any single sentence longer than `max_chunk` whole — it never calls `_split_overlong`. `_split_overlong` is called only from the Japanese path (`chunk_japanese.py:130` and `chunk_utils.py:124`).
- The correction rewrites only the English/Markdown-heading size-rule sentence(s) to describe this accurately (accumulate → split oversized paragraphs at sentence boundaries → keep oversized sentences whole), removes the false `_split_overlong` attribution for EN/heading, and leaves the correct Japanese `_split_overlong` statement intact. No other section is edited unless a fresh re-read surfaces a new inaccuracy.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Preparation / Refactoring**
   - [ ] Re-read `chunk_english.py::_split_sentences_en`, `chunk_utils.py::_split_overlong` callers, and the Markdown-heading fallback in `chunk_splitter.py` to lock the exact English/heading size rule and resolve UNK-01 — REQ-001, REQ-002, `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_utils.py`.
2. **Phase 2: Core Logic Implementation**
   - [ ] Correct `rag_02_03` section 3.1.4's English/Markdown-heading size-rule description to match production (accumulate -> split oversized paragraphs at sentence boundaries -> keep oversized sentences whole) and remove the false `_split_overlong` attribution for EN/heading while preserving the correct Japanese statement — REQ-001, REQ-002, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`.
3. **Phase 3: Deployment & Verification**
   - [ ] Manual cross-read of all four chunking paths against the source to confirm every per-path size statement is accurate; run the applicable documentation consistency checker from `routing.md` and confirm it passes; confirm the English `content`/`normalized_content`, `chunk_overlap` bound in `rag_05_01`, and `NC-034` wording are unchanged — REQ-001, REQ-002, REQ-003, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`.

### Release units
N/A: every phase passes validation alone; the doc correction is independently runnable and readable.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Static: section 3.1.4's English/heading size rule matches `chunk_english.py`; no `_split_overlong` attribution for EN/heading; JP statement preserved | manual cross-read vs `chunk_english.py::_split_sentences_en`, `chunk_utils.py::_split_overlong` callers | Doc matches production |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Static: English `content`/`normalized_content`, `chunk_overlap` bound in `rag_05_01`, `NC-034` wording unchanged | `rg -n "Shape B|chunk_overlap < max_chunk|NC-034"` before/after diff | No unintended edits |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Checker: applicable documentation consistency checker passes | `uv run python tools/<doc-checker>` per `routing.md` | Passes |

## Risks
- **Risk**: Rewriting the English size-rule sentence accidentally alters or drops the correct Japanese `_split_overlong` statement that sits in the same paragraph. → **Mitigation**: edit only the English/heading sentence(s); diff-review that the Japanese `_split_overlong` clause is byte-for-byte preserved.
- **Risk**: Over-correcting beyond F-010's scope by re-editing the already-correct English `content`/`normalized_content`, `chunk_overlap` bound, or `NC-034` wording. → **Mitigation**: scope the edit to section 3.1.4's size-rule description only; verify with a before/after `rg` diff that the protected statements are untouched.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: lock English/heading size rule from source; resolve UNK-01 | Pending | — | — | |
| 2 | Phase 2: correct `rag_02_03` section 3.1.4 English/heading size rule; remove false `_split_overlong` attribution | Pending | — | — | |
| 3 | Phase 3: cross-read four paths; run doc checker; confirm protected statements unchanged | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

Type options: Test / Task / Phase / Doc / Config / Infra / Other

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112022_ragcrv010_chunking-docs-max-chunk.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-051800
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
