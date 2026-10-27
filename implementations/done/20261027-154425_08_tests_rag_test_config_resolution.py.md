# Implementation Procedure: Rename key fixtures and add the new-key-resolves / old-key-ignored regression test

## Goal
Rename existing key fixtures and add the Plan's new test pinning the contract: `{"rag_query_service_url": ...}` resolves, and the old spelling `{"rag_service_url": ...}` is ignored (stays `None`) (REQ-004, AC-2).

## Scope
- Fixture renames in existing tests plus one new test function. Assertion logic otherwise unchanged.

## Assumptions
- Mechanical rename only: every edit is a whole-word substitution of `rag_service_url` to `rag_query_service_url`; no semantics, defaults, or reader logic change (Plan Design).
- `rag_pipeline_service_url` occurrences are a superset substring of the old key; every validation grep excludes it (`grep -v rag_pipeline_service_url`) so ingestion-path text is never touched (REQ-003).
- Rebase immediately before implementing: the sibling rag001 Plan procedures (implementations/20261027-131124_*) touch `tests/rag/test_rag_pipeline.py` and `tests/rag/test_augment_refiner.py`, and the rag002 Plan procedures (implementations/20261027-144351_*) touch `docs/21_rag/rag_05_01-configuration-reference.md` and `tests/rag/test_rag_pipeline.py`; edits are disjoint, whichever implements second rebases (Plan Dependencies).
- The old spelling being ignored is the documented extras-filter behavior (`_ALL_FIELDS` filter in `resolve_rag_config`); the new test converts it from implicit to pinned contract (Plan Design).

## Design decisions
- New test rather than modifying an existing one: the old spelling must stay asserted as ignored so a stray legacy key in any future config fails visibly (fail-safe `None` = no delegation) (Plan Assumptions).

## Alternatives considered
- Treat the old spelling as a config-dict input only in the one new test — everywhere else in tests/ the rename is complete (AC-1).
- Add a compat alias test asserting the old key still resolves — rejected: no alias exists by design.

## Implementation
### Target file
`tests/rag/test_config_resolution.py`
### Procedure
1. Rename fixture occurrences: the expected-dict entry `"rag_service_url": None` (verified at L29) and the construction kwarg `rag_service_url=None` (verified at L77).
2. Add a new test (new): `test_renamed_key_resolves_and_old_spelling_ignored` — resolve a config dict containing `{"rag_query_service_url": "http://x"}` and assert `rag_query_service_url == "http://x"` (AC-2).
3. In the same or a companion test case, resolve a config dict containing `{"rag_service_url": "http://x"}` and assert the resolved value stays `None` (old spelling ignored, AC-2).
### Method
Add one test function with two cases (new key resolves; old key ignored); rename the two fixture occurrences. Keep the file's existing helper/config-builder style.
### Details
- The new test depends on procedures _01/_02 landing first (declaration rename); it belongs to Plan Phase 3 after Phase 2.

## Compatibility considerations
- The rename is repo-internal: no repo or deployed config file references the old spelling (verified 2026-10-27 across `config/` and `/opt/llm/config/`), so no external consumer is affected (REQ-006, Plan Design).
- `rag_query_service_url` collides with no existing identifier; the only `rag_query*` names in the repo are the unrelated `rag_query_id` log context key and `rag_query_count` session stat (Plan Assumptions, verified).

## Security considerations
- No security surface change. With an unrecognized key the loader keeps the `None` default, which means "no HTTP delegation" — the fail-safe direction (Plan Design). `rag_auth_token` pairing semantics are unchanged.

## Rollback considerations
- Single atomic rename commit; rollback is `git revert` of that commit. No data migration, no config-file change, and no deployed-state change means revert is complete on its own.

## Validation plan
- `uv run pytest tests/rag/test_config_resolution.py` green including the new test.
- `uv run python -c "import subprocess,sys; sys.exit(0 if not subprocess.run([ 'grep','-rn','rag_service_url','scripts/','tests/','docs/','--include=*.py','--include=*.md'], capture_output=True).stdout.replace(b'rag_pipeline_service_url', b'') else 1)"`-style exhaustiveness check: `grep -rn "rag_service_url" scripts/ tests/ docs/ | grep -v "rag_pipeline_service_url"` returns zero matches outside the single ADR rename note (AC-1, AC-5).
- Full suite green.

## Completion criteria
- New test present and passing; no standalone old-spelling fixture references remain outside the new test's ignore-assertion input.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154425
- **Related target files**: tests/rag/test_config_resolution.py
