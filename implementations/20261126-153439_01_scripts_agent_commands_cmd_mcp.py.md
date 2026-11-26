## Goal
- Make `agent.commands.cmd_mcp` importable again by deferring annotation evaluation (REQ-001), and add a guard test that imports every module under `scripts/agent/commands/` by name (REQ-002), so the 26 failed tests and 88 errors of the 2026-11-26 full run pass (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module header of `scripts/agent/commands/cmd_mcp.py` and the new guard test file.
- Out of scope: any `/mcp` behavior, the registry contents, and a wider import guard over `scripts/agent/`.

## Assumptions
- Verified in Step 3a (current source): `cmd_mcp.py` imports `RuntimeToolRegistry` only under `TYPE_CHECKING` (lines 35-36), has no `from __future__ import annotations`, and annotates `_write_tool_summary` (line 264) and `_write_tool_diagnostics` (line 356) with `RuntimeToolRegistry | None`; the file was last changed by `f0334b72f` (`git log -1 -- scripts/agent/commands/cmd_mcp.py`).
- Verified: nothing in the module reads annotations at run time (`rg "get_type_hints|pydantic|dataclass|__annotations__|inspect"` found no match), so lazy annotations do not change behavior (Plan decision D-1).
- Verified: the directory holds 26 module files, `scripts/agent/commands/__init__.py` imports nothing, and importing each `agent.commands.*` module one by one failed only for `cmd_mcp` and `registry`.
- Plan overlap check: no other Frozen Plan targets these files.
- The system default Python is 3.14 while `.venv`, CI, and `requires-python` use 3.13; run every command through `uv run` so the interpreter is the 3.13 one. Note the interpreter in the validation record (Plan UNK-02).

## Design decisions
- Use the future import, the convention of 19 sibling modules; the alternative (quoting the two annotations) stays available only if a run-time annotation reader appears.
- The guard builds its module list from file names and calls `importlib.import_module` inside each test, so a failing module is named in the test id and collection never imports the package.

## Alternatives considered
- Quote the two annotations: a smaller diff, but it leaves the module outside the directory's convention.
- Discover modules with `pkgutil`: rejected, it imports the package and a failing module would break collection.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
1. Write the guard test first (companion below) and run it; confirm the `cmd_mcp` case fails on the current code with the `NameError`.
2. Re-run the `rg` check for run-time annotation readers in `cmd_mcp.py`; stop and report if one exists.
3. Add `from __future__ import annotations` immediately after the module docstring, before `import logging`, with a blank line after it as the other modules do.
4. Run `uv run ruff format` and `uv run ruff check` on the file; if ruff then reports a rule about the now-redundant quotes or ordering, apply only that fix.

### Method
- The edit is one added line plus its blank line; no other line of the file changes.
- The `TYPE_CHECKING` import of `shared.runtime_tool_registry` stays as it is, so the module still does not import it at run time.

### Details
- Confirm afterwards that `import agent.commands.cmd_mcp` and `import agent.commands.registry` succeed (run from `scripts/` with `uv run python -c`).

### Companion test files
- `tests/agent/commands/test_command_modules_import.py` (new)
  - Procedure: create the module with a docstring in the repository test style; build the list of module names from `scripts/agent/commands/*.py` (the repository root from `Path(__file__).resolve().parents[3]`), skipping `__init__.py`; parametrize one test over the names with the module name as the test id; in the test call `importlib.import_module(f"agent.commands.{name}")`; add one test asserting the discovered list is not empty and contains `cmd_mcp` and `registry`.
  - Validation: `uv run pytest tests/agent/commands/test_command_modules_import.py` fails for `cmd_mcp` and `registry` before the fix and passes for all modules after it.

## Compatibility considerations
- No behavior change: the module's public names, the registry, and `/mcp` output are untouched; only annotation evaluation becomes lazy.

## Security considerations
- N/A: no input handling, credential, or network change.

## Rollback considerations
- N/A: revert the commit; the guard test and the future import revert together.

## Validation plan
- `uv run pytest tests/agent/commands/test_command_modules_import.py tests/agent/commands/test_cmd_mcp.py`; then `uv run pytest tests/agent/commands tests/agent/test_repl.py tests/agent/test_repl_error_handling.py tests/agent/test_repl_shutdown_machine.py tests/agent/test_mcp_health_posture.py tests/docs/test_command_docs_sync.py`.
- `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit scripts/agent/commands/cmd_mcp.py -c pyproject.toml`; `uv run python tools/generate_reference_table.py --check`.
- The full suite once and diff-cover per `rules/toolchain.md` section 7, then `rules/toolchain.md` completion checklist; compare the result with the 2026-11-26 failure list (26 failed, 88 errors).

## Completion criteria
- `import agent.commands.cmd_mcp` and `import agent.commands.registry` succeed under the `.venv` interpreter; `shared.runtime_tool_registry` is still imported only under `TYPE_CHECKING`.
- The guard test passes for every module and was shown failing before the fix.
- The listed regression tests pass and the full suite shows no failure that the 2026-11-26 run did not show; all validation commands pass.

## Out of Scope
- `/mcp` behavior, a baseline mechanism for known test failures, a guard over other packages, and deployment (the user's decision, Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion guard test first, then confirm it fails before and passes after | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (importable module), `REQ-002` (guard test), `REQ-003` (failure set resolved)
- **Source issue**: issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152751_wfeff001_cmd-mcp-import-nameerror.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-153439
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/test_command_modules_import.py`
