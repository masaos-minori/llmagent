## Goal
- `REQ-004`: the `/memory` registry entry renders exactly the documented usages so `GV-023` can compare it with the chapter.

## Scope
- The `/memory` `CommandDef` in `scripts/agent/commands/command_defs_list.py` only (its `help` text and the `SubcommandSpec` arguments of `list`, `pin`, `unpin`, `delete`, and `prune`).

## Assumptions
- `ArgSpec.render()` shows `<token>` for a required argument and `[token]` for an optional one; `format_usage` joins command, subcommand, and arguments (`command_defs.py`).
- A default declared on an `ArgSpec` must be stated next to its usage in the chapter (`check_command_contracts`).
- The chapter is the normative contract (Plan decision); its notation for `rebuild` and `unpin` is adjusted in the docs row, not here.

## Design decisions
- Arguments of `list`: `ArgSpec("n", default="20")`, `ArgSpec("--type semantic|episodic")`, `ArgSpec("--pinned")`, `ArgSpec("--query <text>")`.
- `pin`, `unpin`, and `delete` use `ArgSpec("memory_id", required=True)`; `prune` uses `ArgSpec("--days <n>")`.
- `status`, `reindex`, and `rebuild` stay as they are (`rebuild` renders `[--confirm] [--allow-loss]`).

## Alternatives considered
Rendering `rebuild` as the nested documented form: rejected because `ArgSpec` renders flat tokens; the chapter adopts the flat form instead.

## Implementation
### Target file
`scripts/agent/commands/command_defs_list.py`

### Procedure
- In the `/memory` `CommandDef`, replace the `list` arguments, the `pin`, `unpin`, and `delete` argument tokens, and the `prune` argument as designed; keep descriptions short and accurate (for example `list`: "List entries"; `prune`: "Delete old entries after confirmation").
- Leave the `help` string unless it names a removed subcommand (it lists `status|list|delete|pin|unpin|prune|reindex|rebuild`, which stays correct).

### Method
- Edit only the `/memory` block; keep the surrounding `CommandDef` entries and imports unchanged.

### Details
- After the edit, `CommandDef.usages()` for `/memory` must equal: `status`, `list [n] [--type semantic|episodic] [--pinned] [--query <text>]`, `pin <memory_id>`, `unpin <memory_id>`, `delete <memory_id>`, `prune [--days <n>]`, `reindex [--fts|--vec]`, `rebuild [--confirm] [--allow-loss]` (each prefixed with `/memory`); print them from the registry to confirm.
- This file has high churn (7 commits in 30 days); keep the diff to the `/memory` block.

## Compatibility considerations
- The registry feeds help and the contract check; removing `--source`, `--branch`, and `[limit]` from the declared `list` arguments follows the handler change in the other row.

## Security considerations
N/A: declarative metadata only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands tests/tools/test_check_command_contracts.py -q`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`
- `uv run python tools/check_docs_consistency.py --domain agent` (run after the docs row; before it, expect findings only for the chapter notation)

## Completion criteria
- The rendered `/memory` usages equal the list in Details.
- Registry and command tests pass; lint, type, and architecture checks report no new findings.

## Out of scope
- The handler logic, the chapter text, the exemption table, and every other command's entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `/memory` arguments in the registry | Completed | 20261016-213747 | 20261016-213747 |  |
| 2 | Print the rendered usages and compare with the documented forms | Completed | 20261016-213747 | 20261016-213747 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-213747 | 20261016-213747 | ruff/mypy/lint-imports/command-registry tests pass; usage matches documented forms. 3 test_memory_data_ops failures are pre-existing (row 01 impl) and owned by row 03. |

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
- **Requirement ID**: REQ-004 (registry usages match the documented forms)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: scripts/agent/commands/command_defs_list.py