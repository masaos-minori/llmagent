## Goal
Make the shell package `__init__` load its submodules lazily so importing the package or running a server module with `python -m` executes the module once (`REQ-002`).

## Scope
- Replace the eager `from . import ... as ...` lines with a module-level `__getattr__` (new) that imports on demand (`server` -> `shell_server`).
- Keep `__all__` and the public alias names.

## Assumptions
- Tests and tools import aliases as `from mcp_servers.<pkg> import <alias>` or reach submodules through the import system; both keep working with a module `__getattr__` (new).
- The module is a few hundred bytes, so the module-size gate is not a concern.

## Design decisions
- Use a small `_ALIASES` (new) mapping and `importlib.import_module` so each alias loads its submodule only when first accessed, then cache it in module globals.
- Raise `AttributeError` for unknown names so `hasattr` and `from ... import` behave normally.

## Alternatives considered
- Remove the aliases: rejected, existing tests import them (for example `from mcp_servers.git import server`).

## Implementation
### Target file
`scripts/mcp_servers/shell/__init__.py`

### Procedure
1. Remove the eager submodule imports.
2. Add `_ALIASES` (new) mapping each alias name to its submodule name (`server` -> `shell_server`).
3. Add `__getattr__(name: str) -> ModuleType` (new): look up the alias, import `f"{__name__}.{target}"` with `importlib.import_module`, store it in `globals()[name]`, return it; otherwise raise `AttributeError`.
4. Keep the module docstring line exactly as it is: `tools/check_docstrings_baseline.txt` grandfathers this file as "missing separator", and changing it would make the baseline entry stale.

### Method
- Add `import importlib` and `from types import ModuleType` at the top; keep `from __future__ import annotations` where the file has it.

### Details
- Evidence: `scripts/mcp_servers/shell/__init__.py` currently imports its submodules eagerly; a probe counted two loads of the server config under `python -m` for git.
- Reference only: the sibling `__init__` rows of this Plan use the same pattern.

## Compatibility considerations
- Existing aliases keep working; the difference is that the submodule executes on first access instead of at package import.

## Security considerations
- Strengthens ADR-002 config isolation: a server process can no longer read another server's configuration, including its token and policy settings, through package imports or ahead of the restriction.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_config_isolation_import.py` (alias and single-execution tests, tracked in its own document).
- `uv run pytest tests/mcp_servers tests/agent tests/tools`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_docstrings.py`, `uv run python tools/check_module_size.py`, `lint-imports`.

## Completion criteria
- Importing the package does not execute any server module; each alias still resolves; `python -m` executes the server module once.

## Out of Scope
- Changing which names the package exports
- Server module contents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the lazy aliases per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_config_isolation_import.py`, tracked in its own document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (lazy package imports, single module execution)
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: scripts/mcp_servers/shell/__init__.py
