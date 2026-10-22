## Goal

Update the `/session export` usage form and prose in the command document to show `md` as a permanent short form of `markdown`, keeping the documented form in sync with the registry (GV-023) per `REQ-002`; `AC-2`.

## Scope

- Modify `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` only.
- Change one table usage form and one prose sentence; write current behavior only (no history note).

## Assumptions

- The GV-023 command contract check (`check_docs_consistency.py --domain agent`) compares the registry usage with the documented form in both directions, so this doc must change together with `command_defs_list.py` (separate row).

## Design decisions

- Change the table's `[markdown|json]` to `[markdown|md|json]` and restate the prose so `md` is described as a permanent short form of `markdown` (the alias is permanent by owner decision, so no deprecation wording).

## Alternatives considered

- Adding a separate note that `md` is an alias — rejected: the usage form should show it directly, and the prose should state permanence rather than hint at future change.

## Implementation

### Target file

`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

1. Update the export table row's usage form.
2. Restate the export prose to name `md` as a permanent short form of `markdown`.
3. Run the agent-domain contract check and the documentation checkers.

### Method

- Table row (line 41):

  ```
  | `/session export` | `/session export [markdown\|json] [file]` | Exports the current in-memory conversation history |
  ```

  →

  ```
  | `/session export` | `/session export [markdown\|md\|json] [file]` | Exports the current in-memory conversation history |
  ```

- Prose (line 43), the clause:

  > For `/session export`, the format defaults to Markdown (`md` is accepted as an alias for `markdown`)

  →

  > For `/session export`, the format defaults to Markdown (`md` is the permanent short form of `markdown`)

### Details

- Evidence in-file: line 41 table cell shows `[markdown\|json]`; line 43 prose says "`md` is accepted as an alias for `markdown`".
- REQ-002 requires the usage form AND prose to state `md`; both are on lines 41 and 43.

## Compatibility considerations

N/A: documentation-only; no runtime contract is affected. The registry spec must change in the same edit to keep the contract check passing (separate row).

## Security considerations

N/A: no auth, authorization, or input-handling path is described here.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Document | Static + contract | `uv run python tools/check_docs_consistency.py --domain agent`; `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | No finding |

## Completion criteria

The table usage form reads `[markdown\|md\|json]`, the prose names `md` as a permanent short form of `markdown`, `check_docs_consistency.py --domain agent` passes, and the documentation checkers pass.

## Out of Scope

- Editing any other command document.
- Changing the registry spec (separate row) or the export behavior (out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the export usage form and prose to state md as a permanent short form | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (apply the `md` decision to the command document; pass the agent-domain contract check)
- **Source issue**: `issues/20261022-124244_aliasstatus_classify-session-export-alias-and-removed-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-131142_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-155000
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
