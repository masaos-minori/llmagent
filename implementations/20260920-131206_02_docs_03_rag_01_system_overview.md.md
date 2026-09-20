## Goal
Replace `docs/03_rag_01_system_overview.md`'s "## Constraints" table rows
"Crawl Depth"/"Max Pages Per Site" and "Chunk Size"/"Chunk Overlap"
(REQ-002) with role/constraint descriptions, each pointing to
`docs/03_rag_05_1-configuration-reference.md` for the current value and to
NC-035 or NC-034 for the rationale gap.

## Scope
In scope: exactly the 4 named rows (lines 210-211, 213-214) of the
"## Constraints" table (lines 205-215). Out of scope: the table's other 3
rows (Language Detection, Embedding Dimension, Database), the "Note"
paragraph immediately below the table (line 217), and the
"### Constraint Violation Behavior and Enforcement" subsection (lines
219-233).

## Assumptions
Per Plan Design's "Note-paragraph interaction": the Note paragraph remains
accurate after this edit (it still describes 6 rows in the same table, 4 of
which now express role/constraint language instead of raw numbers) — no
edit to the Note is needed.

## Design decisions
Replace only the `Value` column's cell content for the 4 target rows,
keeping each row's `Constraint` name and `Source` column unchanged — this
preserves the table's overall shape (still a 3-column, 7-row table) while
removing the concrete-value/comparison content from exactly the 4 cells
targeted.

## Alternatives considered
Remove the 4 rows from the table entirely (reducing it to 3 rows) —
rejected: the Plan's Design explicitly notes the "Note" paragraph refers to
"these six constraint values" for the whole table; removing rows would
require also editing that Note (Out of Scope) to stay accurate, whereas
keeping all 7 rows and only changing 4 cells' content leaves the Note's
"six constraint values" framing intact.

## Implementation
### Target file
docs/03_rag_01_system_overview.md

### Procedure
Replace the `Value` column cell content for the 4 target rows as follows
(the `Constraint` and `Source` columns are unchanged):

- **Chunk Size**: replace `Min 40 chars, Max 500 chars` with
  `Bounded to keep each chunk within a useful retrieval granularity — not
  so small it is noise, not so large it dilutes relevance. Current
  operational value in [Configuration Reference §1.2](03_rag_05_1-configuration-reference.md).
  Rationale for the specific bounds tracked as unresolved in NC-034
  (\`docs/00_governance_03_issue-and-uncertainty-management.md\`).`
- **Chunk Overlap**: replace `50 character sliding window` with
  `Preserves context continuity across chunk boundaries by including a
  trailing slice of the previous chunk. Current operational value in
  [Configuration Reference §1.2](03_rag_05_1-configuration-reference.md).
  Rationale tracked as unresolved in NC-034.`
- **Crawl Depth**: replace `Operational value is 3 (max 3 hops from start
  URL, \`config/crawler.toml\`'s \`max_depth\`). Differs from code
  fallback; use operational config` with
  `Bounds BFS traversal depth to prevent unbounded crawl time and
  external-site load. Current operational value in
  [Configuration Reference §1.1](03_rag_05_1-configuration-reference.md).
  Rationale for the specific limit tracked as unresolved in NC-035.`
- **Max Pages Per Site**: replace `Operational value is 200 (max 200 pages
  per site, \`config/crawler.toml\`'s \`max_pages\`). Code fallback is
  500; use operational config` with
  `Bounds crawl scope per site to prevent unbounded processing time and
  storage growth. Current operational value in
  [Configuration Reference §1.1](03_rag_05_1-configuration-reference.md).
  Rationale for the specific limit tracked as unresolved in NC-035.`

### Method
Four separate `Edit` calls (old_string/new_string), one per row's `Value`
cell — each is independently revertable. Use enough surrounding context
(the row's `Constraint` name cell) in each `old_string` to uniquely match
the correct row, since some phrase fragments (e.g. "operational value")
recur across rows.

### Details
Do not alter the `Constraint` or `Source` columns of any row, the table's
other 3 rows (Language Detection, Embedding Dimension, Database), the
"Note" paragraph (line 217), or the
"### Constraint Violation Behavior and Enforcement" subsection.

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
- `uv run python tools/check_docs_quality.py docs/03_rag_01_system_overview.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_01_system_overview.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm no
  new finding for this file)

## Completion criteria
All 4 target cells no longer state a concrete value/comparison; each
states a role/constraint description and points to the Configuration
Reference and to NC-034/NC-035 as applicable; the table's other 3 rows and
the Note paragraph are unchanged; `check_docs_quality.py`/
`check_docs_structure.py` report no new finding on this file relative to
the Plan's baseline (0 findings on both, unchanged).

## Out of scope
- `docs/03_rag_05_1-configuration-reference.md` and
  `docs/00_governance_03_issue-and-uncertainty-management.md` (read-only
  references, never edited).
- The table's "Language Detection", "Embedding Dimension", and "Database"
  rows, the "Note" paragraph, and the "Constraint Violation Behavior and
  Enforcement" subsection.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 4 Edits per Procedure/Method | Completed | 20260920-134553 | 20260920-134553 | 4 target rows confirmed unchanged before edit. Applied all 4 Edits. |
| 2 | N/A: no test suite applies to a documentation content change | Completed | 20260920-134553 | 20260920-134553 |  |
| 3 | Run the 3 commands in Validation plan | Completed | 20260920-134553 | 20260920-134553 | check_docs_quality.py/check_docs_structure.py: No issues. check_docs_content_policy.py: 0 findings for this file (was 2). Note paragraph and other 3 rows confirmed unchanged. |
| 4 | N/A: no further documentation update needed beyond this file itself | Completed | 20260920-134553 | 20260920-134553 |  |

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
- **Requirement ID**: `REQ-002` — remove system_overview.md's config-value duplication
- **Source issue**: issues/20260920-102252_doccfgval01_remove-concrete-configuration-values-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114827_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131206
- **Related target files**: docs/03_rag_01_system_overview.md