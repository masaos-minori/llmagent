# Implementation Procedure: Rename key occurrences and add the two-key purpose-contrast paragraph

## Goal
Rename both `rag_service_url` occurrences to `rag_query_service_url` and add an explicit paragraph contrasting the two service-URL keys (query delegation vs ingestion callback) (REQ-005, AC-5).

## Scope
- Two occurrence renames (verified at L90 and L93, both negative statements about `config/agent.toml`) plus one new contrast paragraph.

## Assumptions
- Mechanical rename only: every edit is a whole-word substitution of `rag_service_url` to `rag_query_service_url`; no semantics, defaults, or reader logic change (Plan Design).
- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text is never touched (REQ-003).
- Rebase immediately before implementing: the sibling rag001 Plan procedures (implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures (implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second rebases (Plan Dependencies).
- Overlap: the rag002 Plan procedures (implementations/20261027-144351_03_*) add the `http_timeout` paragraph to this same page; the paragraphs are disjoint and whichever implements second rebases (Plan Dependencies).

## Design decisions
- The contrast paragraph is required by the Issue's Documentation Impact: neither this page nor ADR-010 currently presents the two key names as a pair (Plan Problem).

## Alternatives considered
- Document the distinction only in ADR-010 — rejected: the config reference is the page operators read when configuring RAG (Plan Documentation Impact).

## Implementation
### Target file
`docs/21_rag/rag_05_01-configuration-reference.md`
### Procedure
1. Rename the occurrence in the L90 sentence ("... or `rag_service_url`. Those are owned by `config/rag_pipeline_mcp_server.toml` ...").
2. Rename the L93 bullet ("`rag_service_url` is not a key of `config/agent.toml`, and no production process sets it to a non-empty value ...").
3. Add a contrast paragraph (new) near those lines stating: `rag_query_service_url` selects query-path HTTP delegation (paired with `rag_auth_token` as the outbound Bearer token; default `None` = run in-process), while `rag_pipeline_service_url` is the ingestion-path callback URL read by the ingester from `config/ingester.toml` (live in the deployed config); the keys are independent and name-distinct by design (REQ-005, Assumptions pairing note).
4. Do not restate deployment facts beyond what the renamed L93 bullet already claims.
### Method
Two token renames plus a short (3-5 sentence) paragraph in the existing section voice; keep the page's negative-claim structure intact.
### Details
`rag_pipeline_service_url` mentions elsewhere on this page (the `config/ingester.toml` section) stay byte-identical.

## Compatibility considerations
- The rename is repo-internal: no repo or deployed config file references the old spelling (verified 2026-10-27 across `config/` and `/opt/llm/config/`), so no external consumer is affected (REQ-006, Plan Design).
- `rag_query_service_url` collides with no existing identifier; the only `rag_query*` names in the repo are the unrelated `rag_query_id` log context key and `rag_query_count` session stat (Plan Assumptions, verified).

## Security considerations
- No security surface change. With an unrecognized key the loader keeps the `None` default, which means "no HTTP delegation" — the fail-safe direction (Plan Design). `rag_auth_token` pairing semantics are unchanged.

## Rollback considerations
- Single atomic rename commit; rollback is `git revert` of that commit. No data migration, no config-file change, and no deployed-state change means revert is complete on its own.

## Validation plan
- `rules/toolchain.md` documentation consistency check for the 21_rag domain passes; the contrast paragraph is present (AC-5).
- `uv run python -c "import subprocess,sys; sys.exit(0 if not subprocess.run([ 'grep','-rn','rag_service_url','scripts/','tests/','docs/','--include=*.py','--include=*.md'], capture_output=True).stdout.replace(b'rag_pipeline_service_url', b'') else 1)"`-style exhaustiveness check: `grep -rn "rag_service_url" scripts/ tests/ docs/ | grep -v "rag_pipeline_service_url"` returns zero matches outside the single ADR rename note (AC-1, AC-5).

## Completion criteria
- Page names only `rag_query_service_url` for the query key; contrast paragraph present; `rag_pipeline_service_url` sections untouched.

## Out of Scope
- Renaming `rag_pipeline_service_url` or editing `config/ingester.toml` / `/opt/llm/config/ingester.toml` (REQ-003).
- Backward-compat alias or mapping for the old spelling (Plan Design: no consumer exists).
- Renaming `rag_auth_token` or any other RAG config field.
- Changes to which path reads which key, defaults, or delegation semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154425
- **Related target files**: docs/21_rag/rag_05_01-configuration-reference.md
