## Goal
Replace `docs/03_rag_02_02_ingestion_pipeline-crawler.md`'s "2.1.1
Configuration Parameters" table (REQ-001) with a role/constraint
description of `max_depth`/`max_pages`/`skip_nofollow`, pointing to NC-035
for the rationale gap and reusing the section's existing
configuration-reference pointer rather than duplicating it.

## Scope
In scope: exactly the table at lines 48-52 (header through last data row).
Out of scope: the section heading (`### 2.1.1 Configuration Parameters`,
line 46), the existing configuration-reference pointer blockquote (line
54), and every other section of this file.

## Assumptions
Per Plan Assumptions: the existing pointer to
`docs/03_rag_05_1-configuration-reference.md` (line 54) is sufficient — no
second, duplicate pointer is added alongside the new role/constraint prose.

## Design decisions
Replace the 3-row table with 2 sentences: one covering `max_depth`/
`max_pages` together (both are BFS traversal bounds, both tracked by
NC-035), one covering `skip_nofollow` separately (a routing-behavior flag,
not a numeric limit, so it has no NC entry and needs no rationale pointer).

## Alternatives considered
Keep the table shape but blank out the value cells — rejected: this would
still be a config-value-shaped table (an implementation-reference pattern
`tools/check_docs_content_policy.py`'s new
`check_code_fallback_value_comparison` header-shaped path would likely
still match on the header row alone), not a genuine prose replacement.

## Implementation
### Target file
docs/03_rag_02_02_ingestion_pipeline-crawler.md

### Procedure
Replace lines 48-52 with:
```
`max_depth` and `max_pages` bound the crawl's BFS traversal to prevent
unbounded growth in processing time, storage, and external-site load — see
[section 1.1 Configuration Reference](03_rag_05_1-configuration-reference.md)
below for the current operational values. The rationale for the specific
limit values is tracked as unresolved in NC-035
(`docs/00_governance_03_issue-and-uncertainty-management.md`).
`skip_nofollow` controls whether nofollow-marked links are excluded from
the BFS queue.
```

### Method
One `Edit` call (old_string = the table's header row through its last data
row; new_string = the prose above).

### Details
Do not alter the `### 2.1.1 Configuration Parameters` heading or the
`> For a full list of parameters, see...` blockquote immediately below the
replaced content (line 54, unaffected since the old_string ends at the
table's last row).

## Compatibility considerations
Documentation-only; no public interface, CLI, or data format changes. No
compatibility impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting the single Edit — no data migration or state change is involved.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/03_rag_02_02_ingestion_pipeline-crawler.md`
- `uv run python tools/check_docs_structure.py docs/03_rag_02_02_ingestion_pipeline-crawler.md`
- `uv run python tools/check_docs_content_policy.py` (full-tree; confirm no
  new finding for this file)

## Completion criteria
The table no longer exists, replaced by the prose in Procedure; the
heading and existing configuration-reference blockquote are unchanged;
`check_docs_quality.py`/`check_docs_structure.py` report no new finding on
this file relative to the Plan's baseline (0 findings on both, unchanged).

## Out of scope
- `docs/03_rag_05_1-configuration-reference.md` and
  `docs/00_governance_03_issue-and-uncertainty-management.md` (read-only
  references, never edited).
- Any other section of this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the 1 Edit per Procedure/Method | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` — remove crawler.md's config-value duplication
- **Source issue**: issues/20260920-102252_doccfgval01_remove-concrete-configuration-values-from-rag-design-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114827_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131206
- **Related target files**: docs/03_rag_02_02_ingestion_pipeline-crawler.md
