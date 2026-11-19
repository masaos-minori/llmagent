## Goal

Correct the one remaining inaccuracy in `rag_02_03` left after the size-rule fixes
landed: section 3.1.4 currently asserts, via a parenthetical, that the English and
Markdown-heading chunking paths share `chunk_utils._split_overlong`, but production
keeps any single sentence longer than `max_chunk` whole via
`chunk_english.py::_split_sentences_en` and never calls `_split_overlong` on the
English path. This procedure removes that false `_split_overlong` attribution for
the English and heading paths while preserving the correct Japanese
`_split_overlong` statement, so the per-path size rules match the current
implementation (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The only remaining inaccuracy from F-010 is the English/heading `_split_overlong`
  misattribution in section 3.1.4; the English `content`/`normalized_content`
  (Shape B, line 72), the `chunk_overlap < max_chunk` bound in `rag_05_01`, and the
  tuning-constants `NC-034` / "no measured rationale" wording (rag_05_01 line 45) are
  already correct and MUST be left unchanged (REQ-003).
- The false attribution is a single parenthetical inside the one long
  "**Japanese oversized-sentence rule and non-empty content.**" paragraph on line 59:
  "...by the shared `chunk_utils._split_overlong` rule **(the same character-level
  greedy fill the English and heading paths use)**", whatever the state of the
  running buffer... Removing only that parenthetical leaves the Japanese
  `_split_overlong` statement byte-for-byte intact and the sentence grammatical.
- `_split_overlong` is called only from the Japanese path today:
  `chunk_japanese.py:130` (`_split_overlong(item[0], " ", self._settings.max_chunk)`)
  and `chunk_utils.py:124` (`accumulate_items`). The English text path
  (`chunk_english.py::_split_sentences_en`, line 105-120, docstring line 106
  "Oversized sentences are kept as-is") splits at sentence boundaries and keeps an
  oversized sentence whole; it never calls `_split_overlong`.
- **Overlap (ragcrv009 ↔ ragcrv010)**: `ragcrv009` also edits
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, but the "**Undersized**"
  row on line 53 (recording the below-`min_chunk` discard warning), not line 59. The
  two edits are on different lines and address different concerns (discard-warning vs.
  oversized-sentence splitting); they are compatible and may be applied in either
  order. This procedure scopes its edit to the line-59 parenthetical only and does not
  touch line 53 or the Japanese `_split_overlong` statement.
- The Markdown-heading "Oversized" bullet (line ~55) already correctly states that an
  oversized heading section is split by `_chunk_japanese` (ja) or `_chunk_english`
  (non-ja); it does not mention `_split_overlong` and is left unchanged. The
  Markdown-heading fallback routes through those language mixins
  (`scripts/rag/ingestion/chunk_splitter.py::_chunk_markdown_by_heading`, lines
  367-398), never calling `_split_overlong` directly — this resolves UNK-01.

## Design decisions
- Make the smallest correct edit: delete only the false parenthetical
  "(the same character-level greedy fill the English and heading paths use)" from line
  59, leaving the Japanese `_split_overlong` clause and the rest of the paragraph
  untouched. This removes the misattribution without rewriting a paragraph that is
  otherwise accurate.
- Do NOT add a positive claim that the English/heading paths use some other named
  function in that exact spot; the English per-path size rule is described elsewhere
  (section 3.2 English-text row and the "Oversized" heading bullet), and re-stating it
  here risks duplicating or contradicting those statements. The Plan's REQ-001 is
  satisfied by making the per-path statement accurate (i.e. no longer claiming EN/heading
  use `_split_overlong`), not by adding new EN detail to this paragraph.

## Alternatives considered
- Rewriting the whole "Japanese oversized-sentence rule" paragraph to add explicit
  English behavior: rejected — over-scopes the edit beyond F-010, risks duplicating the
  section 3.2 English row and the "Oversized" heading bullet, and endangers the
  correct Japanese statement this Plan must preserve.
- Renaming/relocating `_split_overlong`: out of scope — this is a documentation-only
  Issue; production code is unchanged.

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Open `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` and locate
   section 3.1.4 ("Markdown Heading Chunking Behavior"), specifically the
   "**Japanese oversized-sentence rule and non-empty content.**" paragraph on line 59.
