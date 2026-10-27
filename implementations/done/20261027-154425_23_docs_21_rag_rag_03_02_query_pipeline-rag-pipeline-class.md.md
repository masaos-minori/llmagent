# Implementation Procedure: Rename the HTTP Mode heading, body, and prevention-table occurrences

## Goal
Rename all three `rag_service_url` occurrences — the section heading, body sentence, and prevention-table row — to `rag_query_service_url` (REQ-005).

## Scope
- Heading rename "### HTTP Mode (`rag_service_url`)" (L36), body sentence rename (L38), prevention-table cell rename (L46). No other content changes.

## Assumptions
- Mechanical rename only: every edit is a whole-word substitution of `rag_service_url` to `rag_query_service_url`; no semantics, defaults, or reader logic change (Plan Design).
- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text is never touched (REQ-003).
- Rebase immediately before implementing: the sibling rag001 Plan procedures (implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures (implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second rebases (Plan Dependencies).

## Design decisions
- Heading renames keep any in-repo links to this page working only if the anchor is not referenced by name; grep docs/ for links to the old heading anchor before committing and update them in the same edit if found.

## Alternatives considered
- Keep an alias mapping `rag_service_url` -> `rag_query_service_url` — rejected: zero consumers exist (verified inventory), and an alias re-introduces the ambiguity the rename removes (Plan Design).
- Keep the heading on the old key — rejected: it is live in `config/ingester.toml` and `/opt/llm/config/ingester.toml` (Plan Design).

## Implementation
### Target file
`docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md`
### Procedure
1. Rename L36 heading to "### HTTP Mode (`rag_query_service_url`)".
2. Rename L38 body occurrence (keeping the `rag_auth_token` pairing sentence intact).
3. Rename L46 prevention-table cell ("The MCP adapter hardcodes `rag_query_service_url=""` ...").
### Method
Whole-word substitution of `rag_service_url` restricted to occurrences NOT part of `rag_pipeline_service_url` (the ingestion key is a superset substring — verify each match or use `grep -v rag_pipeline_service_url`), followed by the exhaustiveness grep.
### Details
- Verified occurrences: L36, L38, L46.

## Compatibility considerations
- The rename is repo-internal: no repo or deployed config file references the old spelling (verified 2026-10-27 across `config/` and `/opt/llm/config/`), so no external consumer is affected (REQ-006, Plan Design).
- `rag_query_service_url` collides with no existing identifier; the only `rag_query*` names in the repo are the unrelated `rag_query_id` log context key and `rag_query_count` session stat (Plan Assumptions, verified).

## Security considerations
- No security surface change. With an unrecognized key the loader keeps the `None` default, which means "no HTTP delegation" — the fail-safe direction (Plan Design). `rag_auth_token` pairing semantics are unchanged.

## Rollback considerations
- Single atomic rename commit; rollback is `git revert` of that commit. No data migration, no config-file change, and no deployed-state change means revert is complete on its own.

## Validation plan
- 21_rag documentation consistency check passes; grep shows zero standalone old-name occurrences on the page.

## Completion criteria
- Heading, body, and table name only `rag_query_service_url`.

## Out of Scope
- Renaming `rag_pipeline_service_url` or editing `config/ingester.toml` / `/opt/llm/config/ingester.toml` (REQ-003).
- Backward-compat alias or mapping for the old spelling (Plan Design: no consumer exists).
- Renaming `rag_auth_token` or any other RAG config field.
- Changes to which path reads which key, defaults, or delegation semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261027-214410 | 20261027-214410 | batch 20261027-154425 validated |
| 2 | Add or update tests per Validation plan | Completed | 20261027-214410 | 20261027-214410 | batch 20261027-154425 validated |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261027-214410 | 20261027-214410 | batch 20261027-154425 validated |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261027-214410 | 20261027-214410 | batch 20261027-154425 validated |

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
- **Generated at**: 20261027-154425
- **Related target files**: docs/21_rag/rag_03_02_query_pipeline-rag-pipeline-class.md
