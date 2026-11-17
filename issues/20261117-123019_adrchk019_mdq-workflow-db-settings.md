# Fix database connection settings for MDQ and workflow

## Priority
Medium

## Summary
MDQ never enables SQLite foreign keys, so cascade deletes do not run, and the workflow database path is hard-coded in Python instead of read from configuration.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M07`; merged from ADRCHK-M21, M22 (review findings N27, N40)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
MDQ connections call `apply_connection_pragmas(..., write_mode=False)` in `mdq_service.py` and `db_schema.py` (`Explicit in code`, confirmed by `rg`). Whether `foreign_keys=ON` is then never set is from the review. The workflow path claim is from the review.

## Reason for Change
- Foreign keys are off in MDQ: the `chunks ON DELETE CASCADE` defined in `db_schema.py` does not run, so deleting a document leaves orphan chunks and search returns content from deleted files.
- The workflow path is hard-coded: the default appears in both `DbConfig` and `build_db_config` in `scripts/db/config.py`, and `config/agent.toml` has no `workflow_db_path`. ADR-002 and ADR-008 say database paths come from configuration, and the manifest shows `in_agent_toml: false` for workflow.

## Implementation Intent
- Every MDQ connection enforces foreign keys.
- Every database path is read from configuration, with at most one default in code.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_service.py`
- `scripts/mcp_servers/mdq/db_schema.py`
- `scripts/mcp_servers/mdq/indexer.py`
- `scripts/db/config.py`
- `config/agent.toml`
- registry/manifests/db_schema_versions.yaml (regenerated)
- `tests/mcp_servers/mdq/`
- `tests/db/`

## Required Changes
- Write a test that deletes a document and expects its chunks to be removed; it must fail first.
- Enable `foreign_keys` on every MDQ connection, or use `write_mode=True` for write paths.
- Add `workflow_db_path` to `config/agent.toml`, and keep a single default, or none, in code.
- Regenerate the manifest.

## Constraints
- Check whether existing MDQ databases already contain orphan chunks and report the count; do not clean them up in this issue.
- Run `tools/check_db_separation.py` and `tools/generate_reference_table.py --check`; measure `DbConfig` blast radius with `rg` first.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- Deleting a document removes its chunks (test).
- The manifest shows `in_agent_toml: true` for workflow.

## Testing Expectations
Tests under `tests/mcp_servers/mdq/` and `tests/db/`, MDQ/RAG boundary test, ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes if config guides list database path keys: regenerate `deployment` reference tables.

## Out of Scope
- Cleaning existing orphan chunks.
- Schema or DDL changes.

## Dependencies
- N/A: none

## Unresolved Questions
- `scripts/mcp_servers/mdq/indexer.py` was not reviewed; how deletes are done is `Needs confirmation`.

## AI Implementation Instruction
- Report the orphan chunk count from existing databases; do not clean them up.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123019
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`; `scripts/mcp_servers/mdq/db_schema.py`; `scripts/mcp_servers/mdq/indexer.py`; `scripts/db/config.py`; `config/agent.toml`; `registry/manifests/db_schema_versions.yaml (regenerated)`; `tests/mcp_servers/mdq/`; `tests/db/`
