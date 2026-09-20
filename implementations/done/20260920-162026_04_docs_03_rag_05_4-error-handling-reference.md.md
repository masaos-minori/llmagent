## Goal
Remove the literal error-handling action-column entries in
`docs/03_rag_05_4-error-handling-reference.md`'s `## Crawler` table (lines 18-22) that
restate visible `try`/`except` behavior, per `REQ-004` (Plan
`plans/20260920-155829_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at this table's location while the fatal/non-fatal and skip-unit-granularity
intent is preserved as prose.

## Scope
In scope: the `## Crawler` table (lines 18-22) only. Out of scope: every other
error-handling table in this same file (`## ChunkSplitter` line 26, `## Pipeline Utils`
line 40, `## RagIngester` line 103, `## RagPipeline` line 112) — none of these were
flagged by `check_docs_content_policy.py` (re-confirmed 2026-09-20) and none is covered
by `REQ-004`; and every prose section of this file (`### ChunkFormatError
Classification Guidance` and its subsections).

## Assumptions
The finding at line 18 and the table's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file since. `scripts/rag/ingestion/crawler.py` (confirmed to
exist and to define `_fetch_retry` at line 63 and the per-URL crawl-loop exception
handling at lines 108-118) is the canonical source for the Crawler's exact
retry/backoff/exception behavior.

## Design decisions
Replace the three-row table with a short paragraph stating the design-level fact common
to all three rows — every Crawler-level failure is non-fatal at URL granularity — and
pointing to `scripts/rag/ingestion/crawler.py` for the exact retry/backoff formula and
log level, which are code-derivable and not retained. The distinction between "retries
before failing" (HTTP failure) and "fails immediately, skips" (exception, bad `lang`)
is design intent (how much resilience this specific failure mode gets) and is retained
in prose.

## Alternatives considered
- Keep the table shape but replace the `Action` cells with `"see crawler.py"`:
  rejected — `check_docs_content_policy.py`'s error-handling table detection likely
  keys on the `| Error | Action |` header shape itself (consistent with how the
  `PipelineExecutionResult` finding in a sibling row of this same Plan keys on its own
  table header), so a same-shaped table risks reproducing the finding.
- Drop the fatal/non-fatal distinction entirely and only point to the source file:
  rejected — this is exactly the design-intent content the Plan's Implementation
  intent requires retaining ("keep the failure-mode/severity intent... and drop the
  literal action strings").

## Implementation
### Target file
`docs/03_rag_05_4-error-handling-reference.md`

### Procedure
1. Read lines 16-23 to confirm current content matches the Plan's recorded evidence.
2. Replace the `## Crawler` table (lines 18-22, i.e. the header row through the
   `lang` row) with a short paragraph stating: all Crawler-level failures are
   non-fatal at URL granularity; an HTTP failure is retried with backoff before
   falling through to the same per-URL exception handling that an unhandled exception
   or an unsupported `lang` value also hits, each of which skips just that URL without
   stopping the overall crawl; point to `scripts/rag/ingestion/crawler.py` for the
   exact retry count/backoff formula.
3. Leave the `## Crawler` heading and every other heading/section in this file
   unchanged.

### Method
Single localized `Edit`, replacing the table (lines 18-22) with the paragraph from
Procedure step 2. Do not touch any other line in this file.

### Details
Do not restate the specific backoff formula (`min(2**i, 10)` seconds) or the exact log
level (`WARNING`) — both are directly readable from
`scripts/rag/ingestion/crawler.py` and are the code-derivable content this cleanup
removes. Do retain: (a) that HTTP failure gets a retry attempt before failing, while
the other two cases do not, and (b) that every case's failure unit is one URL, not the
whole crawl run — both are severity/scope decisions a reader cannot get from a
one-line glance at the code without also reading the surrounding control flow.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other three Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/03_rag_05_4-error-handling-reference.md` (Plan `AC-4`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/03_rag_05_4-error-handling-reference.md`
  — confirm it passes.
- `uv run python tools/check_docs_consistency.py --domain rag` — confirm no new drift
  finding.

## Completion criteria
The `## Crawler` section no longer contains an `| Error | Action |` table; it instead
states the non-fatal/URL-granularity intent and points to
`scripts/rag/ingestion/crawler.py` for the exact mechanism; `check_docs_content_policy.py`
reports zero findings for this file.

## Out of scope
- The four other error-handling tables in this file (`ChunkSplitter`, `Pipeline
  Utils`, `RagIngester`, `RagPipeline`) — not flagged, not part of `REQ-004`.
- Any other `docs/*.md` file — see the Plan's other three target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-165929 | 20260920-165929 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-165929 | 20260920-165929 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-165929 | 20260920-165929 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-165929 | 20260920-165929 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-004` — remove the literal error-handling action entries that restate visible try/except behavior
- **Source issue**: issues/20260920-154305_dcp009_rag-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-155829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162026
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md