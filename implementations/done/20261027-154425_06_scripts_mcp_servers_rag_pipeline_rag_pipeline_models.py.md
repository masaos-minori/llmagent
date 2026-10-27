# Implementation Procedure: Rename the anti-loop pin keyword in `build_rag_cfg_adapter()`

## Goal
Rename the `rag_service_url=""` keyword pin so the HTTP-loop guard binds to the renamed field and still pins the value to `""` (REQ-002, REQ-006).

## Scope
- One keyword rename plus its inline comment. The pinned empty-string value and the adapter's other fields are unchanged.

## Assumptions
- Mechanical rename only: every edit is a whole-word substitution of `rag_service_url` to `rag_query_service_url`; no semantics, defaults, or reader logic change (Plan Design).
- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text is never touched (REQ-003).
- Rebase immediately before implementing: the sibling rag001 Plan procedures (implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures (implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second rebases (Plan Dependencies).

## Design decisions
- The pin is what guarantees the rag_pipeline MCP server never re-delegates (ADR-010 consequence); the keyword name must match the renamed dataclass field or construction fails at import/runtime — mypy and the adapter test catch either miss.

## Alternatives considered
- Keep an alias mapping `rag_service_url` -> `rag_query_service_url` — rejected: zero consumers exist (verified inventory), and an alias re-introduces the ambiguity the rename removes (Plan Design).
- Rename the ingestion key instead — rejected: it is live in `config/ingester.toml` and `/opt/llm/config/ingester.toml` (Plan Design).

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
### Procedure
1. Rename `rag_service_url="",  # prevent HTTP loop when augment() is called in-process` (verified at L171) to `rag_query_service_url="",  # ...` keeping the anti-loop comment.
2. Commit together with procedure _02 (dataclass field rename): the keyword binds to the dataclass parameter name.
### Method
Whole-word substitution of `rag_service_url` restricted to occurrences NOT part of `rag_pipeline_service_url` (the ingestion key is a superset substring — verify each match or use `grep -v rag_pipeline_service_url`), followed by the exhaustiveness grep.
### Details
- Adapter anti-loop assertions in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` (L37, L76-80, L119, L148 verified) are renamed by procedure _19.

## Compatibility considerations
- The rename is repo-internal: no repo or deployed config file references the old spelling (verified 2026-10-27 across `config/` and `/opt/llm/config/`), so no external consumer is affected (REQ-006, Plan Design).
- `rag_query_service_url` collides with no existing identifier; the only `rag_query*` names in the repo are the unrelated `rag_query_id` log context key and `rag_query_count` session stat (Plan Assumptions, verified).

## Security considerations
- No security surface change. With an unrecognized key the loader keeps the `None` default, which means "no HTTP delegation" — the fail-safe direction (Plan Design). `rag_auth_token` pairing semantics are unchanged.

## Rollback considerations
- Single atomic rename commit; rollback is `git revert` of that commit. No data migration, no config-file change, and no deployed-state change means revert is complete on its own.

## Validation plan
- `uv run python -c "import subprocess,sys; sys.exit(0 if not subprocess.run([ 'grep','-rn','rag_service_url','scripts/','tests/','docs/','--include=*.py','--include=*.md'], capture_output=True).stdout.replace(b'rag_pipeline_service_url', b'') else 1)"`-style exhaustiveness check: `grep -rn "rag_service_url" scripts/ tests/ docs/ | grep -v "rag_pipeline_service_url"` returns zero matches outside the single ADR rename note (AC-1, AC-5).
- `uv run mypy --no-namespace-packages scripts/` — protocol/dataclass rename type-checks across packages; MagicMock-based fixtures accept any attribute name, so mypy plus the grep are the safety net (Plan Risks).
- `uv run ruff check scripts/` and `PYTHONPATH=scripts uv run lint-imports` unchanged.
- `uv run pytest tests/` — full suite green with name-only test edits (AC-6).
- Adapter anti-loop test: `uv run pytest tests/mcp_servers/rag_pipeline/` green; the pin assertion `adapter.rag_query_service_url == ""` holds (AC-3).

## Completion criteria
- L171 pins `rag_query_service_url=""`; anti-loop assertions pass; full suite green.

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154425
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py
