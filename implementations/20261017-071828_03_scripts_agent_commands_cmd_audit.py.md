## Goal

Delete the `scripts/agent/commands/cmd_audit.py` module, which exists only to back the
removed `/audit` command (`REQ-003`, command-surface reduction).

## Scope

In scope: delete `scripts/agent/commands/cmd_audit.py`. Out of scope: the `CommandDef`
entry (`command_defs_list.py`, `REQ-001`), the `/diff`/`/system` handlers
(`cmd_context.py`, `REQ-002`), the `registry.py` import/composition/docstring removal for
`_AuditMixin` (`REQ-003`, separate document), the test deletion
(`test_cmd_audit.py`, `REQ-003`, separate document), and documentation (`REQ-007`).

## Assumptions

- `_AuditMixin` lives only in this module and exists solely to implement `/audit`.
- No other module imports from `cmd_audit.py` besides `registry.py` (which removes its own
  import in a sibling document).

## Design decisions

- **Whole-module deletion.** The module is a single self-contained mixin; deleting the file
  is one coherent removal rather than piecemeal edits.
- **Remove the wiring together with the module.** `registry.py` imports and composes
  `_AuditMixin`; both the module and its wiring must go in the same change so no dangling
  import survives.

## Alternatives considered

`N/A`: the goal mandates deletion with no shim or forwarding path; keeping an empty module
would contradict it.

## Implementation

### Target file

`scripts/agent/commands/cmd_audit.py`

### Procedure

1. Confirm the module exists and contains only `_AuditMixin` (`class _AuditMixin(MixinBase)`
   at L30) via `rg`.
2. Confirm nothing outside `registry.py` imports from `cmd_audit` (`rg cmd_audit scripts/`).
3. Delete the file (`git rm` / equivalent).

### Method

Delete the file from the working tree and stage the removal with git.

### Details

- `registry.py` L31 imports `_AuditMixin` and L55 composes it; that removal is a separate
  procedure document. Land both together so the registry integrity check never sees a
  missing import.
- Audit generation, persistence, and redaction (`audit_event_emitter.py`, `factory.py`) are
  out of scope and stay unchanged.

## Compatibility considerations

Removing the module removes `/audit` from the registry composition; `/audit` now fails like
an unknown command. Nothing else depends on the module.

## Security considerations

`N/A`: removing the audit-read command reduces REPL information exposure; no data path is
touched.

## Rollback considerations

`git restore --staged <file> && git checkout -- <file>` (or revert the commit) to recover
the file.

## Validation plan

- `lint-imports` — no dangling `from agent.commands.cmd_audit import`.
- `pytest` full suite — no missing-import failures from other test files.
- `ruff` / `mypy --no-namespace-packages scripts/` — clean.

## Completion criteria

`scripts/agent/commands/cmd_audit.py` no longer exists, `registry.py` no longer imports or
composes `_AuditMixin`, and no other file references the module.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `registry.py`
(`REQ-003`), `test_cmd_audit.py` (`REQ-003`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `scripts/agent/commands/cmd_audit.py` (`REQ-003`) | Pending | — | — | |
| 2 | Delete `tests/agent/commands/test_cmd_audit.py` (`REQ-003`) | Pending | — | — | |
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
- **Related target files**: `scripts/agent/commands/cmd_audit.py`
