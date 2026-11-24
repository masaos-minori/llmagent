## Goal

Register the job commands as the single source of registered commands and completion candidates, and rename the RAG vector subcommand to the name that matches what it does (REQ-001: job commands exist as registered commands; REQ-007: name matches behavior; REQ-010: the registry is the source of truth for command lists).

## Scope
**Release unit**: R2-job-commands (Phase 2); the rename part is R6-rag-vector-contract (Phase 6)

- In scope: the `/jobs` `CommandDef` entries, the command contract entries, the `/session` `SubcommandSpec` name for the vector operation.
- Out of scope: the handler implementation (row 10), the completion set in `repl.py` (row 11), the Built-in Command Index document (row 24).

## Assumptions

- `/jobs` is a top-level command with `status <id>` and `cancel <id>` subcommands (plan decision OD-02, 2026-11-24).
- The retired `rag-rebuild-vec` name is not reintroduced as an alias; `tests/agent/commands/test_removed_commands.py` (row 50) asserts that.

## Design decisions

- The `CommandDef` entries carry the handler name of an existing mixin rather than introducing a new mixin, because the registry MRO counts are pinned by the consistency tests (rows 10, 41, 53, 56).

## Alternatives considered

- A new `*Mixin` class for the job commands — rejected: it would move the pinned counts 10 and 8 and change four tests that only need the handler path.

## Implementation
### Target file
`scripts/agent/commands/command_defs_list.py`

### Procedure
1. Add the `/jobs` `CommandDef` (`prefix=True`) with the `status` and `cancel` `SubcommandSpec` entries near the `/session` and `/memory` specs at `command_defs_list.py:102,160`.
2. Add the contract entries the checker requires for the new command.
3. Rename the vector `SubcommandSpec` name from `rag-rebuild-vec` to `rag-prune-vec` and keep `rag-rebuild-fts` unchanged.

### Method
- `handler` names an existing mixin method (`_cmd_jobs` (new)) that row 10 adds inside an existing mixin.

### Details
- `help` text names the subcommands only; it does not restate approval behavior.

### Companion test files
- `tests/agent/commands/test_command_defs.py`
  - Procedure: extend the `SubcommandSpec` expectations to `/jobs status` and `/jobs cancel`, and the RAG vector subcommand name.
  - Validation: `uv run pytest tests/agent/commands/test_command_defs.py -q` (AC-1, AC-7, AC-8).

## Compatibility considerations

- `check_command_coverage` requires the new command in the Built-in Command Index and a chapter; that document change is row 24 in the same unit.

## Security considerations

- The registered approval level for each operation is declared in the job record, not in the `CommandDef`; the definition only exposes the commands.

## Rollback considerations

- Revert the Phase 2 commit for the registration and the Phase 6 commit for the rename separately.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/command_defs_list.py` | Unit | `uv run pytest tests/agent/commands/test_command_defs.py tests/agent/commands/test_command_def_sync.py -q` | Job commands registered with their subcommands |
| Same file | Checker | `uv run python tools/check_docs_consistency.py` | Command coverage and contract pass with the new command |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/command_defs_list.py` | No finding |

## Completion criteria

- `/jobs`, `/jobs status <id>`, and `/jobs cancel <id>` are registered and completable, and the vector subcommand is registered only under `rag-prune-vec`.

## Out of Scope

- The handler body, the completion candidate set, the documentation rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register `/jobs` and its subcommands with contract entries | Completed | — | 20261124-165333 | Phase 2 Phase 2 part landed: /jobs CommandDef with status/cancel SubcommandSpec, required id argument, help naming both subcommands. The RAG vector rename is Phase 6. |
| 2 | Rename the RAG vector subcommand | Pending | — | — | Phase 6 |
| 3 | Update the companion test per Validation plan | In Progress | — | — | Row 40 is covered by this document Job-contract assertions landed in Phase 2 (test_command_defs.py); the renamed RAG vector subcommand assertion follows with step 2 in Phase 6. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-001 (job commands as registered commands), REQ-007 (name matching behavior), REQ-010 (registry as the source of command lists)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/command_defs_list.py`, `tests/agent/commands/test_command_defs.py`