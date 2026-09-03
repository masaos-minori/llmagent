## Goal
Add the missing `tags` field, via manual `Edit`, to the 11 ADR files that
already carry `title`/`area`/`related` — `tools/manage_frontmatter.py
add-missing --fix` cannot reach `docs/adr/` (its glob is `docs/*.md` only, and
even for `docs/*.md` root files with existing-but-incomplete front matter it
only reports missing fields, it does not add them).

**Consolidated by explicit user decision** (2026-09-03): this document covers
all 11 ADR files together, per the same consolidation the user chose for the
43-file bucket (seq 03) — the mechanism (manual `Edit`, one `tags:` insertion
per file) and review standard are identical across all 11; only the specific
tag values differ per file, derived below from each ADR's own existing
`decision_scope:` field plus its title.

## Scope
- **In-Scope**: the 11 ADR files listed in Details below — inserting a
  `tags:` field into each, immediately after the existing `area: adr` line.
- **Out-of-Scope**: `docs/01_overview-files-03-scripts.md` /
  `docs/01_overview-files-04-shared.md` (seq 01/02), the 43
  missing-front-matter files (seq 03); any other front-matter field
  (`title`/`area`/`related`/`decision_scope`/`supersedes`) already present in
  these 11 files — unmodified by this row; any ADR body content.

## Assumptions
- All 11 ADR files are confirmed still missing `tags` as of 2026-09-03 —
  re-verified via `uv run python tools/check_docs_structure.py docs/adr/*.md`,
  matching this Plan's own 11-file list exactly with zero drift.
- Each of the 11 files already has a `title`, `area: adr`, `related:`, and
  (for all but ADR-001/ADR-012) a `decision_scope:` field with a real,
  specific value (`system`, `rag`, `eventbus`, `mcp`, or `mcp/git`) —
  re-verified 2026-09-03 by direct `Read` of all 11 files' front matter — this
  is a strong, already-evidenced basis for deriving each file's `tags` value,
  rather than inventing tags from scratch.
- `schemas/doc_front_matter.json` (from `docmeta01`, already implemented) sets
  `additionalProperties: true`, so these files' existing extra fields
  (`decision_scope`, `supersedes`) beyond the four canonical required fields
  remain valid alongside the new `tags` field — no conflict with the
  finalized schema.

## Design decisions
- **Each file's `tags` value is derived from its existing `decision_scope:`
  value plus 1-2 keywords from its own title**, rather than a generic
  `[adr]` tag repeated 11 times — this follows the same "genuine
  topic-specific keywords, not just the area name" standard this Plan's
  sibling row (seq 03) applies to the 43 missing-front-matter files, and is
  well-grounded in each file's own already-declared scope rather than an
  invented classification.
- **`tags:` is inserted immediately after `area: adr`**, before
  `decision_scope:` — matching `docs/00_governance_02_documentation-metadata.md`'s
  own canonical Front Matter Example field order (`title`, `area`, `tags`,
  `related`), with each file's pre-existing extra fields
  (`decision_scope`/`supersedes`) following after, unmodified in position.
- **`ADR-001` and `ADR-012` (the two files without a `decision_scope` field)
  still receive a topic-specific tag set, derived from their titles alone**
  (`workflow-engine`/`system` for ADR-001; `git`/`mcp` for ADR-012, matching
  ADR-012's own filename convention `mcp/git`-scoped naming even without a
  formal `decision_scope:` line) — the absence of `decision_scope` on these
  two files is a separate, pre-existing inconsistency (not every ADR has this
  field) this row does not need to fix to derive reasonable tags.

