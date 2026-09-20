## Goal
Remove `docs/03_rag_02_04_ingestion_pipeline-ingester.md`'s 2 hand-maintained
CLI argument tables and 2 duplicated error-handling tables (REQ-004),
replacing each with a pointer to its actual canonical source, and resolve a
factual contradiction between the two error-handling table copies found
during this row's adversarial verification.

## Scope
In scope: exactly the 4 locations named in REQ-004 —
- CLI argument table, line 146 (section "4a" → 4.3, lines 144-148)
- Error-handling table, line 172 (section "4a" → 4.6, lines 170-180)
- CLI argument table, line 224 (section "4c" → 4.3, lines 222-226)
- Error-handling table, line 250 (section "4c" → 4.6, lines 248-258)

Out of scope: sections 4.1/4.2/4.2.1 (Class Overview, Detailed Behavior,
Immutable Deletion Order — appear in both the `## 4.` (lines 33-77) and
`## 4a.` (lines 106-143) headings, identical text, not implementation
reference, no finding), section 4.4 (Embedding API — an `http` code block,
not flagged by any tool or manual check; the HTTP request/response shape is
short and illustrative, not a full payload spec), section 4.5 (Database
Updates — already pointer-only), section 4.7 (Logging — already
pointer-only). Do not touch `docs/03_rag_05_4-error-handling-reference.md`
(Out-of-Scope per Plan Design), `scripts/rag/ingestion/ingester.py`, or any
other source file. **Deduplicating the `## 4.`/`## 4a.`/`## 4c.` section
structure itself is explicitly out of scope** — see Plan Design's
"ingester.md duplicate-section finding" and Risks; this row only remediates
the 4 implementation-reference table locations, not the section duplication
they live inside.

## Assumptions
- Carried from Plan Design: this file contains 3 near-duplicate `## 4`
  headings (`## 4.` line 33, `## 4a.` line 106, `## 4c.` line 220). Only
  `## 4a.` and `## 4c.` contain CLI-argument/error-handling tables (`## 4.`
  ends at line 77, before any such table) — confirmed by `grep -n '^## 4'`
  and direct reading during Plan creation and this row's own verification;
  no third occurrence of either table exists.

## Design decisions
- Point both CLI argument table occurrences (146, 224) at
  `scripts/rag/ingestion/ingester.py --help` — identical replacement text
  for both, since both occurrences' current content is byte-identical
  (confirmed: both show only the `--force` row with the same description).
