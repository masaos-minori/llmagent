# Implementation Procedure: Rename key occurrences and add the two-key contrast paragraph in the RAG configuration reference (rag_05_01)

## Goal

Rename the remaining key occurrences to `rag_query_service_url` (new) and add the
purpose-distinction paragraph contrasting the query-path key with the ingestion-path key
`rag_pipeline_service_url` (REQ-005, AC-5).

## Scope

- Two standalone occurrences (verified 2026-10-27): the `AgentConfig.rag` ownership paragraph
  at L90 and the bullet "not a key of `config/agent.toml` ..." at L93.
- One new contrast paragraph in the same section.
- No other section of the page changes.

## Assumptions

- Documentation-only row; churn 14 commits/30d per the Plan Affected areas: rebase immediately
  before editing.
- The Plan row's occurrence evidence predates recent doc churn; current verification finds two
  standalone occurrences (the Plan's count included mentions resolved against the then-current
  page). AC-5's grep gate is the completion authority.
- Overlap with the rag002 Plan procedure
  (`implementations/20261027-144351_03_docs_21_rag_rag_05_01-configuration-reference.md.md`,
  timeout paragraph extension): disjoint paragraphs; recorded Compatible in both Plans; second
  implementer rebases.

## Design decisions

- Contrast paragraph content per Plan Design and Assumptions: `rag_query_service_url` selects
  HTTP delegation on the query path (ADR-010: unused in production) and pairs with the
  unchanged `rag_auth_token`; `rag_pipeline_service_url` is the ingestion-path callback into
  the rag_pipeline MCP server, live in `config/ingester.toml` (Plan Design "query key vs
  server-name-style ingestion key").

## Alternatives considered

- Separate subsection for the contrast — rejected: the page already discusses both keys in the
  same section; a paragraph keeps the contrast local (Plan Documentation Impact).

## Implementation
### Target file

`docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure

1. Rename the key named in the L90 paragraph ("or `rag_service_url`. Those are owned by ...")
   to the new spelling.
2. Rename the key named in the L93 bullet ("`rag_service_url` is not a key of
   `config/agent.toml` ...") to the new spelling; the ADR cross-reference in the bullet stays.
3. After the L93 bullet, add one contrast paragraph: `rag_query_service_url` (query path;
   selects HTTP delegation to an external RAG service; paired with `rag_auth_token`; never set
   in production per ADR-010) vs `rag_pipeline_service_url` (ingestion path; set in
   `config/ingester.toml`; points at the rag_pipeline MCP server).

### Method

Two single-token renames plus one inserted paragraph; land after the scripts rename rows so
the doc describes the renamed surface.

### Details

- Run the file-level grep after editing: `grep -n "rag_service_url"
  docs/21_rag/rag_05_01-configuration-reference.md | grep -v "rag_pipeline_service_url"` must
  return nothing (AC-5).

## Compatibility considerations

- Docs only; symbols named by the new text (`rag_auth_token`, `rag_pipeline_service_url`,
  `config/ingester.toml`, ADR-010) all exist before and after.

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_05_01-configuration-reference.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean (the configkey
  check must see the new spelling only).
- `grep -rn "rag_service_url" docs/ | grep -v "rag_pipeline_service_url"` — matches only the
  ADR rename note (AC-5, via row 29).

## Completion criteria

- AC-5: no standalone old-spelling mention on this page; the two-key contrast paragraph is
  present.

## Out of Scope

- The timeout paragraph extension (rag002 Plan, separate procedure), the other 7 doc pages
  (own procedure documents), and any config-file change (REQ-003/AC-4: config files are not
  touched by this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 4 row; land after Phase 2-3 rows |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain rag) | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: docs/21_rag/rag_05_01-configuration-reference.md
