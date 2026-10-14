## Goal

Remove the `/skill` command handler module (REQ-001: remove the command).

## Scope

- Delete the file. Only this file; the registry import is removed by procedure 03.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Delete the whole module: `_SkillMixin` and `_skills_dir` have no other caller (`rg` shows `registry.py:43` as the only importer).
- Apply together with procedures 02 and 03 so no intermediate state imports a missing module.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`scripts/agent/commands/cmd_skill.py`

### Procedure

Delete `scripts/agent/commands/cmd_skill.py` with `git rm`.

### Method

No code edit. Confirm with `rg -n "cmd_skill|_SkillMixin" scripts` that only `registry.py` (procedure 03) and this file still match before deleting.

### Details

The module comment at lines 50-58 documents the clearing behavior; it disappears with the file.

## Compatibility considerations

Removes the `/skill` REPL command; typing it prints the existing unknown-command warning (`scripts/agent/repl_input_loop.py`). No alias.

## Security considerations

Removes a path that appended unfiltered arguments to a system-role message.

## Rollback considerations

N/A: revert the commit; apply procedures 01-06 and 07-11 as one commit unit

## Validation plan

- `rg -n "cmd_skill|_SkillMixin" scripts` has no match after procedures 01-03.
- `uv run python -c "import agent.commands.registry"` with `PYTHONPATH=scripts` succeeds.

## Completion criteria

- `scripts/agent/commands/cmd_skill.py` no longer exists.
- No import of it remains in `scripts/`.

## Out of scope

- Registry edits (procedure 03), test edits, doc edits, `skills/` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the file | Completed | 20261014-094631 | 20261014-094631 |  |
| 2 | Run the tests that cover this file (updated by procedures 07-11) | Completed | 20261014-094631 | 20261014-094631 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-094631 | 20261014-094631 |  |

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
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: scripts/agent/commands/cmd_skill.py