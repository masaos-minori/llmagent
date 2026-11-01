# Scan indirect consumers of a change before the Plan is frozen

## Priority
High

## Summary
Add a consumer-scan step to `issue-to-plan` for changes to persisted schema, public APIs, or shared constants, backed by a new read-only tool that lists the direct and indirect consumers of the change (tests, inventories, pinned constants, mocks, deploy scripts, ADR citations). The aim is a complete `Implementation Target Files` table at freeze time, instead of target files discovered one by one during implementation.

## Background
- `Operationally observed` (session of 2026-10-30, plans `dbmig001`, `wftaskapi001`, `wfrecovery001`): three Frozen Plans were amended after freeze because a file outside the table had to change. Each amendment needed a Plan edit, a re-freeze, a new procedure document, and a user approval:
  - `tools/check_db_separation.py` — its `TABLE_OWNERSHIP` inventory rejected the new `schema_migrations` table.
  - `tests/deploy/test_init_db_eventbus_schema.py` — its sandbox config pinned `workflow_db_path` inside a TOML table, so the `create_schema.py` subprocess reached the production database and failed after the schema version bump.
  - `tests/integration/test_orchestrator_integration.py` — seven failures: mocked tasks had no status and a mocked engine returned a `MagicMock` attempt number.
- `Explicit in code`: `skills/plan-to-implementation-procedure/workflow.md` Step 3c ends a cycle `Blocked: additional target file discovered` when a row needs a file outside the table; `skills/issue-to-plan/workflow.md` verifies the files, symbols, and line numbers the issue names, but no step enumerates indirect consumers.
- `Operationally observed`: every one of the three omissions was found only by a full-suite run (about 7 to 8 minutes each) or by a pre-commit hook, never during planning.
- Related closed work: `issues/done/20261024-185427_perf001_cut-redundant-rereads-and-turn-overhead.md` and the other `perf` issues reduced planning cost; none addresses completeness of the target list.

## Problem
A Frozen Plan's target table is the only scope the later phases may touch. When it omits an indirect consumer, the implementation cycle stops, the Plan is amended, and the work waits for approval, while the cause (a consumer the author could not see by name) was knowable at planning time with a search.

## Reason for Change
Schema, DDL, and public-API changes are the most common change class in this repository, and each one has the same blind spot. The cost was three amendments in one release; it will recur with every persisted-state Plan, including the ones already queued (`toolexec001`, `wflease001`, `dlqbox001`).

## Implementation Intent
Treat consumer discovery as a planning step with a tool, not as the author's memory. The tool takes "change seeds" (a symbol, a column or table name, a constant, or a file) and reports candidate consumers by category: direct textual references, files that patch or mock the module containing the seed, inventory-style checkers and pinned constants (for example table inventories, size ceilings, ADR test citations), deploy scripts, and documents. It is heuristic and read-only; its output is a candidate list that the Plan author classifies as a target row, a reference row, or "not affected" with a reason, never a verdict. One candidate source to evaluate is the `pytest-testmon` dependency data, which records which tests execute which source files and would expose mock-based consumers that a text search cannot see.

## Target Files or Areas
- `tools/scan_change_consumers.py` (new)
- `tests/tools/test_scan_change_consumers.py` (new)
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/issue-to-plan/workflow.md` (a step for changes to persisted schema, public API, or shared constants)
- `templates/plan.md` (the notes on filling `Implementation Target Files`)
- `routing.md` (the "When to run which tool" table)

## Required Changes
- Add the tool with seeds as arguments and a categorized candidate report as output (plain text and JSON).
- Cover these candidate categories at least: direct references in `scripts/`, `tests/`, `tools/`, `deploy/`, `docs/`; tests that patch or import the seed's module; inventory-style checkers and pinned constants; ADR citations of tests.
- Evaluate `.testmondata` as an additional source of "tests that execute this file"; use it only if it is available and fresh, and say so in the output when it is not.
- Add a step to `issue-to-plan` that runs the tool for the change classes above and requires each candidate to be recorded as a target row, a reference row, or a stated "not affected" reason.
- Register the tool in `tools/TOOL_DESCRIPTIONS.md` and `routing.md`.

## Constraints
- Read-only; no network access; no writes outside stdout and an optional report path.
- Heuristic output must be labeled as candidates; a missing consumer is not evidence of absence.
- The tool must finish in a time that does not slow planning noticeably (target: under 30 seconds on this repository; `Needs confirmation`).
- Follow `routing.md` "Adding a new tool" validation for a new `tools/*.py` file.

## Acceptance Criteria
- Run against fixture trees in `tests/tools/`, the tool reports each category for a seed that appears in that category and nothing for an unrelated seed.
- Run against the live repository with the seeds `workflow_schema_version`, `WORKFLOW_SCHEMA_VERSION`, and `begin_stage_if_new`, the report lists the three files named in Background that this seed set can reach, and the issue records which of the three were not found and why (recall is reported, not assumed).
- `skills/issue-to-plan/workflow.md` contains the step, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- `check_tool_descriptions_sync.py` passes with the new tool registered.

## Testing Expectations
- Unit tests over temporary directory trees for each candidate category, including the "tool unavailable or data stale" path.
- A manual smoke run on the live repository with the seeds above, with the result recorded in the implementing change.
- `uv run ruff`, `uv run mypy <tool path>`, and `uv run bandit <tool path>` per "Adding a new tool".

## Documentation Impact
Yes. `skills/issue-to-plan/workflow.md` and `templates/plan.md` state the new step and its record format; `tools/TOOL_DESCRIPTIONS.md` and `routing.md` list the tool. Document intent and failure behavior (heuristic, candidates only), not implementation detail.

## Out of Scope
- Changing the Plan Freeze rules, or making the scan a blocking gate.
- Detecting consumers by running the test suite during planning.
- Dependency ordering between Plans and the release-unit concept (separate issues).

## Dependencies
N/A: none. No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30). Related, filed together: `issues/20261030-191057_flowimp002_plan-release-units.md`.

## Unresolved Questions
- `不明`: whether `.testmondata` is reliable enough as a source. The local file exists (ignored by git) but was last updated on 2026-10-25; how it is refreshed in a normal workflow is not confirmed.
- `不明`: how much of the mock-based case (a test builds a `MagicMock` of a changed object) a text search can catch without the testmon data.
- Assumption: recall on the three historical omissions can be measured after the fact and is an acceptable quality bar for a heuristic tool.

## AI Implementation Instruction
Implement the tool and the skill step only. Do not change Plan Freeze semantics or any existing checker. Keep the tool read-only and label every result as a candidate. If a category cannot be detected reliably, report that limit in the tool output rather than guessing. Stop and report if the testmon data cannot be used safely.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191006
- **Related target files**: `tools/scan_change_consumers.py`, `tests/tools/test_scan_change_consumers.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/issue-to-plan/workflow.md`, `templates/plan.md`, `routing.md`
