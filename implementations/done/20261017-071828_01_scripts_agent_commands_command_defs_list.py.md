## Goal

Remove the `/diff`, `/system`, and `/audit` `CommandDef` entries from
`scripts/agent/commands/command_defs_list.py` so dispatch no longer routes to them
(`REQ-001`, command-surface reduction).

## Scope

In scope: delete the three `CommandDef` entries (and any alias or alternate spelling)
from `_COMMANDS`. Out of scope: the handlers they own (`cmd_context.py`, `REQ-002`), the
`/audit` mixin module (`cmd_audit.py` + `registry.py`, `REQ-003`), the rejection tests
(`test_agent_cmd_context.py`, `REQ-006`), and documentation updates (`REQ-007`).

## Assumptions

- `_COMMANDS` is imported by `registry.py` and drives dispatch, so removing the entries
  stops routing to the three commands.
- The registry integrity check (every `_COMMANDS` entry must reference a known handler)
  requires the matching handlers to be removed together; order Phase 2 so the `CommandDef`
  and its handler land in the same change.
- `/workflow` has no `CommandDef` here (named by the source directive only), so there is
  nothing to remove for it.

## Design decisions

- **Delete the entries, do not gate them.** Remove the `CommandDef` dict literals wholesale
  rather than behind a flag or shim, so there is no runtime path to reach them (matches the
  plan's "delete over gate" intent and the goal's "no alias, shim, forwarding path, or
  hidden flag").
- **Leave the surrounding structure intact.** Only the three entries are removed; the rest
  of `_COMMANDS` and the module imports stay unchanged.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or flag; gating or aliasing is out of scope.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Confirm the three entries with `rg`: `name="/diff"` (L90), `name="/system"` (L167),
   `name="/audit"` (L230).
2. Check for any alias or alternate spelling of the three names in the same file; remove
   those too.
3. Delete each `CommandDef` entry (its full dict literal) from `_COMMANDS`.
4. Leave every other entry, the module imports, and the list container untouched.

### Method

Locate each `CommandDef` by its `name=` key and remove the enclosing dictionary literal,
preserving indentation and the surrounding list/dict syntax.

### Details

- `registry.py` imports `_COMMANDS` from this module (`from agent.commands.command_defs_list
  import _COMMANDS`); dispatch reads it, so removing the entries is sufficient to stop
  routing.
- The registry integrity check stays green only if the corresponding handlers are also
  removed — that is `cmd_context.py` (`_cmd_diff`/`_cmd_system`, `REQ-002`) and
  `cmd_audit.py` + `registry.py` (`_AuditMixin`, `REQ-003`). Land these together in Phase 2.
- `/workflow` has no entry here; skip it.

## Compatibility considerations

Removing the entries changes the CLI command surface: `/diff`, `/system`, `/audit` now fail
like any unknown command through the existing `repl.py` rejection path. No supported
production caller remains.

## Security considerations

`N/A`: removing command exposure reduces the CLI attack surface; no new secret, permission,
or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/agent/commands/test_agent_cmd_context.py` — the four rejection tests pass;
  deleted-command behavior is gone.
- `lint-imports` — no dangling reference to the removed entries.
- `ruff` / `mypy --no-namespace-packages scripts/` — clean.

## Completion criteria

No `name="/diff"`, `name="/system"`, or `name="/audit"` (nor any alias/spelling) remains in
the file, `_COMMANDS` is still a well-formed dict, and every other command entry is
unchanged.

## Out of scope

Handlers (`cmd_context.py`), the `/audit` mixin module (`cmd_audit.py`), `registry.py`
composition, tests, and documentation — each a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the `/diff`, `/system`, `/audit` `CommandDef` entries from `scripts/agent/commands/command_defs_list.py` (`REQ-001`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 2 | Drop deleted-handler tests; add the four rejection tests (`tests/agent/commands/test_agent_cmd_context.py`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-100006 | 20261017-100006 |  |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `scripts/agent/commands/command_defs_list.py`