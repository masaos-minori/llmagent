## Goal

Remove the "console script `check-tool-descriptions`" / "console script
`check-needs-confirmation`" caller mentions from `tools/TOOL_DESCRIPTIONS.md` so no
document names a console-script entry point that cannot run in this repository
(REQ-002 / AC-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The four console-script entry points declared in `pyproject.toml` cannot be imported
  (`[tool.setuptools.packages.find] where = ["scripts"]` leaves the root `tools/`
  non-installable), so the hyphenated names `check-tool-descriptions` /
  `check-needs-confirmation` are not runnable here.
- The real callers use the module/path form: the pre-commit hook invokes
  `check_tool_descriptions_sync.py` via `python -m tools.check_tool_descriptions_sync`,
  and CI (`governance-docs-consistency.yml`) invokes `check_needs_confirmation_inventory.py`
  via the path/module form. These callers stay documented.
- The three invocation forms (module, path, test import) remain accurate after the edit.

## Design decisions
- Drop only the un-runnable `console script <hyphenated-name>` phrase from each caller cell;
  keep the pre-commit hook and CI workflow caller names, which are the real, runnable callers.
- Do not add a new concrete `.py` name that `check_tool_descriptions_sync.py` would flag as
  an unindexed tool.

## Alternatives considered
- Rewriting the cells to show the module form as the primary caller: valid, but the cells
  describe *who calls* the tool, and the pre-commit hook / CI workflow already call it by
  module/path form elsewhere; removing the broken phrase is the minimal, accurate change.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
In the two caller cells that name a hyphenated console-script entry point, remove the
`console script <hyphenated-name>` phrase, keeping the runnable caller names.

### Method
Edit the two cells in place; do not touch any other cell or row.

### Details
Cell 1 — `check_tool_descriptions_sync.py` caller column (currently):
```
pre-commit hook, console script `check-tool-descriptions`: any non-zero is failure
```
Change to:
```
pre-commit hook: any non-zero is failure
```

Cell 2 — `check_needs_confirmation_inventory.py` caller column (currently):
```
governance-docs-consistency.yml step, console script `check-needs-confirmation`: any non-zero is failure
```
Change to:
```
governance-docs-consistency.yml step: any non-zero is failure
```

## Compatibility considerations
N/A: a caller-description cell edit; no tool behavior, config, or API changes.

## Security considerations
N/A: no security-relevant change; a documentation caller-reference correction.

## Rollback considerations
N/A: revert the commit that makes this edit.

## Validation plan
- Run `uv run python tools/check_tool_descriptions_sync.py` to confirm
  `tools/TOOL_DESCRIPTIONS.md` still cross-checks cleanly (no unindexed `.py` reference
  remains and none was introduced).
- Confirm no `check-tool-descriptions` / `check-needs-confirmation` hyphenated entry-point
  name remains anywhere in the two edited cells.

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` no longer names `check-needs-confirmation` /
  `check-tool-descriptions` as runnable console scripts.
- The pre-commit hook and `governance-docs-consistency.yml` caller names remain in each cell.
- `check_tool_descriptions_sync.py` cross-checks cleanly.

## Out of Scope
- Changing `pyproject.toml` packaging or the `[project.scripts]` entries.
- Editing documents beyond `tools/TOOL_DESCRIPTIONS.md`.
- Changing any tool's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the un-runnable console-script caller mentions from `tools/TOOL_DESCRIPTIONS.md` (REQ-002) | Completed | — | 20261107-181917 |  |
| 2 | Add or update tests per Validation plan | N/A: docs-only, no tests | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261107-181917 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: this document is the documentation change | — | — |  |

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
- **Requirement ID**: `REQ-002` — stop documenting the un-runnable console-script entry points
- **Source issue**: `issues/20261106-123523_consolescript001_console-scripts-cannot-import-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-174449_consolescript001_console-scripts-cannot-import-tools.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-180341
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`