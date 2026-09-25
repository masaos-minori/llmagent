## Goal

Move `docs/databases/active_databases.md` into `docs/41_db/` using `git mv`, consolidating SQLite database layer documentation that is currently split across two locations (`docs/90_shared_04/05_*` and `docs/databases/`).

## Scope

- **In-Scope**: Moving exactly this one file via `git mv`; removing the empty `docs/databases/` directory after the move; verifying git history preservation through the move.
- **Out-of-Scope**: Moving any other DB-topic file (tracked by its own procedure document); renaming any file; changing `agent-docs-consistency.yml`'s pre-existing asymmetric coverage of `shared_04_*` vs `shared_05_*`; any content edit beyond what `docsreorg04` already covers.

## Assumptions

- `docsreorg01` and `docsreorg02` have landed before merging this move (confirmed via repository evidence).
- `docsreorg03`'s CI path filter update already points `.github/workflows/agent-docs-consistency.yml` at `docs/41_db/90_shared_04_*.md` (confirmed via repository evidence).
- The file exists at its current location (`docs/databases/active_databases.md`).
- The `docs/databases/` directory contains only this one file.

## Design decisions

- Use `git mv` exclusively — no manual copy/delete — to preserve git history through the rename.
- Destination directory `docs/41_db/` does not yet exist; `git mv` will create it implicitly.
- After moving the file, remove the now-empty `docs/databases/` directory.
- No filename change — only relocation.

## Alternatives considered

- Manual `cp` + `rm`: rejected because it breaks git history continuity (no single commit shows the rename relationship).
- Renaming the file during the move: rejected — out of scope per the Plan's explicit constraint ("do not rename any file").

## Implementation

### Target file

`docs/databases/active_databases.md` → `docs/41_db/active_databases.md`

### Procedure

1. Execute `git mv docs/databases/active_databases.md docs/41_db/`.
2. Remove the empty `docs/databases/` directory.
3. Verify the file appears under `docs/41_db/` and no longer exists at the old location.
4. Verify git history is preserved through the move.

### Method

Execute a single `git mv` command targeting this file, followed by removal of the empty parent directory.

### Details

```bash
git mv docs/databases/active_databases.md docs/41_db/
rmdir docs/databases  # Only if directory is empty
```

After execution:
- Confirm `docs/41_db/active_databases.md` exists.
- Confirm `docs/databases/active_databases.md` no longer exists.
- Confirm `docs/databases/` directory has been removed.

## Compatibility considerations

- `.github/workflows/agent-docs-consistency.yml` uses `docs/**/*.md` as its broadest trigger — this file is covered by that wildcard.
- Removing `docs/databases/` may affect any external references to this path.

## Security considerations

N/A: This is a pure documentation reorganization with no code changes.

## Rollback considerations

To rollback, execute `git revert <commit>` where `<commit>` is the merge commit that introduced this move. Alternatively, recreate `docs/databases/` and move the file back: `git mv docs/41_db/active_databases.md docs/databases/`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/41_db/active_databases.md | Integration: verify git history preserved through move | `git log --follow docs/41_db/active_databases.md` | Continuous history shown |
| docs/databases/ | Integration: verify directory removed | `ls docs/databases/` | Directory does not exist |

## Completion criteria

- File exists at `docs/41_db/active_databases.md`.
- File no longer exists at `docs/databases/active_databases.md`.
- `docs/databases/` directory has been removed.
- `git log --follow docs/41_db/active_databases.md` shows continuous history through the move.

## Out of scope

Moving any other DB-topic file (each tracked by its own procedure document); renaming any file; changing `agent-docs-consistency.yml`'s pre-existing asymmetric coverage of `shared_04_*` vs `shared_05_*`; any content edit beyond what `docsreorg04` already covers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move docs/databases/active_databases.md to docs/41_db/ | Completed | — | 20260925-105529 |  |
| 2 | Remove empty docs/databases/ directory | Completed | — | 20260925-105804 |  |
| 3 | Verify git history preserved through move | Completed | — | 20260925-105840 |  |

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
- **Requirement ID**: REQ-001 (move DB-topic file to correct destination)
- **Source issue**: issues/20260923-141205_docsreorg10_move-database-docs-into-new-db-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-070314_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-101817
- **Related target files**: docs/databases/active_databases.md