## Goal
Remove `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s hand-maintained
TypedDict field table, CLI argument table, and duplicated error-handling
table (REQ-003), replacing each with a pointer to its actual canonical
source, and correct the table's pre-existing TypedDict naming error found
during this row's adversarial verification.

## Scope
In scope: exactly the 3 locations named in REQ-003 —
- TypedDict table, line 39 (section "Typed dict", lines 37-41)
- CLI argument table, line 103 (section 2.3, lines 101-107)
- Error-handling table, line 125 (section 2.5, lines 123-130)

Out of scope: sections 2.1-2.2 prose (Class Overview, Configuration
Parameters, Detailed Behavior, Local File Injection, Comparison tables at
lines 80-84 and 94-99), section 2.4 (Output JSON Format prose, lines
109-121 — already pointer-only, no table or JSON literal to remove), and
section 2.6 (Logging — already a pointer). Do not touch
`docs/03_rag_05_4-error-handling-reference.md` (Out-of-Scope per Plan
Design) or any `scripts/rag/**` source file.

## Assumptions
- Section 2.4's existing prose (lines 109-121) already points to
  `pipeline_utils.py`, `error-handling-reference.md`, `chunksplitter.md`,
  and `dto-models_data.md` rather than restating a table or JSON example —
  no change needed there; it is not part of REQ-003's cited locations.
- The Comparison tables at lines 80-84 ("Condition | Decision") and 94-99
  ("Aspect | Web (HTTP) | Local Files") are design-intent (responsibility
  boundary / behavior comparison), not implementation reference — no tool
  or manual finding flagged them; out of scope per Scope above.

## Design decisions
- Point the TypedDict table at `scripts/rag/ingestion/pipeline_utils.py`
  directly, and correct the table's naming error while doing so: the
  table's `CrawlPayload` row (line 41) does not match any actual symbol in
  the codebase (confirmed via grep against `scripts/rag/ingestion/
  pipeline_utils.py` and `scripts/rag/models_data.py` — zero matches for
  `CrawlPayload`); the real TypedDict is `CrawlJsonPayload`
  (`pipeline_utils.py:23`, per this Plan's Design "Naming-accuracy
  finding"). The replacement text must name `CrawlJsonPayload`, not
  `CrawlPayload`.
- Point the CLI argument table at `scripts/rag/ingestion/crawler.py --help`.
- For the error-handling table: the "HTTP request failure," "Exception per
  URL," and "Language is not ja/en" rows are consistent with
  `docs/03_rag_05_4-error-handling-reference.md`'s "Crawler" section
  (confirmed by direct comparison during this row's adversarial
  verification — no discrepancy found, unlike REQ-002/REQ-004's rows) —
  point these to that canonical section. The "Text < 100 characters" row is
  not an error/exception case (it is a normal fallback rule) and duplicates
  section 2.2's existing "Language Detection" bullet ("Pages with fewer
  than 100 characters use the hint language") — drop this row from the
  table rather than pointing it anywhere; the information already exists
  verbatim in retained prose one section above.

## Alternatives considered
- Keep the "Text < 100 characters" row and point it at section 2.2's own
  bullet via a cross-reference — rejected as unnecessary: both are in the
  same document, a few lines apart; a self-referential pointer adds
  indirection without removing any duplication risk (both would still need
  updating together if the threshold changes).

## Implementation
### Target file
docs/03_rag_02_02_ingestion_pipeline-crawler.md

### Procedure
1. Replace the "Typed dict" table (lines 39-41) with a short pointer to
   `CrawlJsonPayload` in `scripts/rag/ingestion/pipeline_utils.py`.
2. Replace the CLI Arguments table (lines 103-107) with a one-line pointer:
   "Run `uv run python scripts/rag/ingestion/crawler.py --help` for the
   current argument list."
3. Replace the Error Handling table (lines 125-130) with a pointer to
   `docs/03_rag_05_4-error-handling-reference.md`'s "Crawler" section for
   the 3 genuine error/exception cases; drop the "Text < 100 characters"
   row (duplicates section 2.2, not an error case).

### Method
Three separate `Edit` calls (old_string/new_string), one per location
above, in the order listed — each is independently revertable.

### Details
- Preserve the `### 2.3 CLI Arguments` and `### 2.5 Error Handling`
  headings exactly as-is.
- Do not alter section 2.4 (already pointer-only, per Assumptions) or any
  content in Out of scope below.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
each Edit — no data migration or state change is involved.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_02_02_ingestion_pipeline-crawler.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_02_02_ingestion_pipeline-crawler.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm
  lines 39/103/125 no longer appear in the output for this file)

## Completion criteria
All 3 locations in Scope no longer contain the original table, each
replaced per Design decisions (with the TypedDict naming corrected and the
non-error CLI/error row dropped as described); `check_docs_quality.py`,
`check_docs_structure.py`, and `check_docs_content_policy.py` report no new
finding on this file relative to this Plan's baseline (crawler.md: 3 tool
findings → 0).

## Out of scope
- `docs/03_rag_05_4-error-handling-reference.md` (Out-of-Scope per Plan).
- Any `scripts/rag/**` source file.
- Sections 2.1, 2.2, 2.4, 2.6, and any content not named in Scope above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 3 Edits per Procedure/Method | Completed | 20260920-100634 | 20260920-100634 | Stale detection: not stale. Adversarial verification: all 3 locations confirmed unchanged. Applied all 3 Edits, correcting CrawlPayload->CrawlJsonPayload naming. |
| 2 | N/A: no test suite applies to a documentation content change | Completed | 20260920-100634 | 20260920-100634 |  |
| 3 | Run the 3 commands in Validation plan | Completed | 20260920-100634 | 20260920-100634 | check_docs_quality.py: No issues found. check_docs_structure.py: All checks passed. check_docs_content_policy.py: 0 findings for this file (was 3). |
| 4 | N/A: no further documentation update needed beyond this file itself | Completed | 20260920-100634 | 20260920-100634 |  |

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
- **Requirement ID**: `REQ-003` — remove crawler.md's implementation-reference content
- **Source issue**: issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-094101_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-094739
- **Related target files**: docs/03_rag_02_02_ingestion_pipeline-crawler.md