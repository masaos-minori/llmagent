# Remove the dead repl_health compatibility shim

## Priority
Medium

## Summary
Remove `scripts/agent/repl_health.py` — the backward-compatibility re-export module that no code imports anymore — and clear its stale references in code comments and docs; alternatively record a documented retention decision if the user keeps it. Review finding F-003.

## Background
`scripts/agent/repl_health.py` was kept as a re-export shim when the health-check functions were extracted into `agent/services/` (archived issue `issues/done/20260831-152636_refactor_004_repl_health_separation.md`) to keep `agent.startup`'s old import path working. Verified at head `2e87bad46`: no module under `scripts/` or `tests/` imports `agent.repl_health`, and the deployed copy under `/opt/llm/scripts` contains no importer either — only its own file and docstring mentions in other modules. The shim re-exports private symbols (`_probe_mcp_health_detail`, `_validate_tools_response`, `_collect_server_tool_names`, `_check_tool_definitions`), keeping them a de facto public surface. A comment in `scripts/agent/config_dataclasses.py` still claims those shapes are "re-exported by agent/repl_health.py", and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` lists `repl_health` as a keyword. Confirmed by review (python-code-review finding F-003, High confidence; absence verified by grep over `scripts/`, `tests/`, and the deployed tree).

## Problem
A shipped module with zero consumers keeps private functions importable through a second path, and a code comment plus a docs keyword assert a live relationship that no longer exists.

## Reason for Change
Dead module cost: every health-check refactor must now keep the shim consistent for no consumer, and the stale comment misleads implementers about where these functions live.

## Implementation Intent
Delete the shim module outright (its sole purpose — a transitional import path — has expired), and correct the two stale references. No logic moves: the real implementations already live in `agent/services/`. If an external consumer is found that still needs the path, keep the module and document the retention reason instead.

## Target Files or Areas
- `scripts/agent/repl_health.py` (delete)
- `scripts/agent/config_dataclasses.py` (stale comment referencing the shim)
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` (keyword list entry)

## Required Changes
- Re-confirm zero importers of `agent.repl_health` in `scripts/`, `tests/`, and the deployed tree before deleting.
- Delete `scripts/agent/repl_health.py`.
- Update the `config_dataclasses.py` comment so it describes the actual services modules.
- Remove the `repl_health` keyword from the mcp startup-modes doc; run the docs checkers.

## Constraints
- No changes to `agent/services/` function signatures or behavior.
- Deletion only after the importer re-check passes; if any importer is found, switch to the retain-and-document outcome and report.

## Acceptance Criteria
- `scripts/agent/repl_health.py` no longer exists (or a documented retention decision is recorded instead).
- `rg 'agent\.repl_health'` finds no remaining references under `scripts/` and `tests/`; docs references updated.
- ruff, mypy, lint-imports, docs checkers, and the full test suite pass.

## Testing Expectations
- Full test suite (no test imports the shim; a suite Pass proves no hidden importer).
- `lint-imports` contracts: still all kept.
- `check_docs_structure` / reference-table checkers Pass after the docs keyword update.

## Documentation Impact
Update `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` (remove the stale keyword) and any doc that presents `repl_health` as an active import path. Record the removal decision (intent: transitional path expired) in the affected doc's change context only if that doc describes the module.

## Out of Scope
- The health-check functions themselves in `agent/services/`.
- Renaming or reorganizing `agent/services/` modules.

## Dependencies
- `issues/done/20260831-152636_refactor_004_repl_health_separation.md` — depends on (archived): the refactor that created the services modules and left this shim; re-verify importer absence against current source after any later services refactor.

## Unresolved Questions
- Whether any deployed external script, cron job, or ops tool imports `agent.repl_health` at runtime (repo and deployed-copy checks found none; a running-environment check beyond static grep is `Needs confirmation`).

## AI Implementation Instruction
Run the importer re-check first; only delete on a clean result. Keep the docs and comment edits minimal and consistent with `skills/DESIGN.md` docs policy. Report any importer found instead of adapting the shim.

## Traceability
- **Workflow phase**: python-code-review (finding F-003)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-210146
- **Related target files**: `scripts/agent/repl_health.py`, `scripts/agent/config_dataclasses.py`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