## Alternatives considered
- **Tag all 11 files with just `[adr]`** — rejected: this provides no more
  information than the existing `area: adr` field already does, defeating the
  purpose of a separate `tags` field for AI-agent document selection (this
  document's own Purpose statement).
- **Derive tags from a full body-content read of each ADR instead of
  `decision_scope` + title** — considered, rejected as the primary method:
  `decision_scope` is each ADR's own author-declared topical scope, already a
  higher-confidence signal than an AI-inferred summary of body content; a full
  body read remains available as a fallback verification step during
  execution if a file's `decision_scope`+title combination proves
  insufficient (none identified as insufficient during this row's own
  re-verification).

## Implementation
### Target file
11 files under `docs/adr/` (see the full list below) — no single canonical
target path; this document is filed under a descriptive slug
(`docs/adr/_bulk_11_adr_missing_tags_files`) per the user's consolidation
decision, not a real repository path.

### Procedure
1. Re-run `uv run python tools/check_docs_structure.py docs/adr/*.md` and
   re-confirm the 11-file list matches Details below (done above at
   generation time; re-confirm again immediately before editing).
2. For each of the 11 files, insert the `tags:` field (with the values in
   Details below) immediately after the existing `area: adr` line.

### Method
Direct text edit (e.g. via the `Edit` tool) per file, inserting the exact
`tags:` block shown in Details for that file.

### Details

**The 11 target files and their derived `tags` values** (each `tags:` block
is inserted immediately after that file's existing `area: adr` line):

| File | Existing `decision_scope` | Derived `tags` |
|---|---|---|
| `docs/adr/ADR-001-workflow-engine-mandatory.md` | (none) | `[system, workflow-engine, architecture]` |
| `docs/adr/ADR-002-config-isolation.md` | `system` | `[system, configuration, config-isolation]` |
| `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` | `system` | `[system, tool-routing, runtime-tool-registry]` |
| `docs/adr/ADR-004-environment-failure-handling-policy.md` | `system` | `[system, failure-handling, environment]` |
| `docs/adr/ADR-005-rag-source-derived-index-relationships.md` | `rag` | `[rag, index, canonical-source]` |
| `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` | `eventbus` | `[eventbus, sqlite, sse]` |
| `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | `mcp` | `[mcp, http, transport]` |
| `docs/adr/ADR-008-sqlite-4db-separation.md` | `system` | `[system, sqlite, database-separation]` |
| `docs/adr/ADR-009-rag-ft5-text-separation.md` | `rag` | `[rag, fts5, text-separation]` |
| `docs/adr/ADR-010-rag-fallback.md` | `rag` | `[rag, fallback, in-process]` |
| `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` | (none) | `[mcp, git, write-enforcement]` |

**Edit pattern** (identical structure for all 11 — example shown for
`ADR-002-config-isolation.md`):

Before:
```yaml
---
title: "ADR-002: プロセス単位の設定所有権とConfig Isolation"
area: adr
decision_scope:
  - system
related:
  - ADR-001
supersedes: []
```

After:
```yaml
---
title: "ADR-002: プロセス単位の設定所有権とConfig Isolation"
area: adr
tags:
  - system
  - configuration
  - config-isolation
decision_scope:
  - system
related:
  - ADR-001
supersedes: []
```

Apply the same pattern (insert `tags:` with the table's derived list
immediately after `area: adr`) to the remaining 10 files, using each file's
own derived tag list from the table above.

## Compatibility considerations
No other document links to any of these 11 files' front matter by anchor.
Independent of seq 01/02/03 — these 11 files are disjoint from the
fence-repair files and the 43 missing-front-matter files (which are all under
`docs/*.md`, not `docs/adr/`).

## Security considerations
None — documentation-only front-matter addition; no code, credentials, or
access-control content is affected.

## Rollback considerations
11 individual file edits under version control; revert via `git revert`. No
other file depends on any of these 11 files' front-matter structure.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All 11 target files | Structure/front-matter check | `uv run python tools/check_docs_structure.py docs/adr/*.md` | Zero "missing 'tags' field" findings among the 11 files |
| All 11 target files | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors introduced |
| All 11 target files | Manual review | Confirm each file's `tags` value is genuinely topic-specific (matches its `decision_scope`/title), not a bare `[adr]` repeat | Each of the 11 files has a distinct, meaningful tag set |

## Completion criteria
- All 11 ADR files have a `tags` field, each derived from that file's own
  `decision_scope` and title, per the table in Details (AC-1).
- `uv run python tools/check_docs_structure.py docs/adr/*.md` reports zero
  "missing 'tags' field" findings; `uv run python tools/check_docs_quality.py`
  reports no new errors.

## Out of scope
`docs/01_overview-files-03-scripts.md` / `docs/01_overview-files-04-shared.md`
(seq 01/02), the 43 missing-front-matter files (seq 03) — each covered by its
own implementation-procedure document. Confirming full-corpus `area` enum
membership and the final compliance survey (REQ-005/REQ-006) — this Plan's
own Phase 3 steps, applied across all 56 files together, not owned by any
single row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Covers all 11 ADR files via 11 individual `Edit` operations |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260902-194021_docmeta02_migrate_all_documents_to_canonical_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-125112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-161847
- **Related target files**: the 11 files listed in Details above