2. Edit the false attribution on line 59: delete the parenthetical
   `(the same character-level greedy fill the English and heading paths use)` that
   follows "by the shared `chunk_utils._split_overlong` rule". The paragraph then reads
   "...segmented into pieces each within `max_chunk` by the shared
   `chunk_utils._split_overlong` rule, whatever the state of the running buffer;..."
   — the Japanese `_split_overlong` statement is preserved and the sentence remains
   grammatical.
3. Confirm no other sentence in the doc attributes `_split_overlong` to the English or
   Markdown-heading paths. The only other `_split_overlong` mention is the (now
   corrected) Japanese statement; the Markdown-heading "Oversized" bullet refers to
   `_chunk_japanese`/`_chunk_english`, not `_split_overlong`.
4. Diff-review that the protected statements are untouched: English `content`/
   `normalized_content` (Shape B, line 72), and — outside this file — the
   `chunk_overlap < max_chunk` bound and `NC-034` / "no measured rationale" wording in
   `rag_05_01` (line 45).

### Method
Edit the single parenthetical on line 59; verify by diff that (a) the Japanese
`_split_overlong` clause is byte-for-byte preserved, (b) no EN/heading `_split_overlong`
attribution remains, and (c) line 72 and rag_05_01 line 45 are unchanged. Cross-read the
four chunking paths against `chunk_english.py::_split_sentences_en` (lines 105-120),
`chunk_japanese.py` (`_split_overlong` caller at line 130) and `chunk_utils.py`
(`_split_overlong` caller at line 124) before finalizing.

### Details
F-010 reported that `rag_02_03` described one uniform `max_chunk` guarantee while the
Japanese and English paths keep oversized sentences whole. The three dependency fixes
(`ragcrv001` JP rule, `ragcrv002` English `content` Shape B, `ragcrv003`
`chunk_overlap < max_chunk` in `rag_05_01`) landed and updated the doc, but section
3.1.4 still carried the parenthetical tying the English and heading paths to the shared
character-level greedy `_split_overlong` rule. Production contradicts this:
`chunk_english.py::_split_sentences_en` (line 106 docstring: "Oversized sentences are
kept as-is") accumulates paragraphs into `<= max_chunk` chunks and keeps any single
sentence longer than `max_chunk` whole, never calling `_split_overlong`; `_split_overlong`
is invoked only from the Japanese path (`chunk_japanese.py:130`, `chunk_utils.py:124`).
The edit removes exactly that false attribution and preserves the correct Japanese
statement.

## Compatibility considerations
Documentation-only; no runtime impact. The edit must not alter the correct Japanese
`_split_overlong` statement (same section 3.1.4) nor the `chunk_overlap` bound
documented in `rag_05_01`. It is compatible with `ragcrv009`'s concurrent edit of the
line-53 "Undersized" row in the same file.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: section 3.1.4 no longer asserts that the English or Markdown-heading paths
  use `chunk_utils._split_overlong`; the Japanese `_split_overlong` statement is
  preserved; the English per-path size rule matches `chunk_english.py::_split_sentences_en`.
- Before/after `rg` diff confirms the protected statements are unchanged:
  `rg -n "Shape B"` in `rag_02_03` (line 72) and
  `rg -n "chunk_overlap < max_chunk|NC-034|no measured rationale"` in
  `rag_05_01` (line 45) are identical before and after.
- Manual cross-read of all four chunking paths against `chunk_english.py`,
  `chunk_japanese.py`, and `chunk_utils.py` confirms every per-path size statement is
  accurate.
- Run the applicable documentation consistency checker listed in `routing.md` and
  confirm it passes.

## Completion criteria
Section 3.1.4 states that a single English sentence longer than `max_chunk` is kept
whole and that the English and Markdown-heading paths do not use
`chunk_utils._split_overlong`; the correct Japanese `_split_overlong` statement is
preserved; and the English `content`/`normalized_content` (Shape B), the
`chunk_overlap < max_chunk` bound in `rag_05_01`, and the `NC-034` wording are unchanged.

## Out of Scope
Editing production chunking behavior, config values, or the `ChunkSplitter`
constructor; re-opening the tuning-constants rationale decision (`nc034`) or rewriting
its `NC-034` / "no measured rationale" wording; editing `rag_05_01-configuration-reference.md`;
re-documenting the Japanese path; or any section other than the line-59 parenthetical.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261119-112022_ragcrv010_chunking-docs-max-chunk.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-051800_ragcrv010_chunking-docs-max-chunk.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-073426
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
