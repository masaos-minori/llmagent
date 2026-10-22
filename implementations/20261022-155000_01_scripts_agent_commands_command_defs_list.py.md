## Goal

Show the permanent `md` alias in the `/session export` usage rendered by the registry: change the help line and the export `ArgSpec` token from `markdown|json` to `markdown|md|json` in `scripts/agent/commands/command_defs_list.py` (REQ-001; AC-1, AC-2).

## Scope

- Modify `scripts/agent/commands/command_defs_list.py` only.
- Change two text/spec copies: the `/session` help line and the export `ArgSpec` token.

## Assumptions

- The `ArgSpec` token string is rendered verbatim into the usage and compared with the document by the GV-023 command contract check, so the document must change in the same edit (separate row).
- Changing the token does not change `_session_export` behavior (`md` already selects the internal `md` format).

## Design decisions

- Replace the alternation token literally (`markdown|json` → `markdown|md|json`) rather than restructuring the spec, keeping the default unchanged.

## Alternatives considered

- Adding `md` as a separate documented option elsewhere — rejected: the token is a single alternation; inserting `md` in the middle keeps the registry, help, error usage, and document in one canonical form.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Update the `/session` help line to render `markdown|md|json`.
2. Update the export `ArgSpec` token to `markdown|md|json`.
3. Run the agent-domain contract check and the session tests.

### Method

- Line 107, the `/session` help line:

  ```
  " | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts|rag-rebuild-vec",
  ```

  →

  ```
  " | export markdown|md|json [file] | stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts|rag-rebuild-vec",
  ```

- Line 120, the export spec:

  ```python
  (ArgSpec("markdown|json", default="markdown"), ArgSpec("file")),
  ```

  →

  ```python
  (ArgSpec("markdown|md|json", default="markdown"), ArgSpec("file")),
  ```

### Details

- Evidence in-file: line 107 carries the help text `export markdown|json [file]`; line 120 carries `ArgSpec("markdown|json", default="markdown")`.
- REQ-001 requires four text copies total; this row covers the registry spec + help line. The docstring and validation-error copies live in `scripts/agent/commands/cmd_session.py` (separate row).

## Compatibility considerations

N/A: usage text and spec token only; `_session_export` behavior and supported formats are unchanged.

## Security considerations

N/A: no auth, authorization, or input-handling path is added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/commands/command_defs_list.py` | Static + unit | `uv run python tools/check_docs_consistency.py --domain agent`; `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` | No finding; export tests pass |
| AC-1 check | rg | `rg "markdown\|json" scripts/agent/commands` | No match |

## Completion criteria

The help line and export `ArgSpec` token both read `markdown|md|json`, `rg "markdown\|json" scripts/agent/commands` returns no match, and `check_docs_consistency.py --domain agent` plus the session export tests pass.

## Out of Scope

- Editing `cmd_session.py` docstrings/validation usage (separate row).
- Editing the command document (separate row).
- Changing the export behavior or supported formats.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the help line and export ArgSpec token to markdown|md|json | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (apply the `md` alias to the registry spec, help line, validation-error text, and docstring)
- **Source issue**: `issues/20261022-124244_aliasstatus_classify-session-export-alias-and-removed-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-131142_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-155000
- **Related target files**: `scripts/agent/commands/command_defs_list.py`
