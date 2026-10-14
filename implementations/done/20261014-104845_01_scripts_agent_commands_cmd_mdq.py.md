## Goal

Delete the `/mdq` handler module (REQ-001: remove the command).

## Scope

- Delete the file. Only this file; the registry import is removed by procedure 03.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Delete the whole module: `_parse_int_flag`, `_require_tools`, `_execute_mdq`, and the `_cmd_mdq*` handlers have no other caller (`rg` shows only `registry.py` and `test_cmd_registry_note_removal.py` import it).
- Apply together with procedures 02, 03, and 05 so no intermediate state imports a missing module.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/commands/cmd_mdq.py`

### Procedure

Delete `scripts/agent/commands/cmd_mdq.py` with `git rm`.

### Method

No code edit. Before deleting, confirm with `rg -n "cmd_mdq|_MdqMixin" scripts tests` that only procedures 03 and 05 still reference it.

### Details

`check_preflight()` keeps its other callers (`cmd_context.py`, `tool_runner.py`, `tool_approval.py`, `repository_gateway.py`), so the policy gate is unaffected.

## Compatibility considerations

Removes the `/mdq` REPL command; typing it prints the existing unknown-command warning (`scripts/agent/repl_input_loop.py`). No alias. The MDQ MCP tools stay reachable through the LLM tool path.

## Security considerations

Removes a second REPL path to `mdq-mcp`; `allowed_dirs` authorization on the server is unchanged.

## Rollback considerations

N/A: removal only, applied as one commit unit with procedures 01-15 (revert the commit)

## Validation plan

- `rg -n "cmd_mdq|_MdqMixin" scripts` has no match after procedures 01-03.
- `PYTHONPATH=scripts uv run python -c "import agent.commands.registry"` succeeds.

## Completion criteria

- `scripts/agent/commands/cmd_mdq.py` no longer exists.
- No import of it remains in `scripts/`.

## Out of scope

- Registry and CommandDef edits (procedures 02-03), tests, docs, and the MDQ MCP server.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the file | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: scripts/agent/commands/cmd_mdq.py