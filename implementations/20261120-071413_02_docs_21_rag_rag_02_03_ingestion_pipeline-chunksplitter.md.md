## Goal

Correct `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` section
3.1.4's "Undersized" row (line 53) so it records that an undersized section is
discarded with a `logging.WARNING` (matching `chunk_splitter` production
behavior, `chunk_splitter.py` line 285-288), and link the size-rule behaviors to
the tests that guarantee them in the doc's existing invariant-matrix style
(REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The current line 53 text is: "**Undersized** (fits but is smaller than
  `min_chunk`): the section is silently dropped, with no error or warning." —
  verified present in the doc.
- Production emits `discarded %s item(s) (%s chars) below min_chunk` at
  `logging.WARNING` when nothing was written (`written == 0`), else
  `logging.INFO` (`scripts/rag/ingestion/chunk_splitter.py` lines 285-288). The
  "Undersized" bullet corresponds to the all-discarded case, i.e. the WARNING.
- `test_T_002_below_min_chunk_markdown_logs_warning` asserts
  `rec.levelno == logging.WARNING`, confirming the documented level.
- **Overlap (ragcrv009 ↔ ragcrv010)**: ragcrv010 also edits section 3.1.4, but
  line 59 (the English/Markdown-heading `_split_overlong` attribution), not line
  53. The two edits are on different lines and address different concerns
  (discard-warning vs. oversized-sentence splitting); they are compatible and can
  be applied in either order. This procedure scopes the edit to the "Undersized"
  row only and does not touch line 59.

## Design decisions
- Replace the "silently dropped, with no error or warning" clause with a statement
  that the section is discarded and a `logging.WARNING` is emitted (below_min_chunk),
  noting the WARNING fires when no chunk was written for the source.
- Add rows to the existing invariant-matrix / behavior-link style connecting each
  size-rule behavior (Fits / Oversized / Undersized, and the Japanese/English
  below-`min_chunk` discard) to its guaranteeing test.
- Do not alter the documented `max_chunk` exception or non-ja behavior.

## Alternatives considered
- Rewriting the whole 3.1.4 section: rejected — only the "Undersized" row is
  stale; the Fits/Oversized/Japanese statements are accurate. Scope the edit to
  the one row plus the behavior links.

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Open section 3.1.4 ("Markdown Heading Chunking Behavior").
2. Edit the "**Undersized**" bullet (line 53): change
   "the section is silently dropped, with no error or warning" to something
   equivalent to: "the section is discarded; when no other chunk is written for
   the source a `logging.WARNING` ('... below min_chunk') is emitted, matching
   `chunk_splitter` production (`scripts/rag/ingestion/chunk_splitter.py`). If
   other content is written the discard is logged at `INFO`."
3. Add invariant-matrix rows linking each size-rule behavior to its guaranteeing
   test (e.g. `test_T_001_below_min_chunk_english_logs_warning`,
   `test_T_002_below_min_chunk_markdown_logs_warning`,
   `test_min_chunk_greater_than_max_chunk_raises_at_construction`) using the doc's
   existing matrix style.
4. Diff-review that the Fits and Oversized bullets and the Japanese paragraph
   (line 57-59) are unchanged by this edit.

### Method
Edit the single "Undersized" bullet and add matrix rows; verify against
`scripts/rag/ingestion/chunk_splitter.py` production (lines 285-288) and the two warning tests before
finalizing.

### Details
The stale clause omits the discard warning that `ragcrv003` introduced. Production
(`chunk_splitter.py` line 285) sets `_discard_level = logging.WARNING` when
`written == 0` and `logging.INFO` otherwise; the "Undersized" heading path drops
its section, so a source whose only section is undersized logs a WARNING. The
procedure states this precisely rather than claiming an unconditional warning.

## Compatibility considerations
Documentation-only; no runtime impact. The edit must not contradict the
`chunk_overlap` bound documented in `rag_05_01` or the size-rule statements
ragcrv010 corrects on line 59.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: the "Undersized" row records the discard warning and matches
  `scripts/rag/ingestion/chunk_splitter.py` production (lines 285-288); the size-rule behaviors are linked
  to their guaranteeing tests.
- Manual cross-read vs. `test_T_001_below_min_chunk_english_logs_warning`/`test_T_002_below_min_chunk_markdown_logs_warning` (both assert
  `levelno == logging.WARNING`).

## Completion criteria
Section 3.1.4 states that an undersized section is discarded with a
`logging.WARNING` (below_min_chunk), matching production, and each size-rule
behavior links to its guaranteeing test.

## Out of Scope
Re-writing the Fits/Oversized/Japanese statements, re-opening the size-rule
regression tests, or editing any other section (including line 59, which
ragcrv010 owns).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct "Undersized" row to record the discard warning | Pending | — | — | |
| 2 | Add size-rule → test links in invariant-matrix style | Pending | — | — | |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-050144_ragcrv009_chunk-test-construction-fragility.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-071413
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
