## Goal

Update the three text copies of the `/session export` usage in `scripts/agent/commands/cmd_session.py` to list `markdown|md|json`: the `_session_export` docstring, the `_cmd_session` docstring, and the validation-error usage text (REQ-001; AC-1).

## Scope

- Modify `scripts/agent/commands/cmd_session.py` only.
- Change three usage strings; do not touch `_session_export` logic.

## Assumptions

- The three copies are pure descriptions of the same `markdown|json` usage that the registry spec (separate row) changes to `markdown|md|json`.

## Design decisions

- Replace each `markdown|json` occurrence with `markdown|md|json` so all four usage copies (registry spec, help, docstring x2, validation error) agree.

## Alternatives considered

- Leaving the docstrings as-is and deriving usage from the registry — rejected: these are independent literal copies that readers see directly.

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py`

### Procedure

1. Update the `_session_export` docstring usage line.
2. Update the `_cmd_session` docstring usage line.
3. Update the validation-error usage string.
4. Confirm `_session_export` logic still accepts `md` (it already does) and run the session tests.

### Method

- `_session_export` docstring (around line 163):

  ```
  Usage: /session export [markdown|json] [filename]
  ```

  →

  ```
  Usage: /session export [markdown|md|json] [filename]
  ```

- `_cmd_session` docstring (around line 181):

  ```
  | export markdown|json [file]
  ```

  →

  ```
  | export markdown|md|json [file]
  ```

- Validation-error usage string (around line 237):

  ```
  " | /session export markdown|json [file]"
  ```

  →

  ```
  " | /session export markdown|md|json [file]"
  ```

### Details

- Evidence in-file: line 163 (`Usage: /session export [markdown|json] [filename]`), line 181 (`| export markdown|json [file]`), line 237 (`" | /session export markdown|json [file]"`).
- `_session_export` already maps both `"markdown"` and `"md"` to the internal `"md"` format (lines 167-171); this row changes only the descriptive text, not that logic.

## Compatibility considerations

N/A: text only; export behavior and supported formats are unchanged.

## Security considerations

N/A: no auth, authorization, or input-handling path is added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_session.py` | Unit | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` | Export tests pass |
| AC-1 check | rg | `rg "markdown\|json" scripts/agent/commands` | No match |

## Completion criteria

All three usage strings read `markdown|md|json`, `rg "markdown\|json" scripts/agent/commands` returns no match, and the session export tests pass.

## Out of Scope

- Changing `_session_export` parsing/format logic.
- Editing the registry spec (separate row) or the command document (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the docstrings and validation-error usage to markdown|md|json | Pending | — | — | |
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
- **Related target files**: `scripts/agent/commands/cmd_session.py`
