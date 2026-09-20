## Goal
Replace `docs/03_rag_05_5-constraints-reference.md`'s rows "Crawl depth"/
"Max crawl pages" and "Chunk size range"/"Chunk overlap" (REQ-003) with
role/constraint descriptions, each pointing to
`docs/03_rag_05_1-configuration-reference.md` and to NC-035/NC-034
respectively.

## Scope
In scope: exactly the 4 named rows (lines 20-21, 23-24) of the
"Constraint | Value" table (lines 17-28). Out of scope: the table's
remaining rows (Language detection threshold, Embedding dimensions,
Replication, `chunk_index` type constraint, `url`/`content` non-empty
requirements, `lang`/`chunking_strategy` validation scope) and the
"Evidence" section (lines 32-38).

## Assumptions
Per Plan Unknowns (UNK-01): the remaining rows are architectural/algorithm/
validation-level invariants, not environment-config values — confirmed
Out of Scope, no further action needed for them in this row.

## Design decisions
Replace only the `Value` column's cell content for the 4 target rows,
keeping each row's `Constraint` name unchanged — same approach as the
sibling `system_overview.md` procedure, preserving the table's overall
shape.

## Alternatives considered
Remove the 4 rows entirely — rejected: the table's remaining 8 rows stand
on their own without needing the 4 removed rows for context, unlike
`system_overview.md`'s Note paragraph; however, keeping all rows and
replacing only cell content is still preferred for consistency with the
sibling procedure's approach and to minimize structural diff.

## Implementation
### Target file
docs/03_rag_05_5-constraints-reference.md

### Procedure
Replace the `Value` column cell content for the 4 target rows as follows
(the `Constraint` column is unchanged):

- **Chunk size range**: replace `40–500 characters (Configurable via
  \`min_chunk\`/\`max_chunk\` in \`config/chunk_splitter.toml\`)` with
  `Bounded to keep each chunk within a useful retrieval granularity — not
  so small it is noise, not so large it dilutes relevance. Current
  operational value in [Configuration Reference §1.2](03_rag_05_1-configuration-reference.md).
  Rationale for the specific bounds tracked as unresolved in NC-034
  (\`docs/00_governance_03_issue-and-uncertainty-management.md\`).`
- **Chunk overlap**: replace `50 character sliding window
  (\`config/chunk_splitter.toml:chunk_overlap\`)` with
  `Preserves context continuity across chunk boundaries by including a
  trailing slice of the previous chunk. Current operational value in
  [Configuration Reference §1.2](03_rag_05_1-configuration-reference.md).
  Rationale tracked as unresolved in NC-034.`
- **Crawl depth**: replace `Code default requires \`max_depth\` to be
  specified (\`config/crawler.toml\` is mandatory). Operational
  \`config/crawler.toml\` uses \`max_depth = 3\`` with
  `Bounds BFS traversal depth to prevent unbounded crawl time and
  external-site load. Current operational value in
  [Configuration Reference §1.1](03_rag_05_1-configuration-reference.md).
  Rationale for the specific limit tracked as unresolved in NC-035.`
- **Max crawl pages**: replace `Code default is 500 pages per site
  (\`crawler.py\` uses \`cfg.get("max_pages", 500)\`). Operational
  \`config/crawler.toml\` uses \`max_pages = 200\`` with
  `Bounds crawl scope per site to prevent unbounded processing time and
  storage growth. Current operational value in
  [Configuration Reference §1.1](03_rag_05_1-configuration-reference.md).
  Rationale for the specific limit tracked as unresolved in NC-035.`

### Method
Four separate `Edit` calls (old_string/new_string), one per row's `Value`
cell — each is independently revertable.

### Details
Do not alter the `Constraint` column of any row, the table's other 8 rows,
or the "Evidence" section (lines 32-38) — the "Evidence" section's own
staleness note (line 34) documents the historical incident motivating this
Plan and is retained as-is per Plan Scope.

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting each Edit — no data migration or state change is involved. Each
of the 4 Method edits is independently revertable.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_05_5-constraints-reference.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_05_5-constraints-reference.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm no
  new finding for this file)

## Completion criteria
All 4 target cells no longer state a concrete value/comparison; each
states a role/constraint description and points to the Configuration
Reference and to NC-034/NC-035 as applicable; the table's other 8 rows and
the Evidence section are unchanged; `check_docs_quality.py`/
`check_docs_structure.py` report no new finding on this file relative to
the Plan's baseline (0 findings on both, unchanged).

## Out of scope
- `docs/03_rag_05_1-configuration-reference.md` and
  `docs/00_governance_03_issue-and-uncertainty-management.md` (read-only
  references, never edited).
- The table's remaining 8 rows and the "Evidence" section.

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
- **Requirement ID**: `REQ-003` — remove constraints-reference.md's config-value duplication
- **Source issue**: issues/20260920-102252_doccfgval01_remove-concrete-configuration-values-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114827_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131206
- **Related target files**: docs/03_rag_05_5-constraints-reference.md
