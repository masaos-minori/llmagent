# Implementation Procedure: Rename the `RagConfigImpl.rag_service_url` dataclass field

## Goal
Rename the `RagConfigImpl` dataclass field so the dataclass declaration matches the renamed config surface attribute `rag_query_service_url` (REQ-001).

## Scope
- One field rename in `RagConfigImpl`. No other field, default, or method changes.

## Assumptions
- Mechanical rename only: every edit is a whole-word substitution of `rag_service_url` to `rag_query_service_url`; no semantics, defaults, or reader logic change (Plan Design).
- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text is never touched (REQ-003).
- Rebase immediately before implementing: the sibling rag001 Plan procedures (implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures (implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second rebases (Plan Dependencies).

## Design decisions
- Field name mirrors the protocol attribute renamed in `scripts/shared/types.py` (procedure _03) and the `_ALL_FIELDS` entry renamed in `scripts/rag/config_resolution.py` (procedure _01); mypy checks the three-line rename as one contract (Plan Validation plan).

## Alternatives considered
- Keep an alias mapping `rag_service_url` -> `rag_query_service_url` — rejected: zero consumers exist (verified inventory), and an alias re-introduces the ambiguity the rename removes (Plan Design).
- Rename the ingestion key instead — rejected: it is live in `config/ingester.toml` and `/opt/llm/config/ingester.toml` (Plan Design).

## Implementation
### Target file
`scripts/rag/models_config.py`
### Procedure
1. Rename the dataclass field `rag_service_url: str` (verified at L26) to `rag_query_service_url: str`.
2. `RagConfigImpl` is constructed from keyword arguments in `resolve_rag_config` (config_resolution.py); the rename lands together with procedure _01 so the two files must be committed in the same change.
### Method
Whole-word substitution of `rag_service_url` restricted to occurrences NOT part of `rag_pipeline_service_url` (the ingestion key is a superset substring — verify each match or use `grep -v rag_pipeline_service_url`), followed by the exhaustiveness grep.
### Details
- The dataclass is built by keyword from the filtered config dict; no positional construction depends on the name.

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

## Completion criteria
- L26 declares `rag_query_service_url: str`; mypy reports no attribute mismatch; full suite green.

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154425
- **Related target files**: scripts/rag/models_config.py
