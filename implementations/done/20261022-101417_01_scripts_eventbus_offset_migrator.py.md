## Goal
Delete the legacy offset import module `scripts/eventbus/offset_migrator.py` (REQ-001: delete the module; remove its import, re-export, and call in sibling procedures).

## Scope
- Delete the file. The re-export in `db.py` and the call in `app.py` are removed by their own procedures; this one is done last among the three so no import breaks.

## Assumptions
- The module defines only `migrate_legacy_offsets()` and has two importers, `scripts/eventbus/db.py` and the tests of the import (verified by search). Its only runtime dependency on the file-based store is `_sanitize_consumer_id` from `scripts/eventbus/offsets.py`, which stays.
- The deployed `offsets_dir` is empty (read-only check before deploy, Plan UNK-02).

## Design decisions
- Delete the file outright; no stub or compatibility shim.

## Alternatives considered
- Keeping the module as a one-off tool: rejected, the Issue forbids a replacement import or one-off tool.

## Implementation
### Target file
`scripts/eventbus/offset_migrator.py`

### Procedure
1. After the `db.py` and `app.py` procedures are applied, delete the file with `git rm scripts/eventbus/offset_migrator.py`.
2. Confirm `rg "offset_migrator|migrate_legacy_offsets" scripts` returns no match.

### Method
- Single-file deletion, which AGENTS.md permits without confirmation; stage via `git rm` so the deletion is recorded.

### Details
- Do not delete any offset file from any host.

## Compatibility considerations
No remaining runtime caller after the sibling procedures; the ADR text that names the module is handled by the owner decision (Plan UNK-01).

## Security considerations
N/A: removes a startup file-reading path.

## Rollback considerations
Revert the commit to restore the file.

## Validation plan
- `uv run pytest tests/eventbus -q`, then the full suite once.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` (confirm no stale baseline entry).

## Completion criteria
- The file no longer exists and nothing imports it.

## Out of Scope
- `scripts/eventbus/offsets.py`, `offsets_dir`, and any offset file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the module after its importers are updated | Completed | 20261022-114122 | 20261022-114122 | Changed: scripts/eventbus/offset_migrator.py (deleted) |
| 2 | Tests are covered by the test-file procedure | Completed | 20261022-114122 | 20261022-114122 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261022-114122 | 20261022-114122 | validated; full suite 9686 passed, 14 skipped; ruff, mypy, lint-imports, check_module_size pass; offset, resume, startup tests pass |
| 4 | Deploy step: read-only `offsets_dir` listing on the host, deploy, verify EventBus resume | Completed | 20261022-114122 | 20261022-122807 | Deploy to /opt/llm not performed: needs user confirmation deploy done 2026-10-22: stale binaries (agent, mcp_rag_pipeline, mcp_mdq) rebuilt; deploy.sh exit 0, DEPLOYED_REV written; no service was running (ports unused), so no restart; deployed code verified against copies of production DBs; mcp_rag_pipeline build-info is flagged dirty because another session modified tracked plan files during the build (no runtime file differed) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | Deploy to the production host `/opt/llm` modifies shared infrastructure and was not performed without the user's confirmation; the read-only `offsets_dir` listing of the host is also pending | Yes | 20261022-122807 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (delete the legacy offset import module)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: scripts/eventbus/offset_migrator.py