- For both error-handling table occurrences (172, 250): point to
  `scripts/rag/ingestion/ingester.py` directly (the actual `raise`/`except`
  sites), not to `docs/03_rag_05_4-error-handling-reference.md`. Per Plan
  Design's "ingester.md duplicate-section finding," that canonical doc's
  "RagIngester" section covers only 3 of the 6 error cases documented here
  (missing: "Improper `chunks_vec` deletion order," "Embedding dimension
  mismatch," "Artifact validation failure," "File move failure") — pointing
  there would silently drop 4 real, currently-documented cases with no
  other home.
- Resolve the factual contradiction between the two copies (line 179's
  "no `WARNING` is logged... not counted as an embedding failure" vs. line
  257's "Logs a `WARNING`; skips the chunk as an embedding failure," for the
  "Artifact validation failure" row) by pointing BOTH occurrences at the
  same accurate source instead of restating either claim: verified against
  `scripts/rag/ingestion/ingester.py:56-60`
  (`IngestUrlResult.validation_failure()`, `n_embed_failed` stays at its
  dataclass default `0`, confirmed not incremented) and the two catch sites
  at lines 217-218 and 235-236 (`except ChunkFormatError: return
  IngestUrlResult.validation_failure(...)`, no `logger.warning` call at
  either site) — the line-179 copy was accurate, the line-257 copy was
  stale. Since both occurrences become the same pointer, this
  implementation does not need to restate which one was "right" in the doc
  itself — the contradiction disappears because neither copy asserts
  divergent behavior any longer.

## Alternatives considered
- Fix only the stale line-257 copy to match line-179's accurate text,
  leaving both as hand-maintained tables — rejected: this still leaves 2
  duplicated implementation-reference tables (REQ-004's actual target),
  just now consistent with each other; it would not satisfy REQ-004's own
  goal of removing the tables, only the contradiction.
- Merge the `## 4.`/`## 4a.`/`## 4c.` sections into one — rejected as out
  of scope for this row (see Scope); flagged separately in the Plan's Risks
  for a follow-up documentation-fix issue.

## Implementation
### Target file
docs/03_rag_02_04_ingestion_pipeline-ingester.md

### Procedure
1. Replace the first CLI Arguments table (lines 146-148, under `## 4a.`)
   with a one-line pointer: "Run `uv run python
   scripts/rag/ingestion/ingester.py --help` for the current argument
   list."
2. Replace the first Error Handling table (lines 172-180, under `## 4a.`)
   with a pointer to `scripts/rag/ingestion/ingester.py` naming the 6
   documented cases' approximate locations (embedding-retry logic, `lang`
   validation, `chunks_vec` deletion-order check, embedding-dimension
   check, `IngestUrlResult.validation_failure()` at lines 56-60 plus its
   two catch sites at lines 217-218/235-236, and the file-move failure
   path) rather than restating the table.
3. Replace the second CLI Arguments table (lines 224-226, under `## 4c.`)
   with the identical pointer text used in step 1.
4. Replace the second Error Handling table (lines 250-258, under `## 4c.`)
   with the identical pointer text used in step 2.

### Method
Four separate `Edit` calls (old_string/new_string), one per location above,
in the order listed. Because the two CLI tables (and, separately, the two
error-handling tables) currently have near-identical or identical
surrounding text, use enough surrounding context in each `old_string` (the
preceding heading and following section marker) to uniquely match each
occurrence — do not rely on `replace_all` for these, since the two
occurrences must each be verified individually per Details below.

### Details
- Before editing, re-confirm via `grep -n` that lines 146/172/224/250 still
  hold the same content as recorded in this Plan (idempotent-command rule:
  skip re-reading if the file is confirmed unchanged since this document's
  generation).
- Do not attempt to deduplicate or merge the `## 4.`/`## 4a.`/`## 4c.`
  headings themselves, their 4.1/4.2/4.2.1/4.4/4.5/4.7 content, or the two
  "Related Documents"/"Keywords" blocks — Out of scope (see Scope).
- Preserve the `### 4.3 CLI Arguments` and `### 4.6 Error Handling`
  headings (both occurrences) exactly as-is.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
each Edit — no data migration or state change is involved. Each of the 4
Method edits is independently revertable.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_02_04_ingestion_pipeline-ingester.md`
  (note: this file has a pre-existing "3 H1 headings" baseline finding —
  Plan AC-3 — unrelated to this row's change; do not fix it here)
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm
  lines 146/172/224/250 no longer appear in the output for this file)

## Completion criteria
All 4 locations in Scope no longer contain the original table, each
replaced with the pointer described in Design decisions; both CLI-table
replacements are textually identical to each other, and both
error-handling-table replacements are textually identical to each other
(resolving the line-179/line-257 contradiction by construction);
`check_docs_quality.py`, `check_docs_structure.py`, and
`check_docs_content_policy.py` report no new finding on this file relative
to this Plan's baseline (ingester.md: 4 tool findings → 0).

## Out of scope
- `docs/03_rag_05_4-error-handling-reference.md` (Out-of-Scope per Plan).
- Any `scripts/rag/**` source file.
- Deduplicating/merging the `## 4.`/`## 4a.`/`## 4c.` section structure
  (see Plan Design and Risks — recommend a separate follow-up issue).
- Sections 4.1, 4.2, 4.2.1, 4.4, 4.5, 4.7, and any content not named in
  Scope above.
- Fixing the pre-existing "3 H1 headings" `check_docs_structure.py` finding
  on this file (pre-existing, unrelated to this row's change — Plan AC-3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 4 Edits per Procedure/Method | Pending | — | — | |
| 2 | N/A: no test suite applies to a documentation content change | Pending | — | — | |
| 3 | Run the 3 commands in Validation plan | Pending | — | — | |
| 4 | N/A: no further documentation update needed beyond this file itself | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — remove ingester.md's implementation-reference content
- **Source issue**: issues/20260920-084526_docref01_isolate-implementation-reference-content-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-094101_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-094739
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
