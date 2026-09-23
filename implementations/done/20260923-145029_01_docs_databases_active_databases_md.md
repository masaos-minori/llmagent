# Implementation Procedure: active_databases.md

## Goal

Determine whether `docs/databases/active_databases.md` should remain in the repository and take appropriate action (keep or delete).

## Scope

- **In-Scope**: Evaluating `docs/databases/active_databases.md` existence, deciding keep or delete, applying the decision
- **Out-of-Scope**: Fixing broken references in other files pointing to this file, restructuring the databases/ directory, modifying any source code files

## Assumptions

- The file's content accurately reflects current database state (verified against config files in config/)
- No other process depends on this file being present in the repository

## Design decisions

- DOC-002 resolved the original structural concerns (Front Matter, H1 heading), so the file's structure is compliant
- The file contains substantive content documenting 5 production databases (rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite, mdq.sqlite)
- Git history confirms the file was intentionally included in DOC-002 governance effort rather than being an accidental orphan

## Alternatives considered

- Delete the file because it lacks clear ownership or active maintenance signal
- Keep the file without further changes since DOC-002 fixed its structural issues

## Implementation

### Target file

`docs/databases/active_databases.md`

### Procedure

KEEP the file as-is. No modifications needed.

### Method

The file serves a legitimate purpose as a cross-reference for all active SQLite databases. Its content is substantively correct and was intentionally maintained during DOC-002 work.

### Details

1. Verify file exists and has valid content (REQ-001; docs/databases/active_databases.md)
   - Read `docs/databases/active_databases.md` to confirm it exists and has Front Matter + H1 heading
   - Confirm it documents 5 production databases: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite, mdq.sqlite
   - Cross-reference database paths against config files:
     - `config/rag_pipeline_mcp_server.toml` for rag_db_path
     - `config/agent.toml` for session_db_path, workflow_db_path
     - `config/eventbus.toml` for eventbus_db_path
     - `config/mdq_mcp_server.toml` for db_path
2. Review git history for deletion intent (REQ-002; docs/databases/active_databases.md)
   - Run `git log --oneline docs/databases/active_databases.md` to confirm last modification during DOC-002 era
   - Confirm no deletion intent in commit messages
3. Make keep/delete decision based on content value (REQ-003; docs/databases/active_databases.md)
   - Decision: KEEP — file has substantive content serving as a cross-reference for active databases
4. If deleting: remove file from repository (REQ-004; docs/databases/active_databases.md)
   - Not applicable — decision is to keep the file

## Compatibility considerations

- Keeping the file does not affect compatibility with existing documentation or tooling
- The file is referenced by `check_docs_structure.py` as part of the documentation inventory

## Security considerations

- No security impact — the file is documentation-only and contains no sensitive information

## Rollback considerations

- N/A: no changes are made to the file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/databases/active_databases.md | Structural validation | uv run python tools/check_docs_structure.py "docs/**/*.md" | Zero errors |

## Completion criteria

- Decision documented: keep or delete
- File remains in repository with no modifications
- Zero errors from `uv run python python tools/check_docs_structure.py "docs/**/*.md"` after verification

## Out of scope

- Updating the file's content if it becomes outdated relative to current database state
- Adding new databases to the file
- Restructuring the databases/ directory

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | No changes needed — decision is to keep the file |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A — no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | N/A — no changes to validate |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A — no documentation updates needed |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260923-015302_doc003_confirm-whether-active-databases-md-exists.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-142145_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-145029
- **Related target files**: docs/databases/active_databases.md
