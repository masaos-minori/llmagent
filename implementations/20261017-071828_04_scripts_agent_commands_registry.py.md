## Goal

Remove the `_AuditMixin` import, list composition, and docstring mention from
`scripts/agent/commands/registry.py` so the deleted `/audit` mixin is no longer wired in
(`REQ-003`, command-surface reduction).

## Scope

In scope: remove the `_AuditMixin` docstring mention (L17), the import (L31), and the list
composition entry (L55) from `scripts/agent/commands/registry.py`. Out of scope: deleting
`cmd_audit.py` itself (`REQ-003`, separate document), the `CommandDef` entries
(`command_defs_list.py`, `REQ-001`), the `/diff`/`/system` handlers (`cmd_context.py`,
`REQ-002`), and documentation (`REQ-007`).

## Assumptions

- `registry.py` is the single place that imports and composes `_AuditMixin`.
- Removing the mixin does not affect the registry integrity check on `_COMMANDS` (that check
  concerns command→handler links, not mixin composition).

## Design decisions

- **Remove all three references in one edit.** The docstring mention, the import line, and
  the composition entry are coupled; removing only some leaves a dangling import or a stale
  doc. Remove them together.
- **Preserve everything else.** Other mixins, the `_COMMANDS` import, and the rest of the
  module stay intact.

## Alternatives considered

`N/A`: leaving any reference would produce an unused import (lint failure) or a broken
composition; partial removal is not viable.

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Confirm the three references with `rg`: docstring mention (L17),
   `from agent.commands.cmd_audit import _AuditMixin` (L31), `_AuditMixin,` in the composed
   list (L55).
2. Remove the `cmd_audit.py / _AuditMixin / /audit` docstring mention (L17).
3. Delete the import line (L31).
4. Remove `_AuditMixin,` from the composed mixin list (L55), preserving the list syntax.

### Method

Delete each of the three lines/blocks as whole lines, preserving surrounding indentation
and list formatting.

### Details

- Do this in the same change as deleting `cmd_audit.py` (separate document) so no dangling
  import survives between the two.
- The registry integrity check (every `_COMMANDS` entry references a handler) is unaffected
  by mixin composition; keep it green by also completing the `command_defs_list.py` /
  `cmd_context.py` deletions.

## Compatibility considerations

Removing the mixin drops `/audit` from the registry composition; `/audit` now fails like an
unknown command. No other mixin or command is affected.

## Security considerations

`N/A`: no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `lint-imports` — no dangling `cmd_audit` import.
- `ruff check scripts/` — no unused-import findings.
- `pytest tests/agent/commands/test_agent_cmd_context.py` (registry integrity) + full suite.

## Completion criteria

`registry.py` no longer mentions, imports, or composes `_AuditMixin`, and every other
symbol in the module is unchanged.

## Out of scope

`cmd_audit.py` (`REQ-003`), `command_defs_list.py` (`REQ-001`), `cmd_context.py`
(`REQ-002`), tests, documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `_AuditMixin` import/composition/docstring from `scripts/agent/commands/registry.py` (`REQ-003`) | Pending | — | — | |
| 2 | Delete deleted-handler/audit tests (`test_agent_cmd_context.py`, `test_cmd_audit.py`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `scripts/agent/commands/registry.py`
