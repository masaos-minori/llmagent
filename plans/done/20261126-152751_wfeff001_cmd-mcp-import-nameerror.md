## Goal
- Make `agent.commands.cmd_mcp` and `agent.commands.registry` importable again, and add a guard test that imports every module of `scripts/agent/commands/` so an import-time error in one command module names that module.

## Priority
High

## Scope
- **In-Scope**:
  - Defer the evaluation of the annotations in `scripts/agent/commands/cmd_mcp.py` with `from __future__ import annotations`, the pattern 19 of the 26 files in that directory already use.
  - A guard test, `tests/agent/commands/test_command_modules_import.py`, that imports each module of `scripts/agent/commands/` by name.
  - A verification that no other command module has the same defect (recorded in Background).
- **Out-of-Scope**:
  - Any behavior change of `/mcp` or of the command registry.
  - The known-failure baseline tool for test runs and other workflow tooling (separate issues of the same review).
  - A broader import guard over all of `scripts/agent/` (see UNK-03).
- **Dependencies**: N/A: none. The known-failure baseline issue of the same review is related (once this defect is fixed the current known-failure set is empty) but does not order this work.

## Background
- Source: the review of the issue-to-implementation flow, issue wfeff001. Step 2/3 adversarial verification against current source:
  - Confirmed: `import agent.commands.cmd_mcp` and `import agent.commands.registry` raise `NameError: name 'RuntimeToolRegistry' is not defined` under Python 3.13.5 (run from `scripts/`, checked in Step 2).
  - Cause: `scripts/agent/commands/cmd_mcp.py` imports `RuntimeToolRegistry` only under `TYPE_CHECKING` (lines 35-36), has no `from __future__ import annotations`, and annotates `_write_tool_summary` (line 264) and `_write_tool_diagnostics` (line 356) with `RuntimeToolRegistry | None`, which Python evaluates when the `def` runs.
  - The defect was introduced by commit `f0334b72f` (2026-11-25, staged reload transaction), which added the `TYPE_CHECKING` import and both annotations; `git diff f0334b72f HEAD` shows no later change to the file.
  - Runtime reach: `scripts/agent/commands/registry.py:36` imports `_McpMixin` at module level, and `scripts/agent/startup_component_init.py:108` imports `CommandRegistry` inside `initialize()` at run time, so Agent startup reaches the failing import (by reading; not run end to end).
  - Other modules: seven files in the directory lack the future import (`__init__.py`, `cmd_debug.py`, `cmd_mcp.py`, `cmd_rag_export.py`, `cmd_session.py`, `cmd_tooling.py`, `registry.py`); none except `cmd_mcp.py` uses `TYPE_CHECKING`, and importing every `agent.commands.*` module one by one failed only for `cmd_mcp` and `registry` (checked in Step 3). `scripts/agent/commands/__init__.py` imports nothing.
  - Test effect: the full run of 2026-11-26 showed 26 failed and 88 errors, all in `tests/agent/` and `tests/docs/test_command_docs_sync.py`, from this one error.
- The commit message of `f0334b72f` reports a green full suite and 100 percent diff coverage, while the failure reproduces on 3.13.5, the interpreter of `.venv`, CI (`python-version: '3.13'`), and `requires-python`. Why that gate was green is `不明` (UNK-02).

## Problem
- Importing the command registry fails, so the REPL command table cannot be built, and the failure leaves the full test suite permanently red, which hides new failures.

## Reason for Change
- Startup or correctness failure of the Agent plus a red suite. Time-sensitive: every full-suite run currently needs manual triage.

## Implementation Intent
- Use the sibling modules' mechanism (lazy annotations) so `/mcp status` behavior is untouched, and add a guard that turns any future import-time error in a command module into a failure that names the module.

## Requirements
- `REQ-001`: `scripts/agent/commands/cmd_mcp.py` MUST be importable, without importing `shared.runtime_tool_registry` at run time and without changing `/mcp` behavior.
- `REQ-002`: A test MUST import every module under `scripts/agent/commands/` by name and fail, naming the module, when one raises at import.
- `REQ-003`: The 26 failed tests and 88 errors of the 2026-11-26 full run MUST pass, with no other test newly failing.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/commands/cmd_mcp.py | Modify: add `from __future__ import annotations` after the module docstring | The two annotations that name `RuntimeToolRegistry` are evaluated at definition time and the name exists only under `TYPE_CHECKING` | REQ-001, REQ-003; AC-01, AC-03 | `cmd_mcp.py:35-36,264,356` and the NameError reproduction (checked in Step 2); `git show f0334b72f` (checked in Step 2) | `tests/agent/commands/test_command_modules_import.py` | Verified |
| tests/agent/commands/test_command_modules_import.py | Create: parametrized import guard over every module file of `scripts/agent/commands/` | No test names a command module when its import fails; discovery must not import the package | REQ-002; AC-02 | `tests/agent/commands/` exists; `scripts/agent/commands/__init__.py` imports nothing; 26 module files (checked in Step 3) | `tests/agent/commands/test_command_modules_import.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/commands/registry.py | Imports `_McpMixin` at module level (`:36`), which is how the failure reaches the registry | REQ-001 |
| scripts/agent/startup_component_init.py | Run-time import of `CommandRegistry` in `initialize()` (`:108`) | REQ-001 |
| scripts/agent/commands/__init__.py | Confirms the package imports nothing, so discovery can use file names | REQ-002 |
| tests/agent/commands/test_cmd_mcp.py | Existing `_McpMixin` tests that must keep passing | REQ-003 |

## Acceptance Criteria
- `AC-01` (REQ-001): `import agent.commands.cmd_mcp` and `import agent.commands.registry` succeed under the `.venv` interpreter (Python 3.13), and `shared.runtime_tool_registry` is still imported only under `TYPE_CHECKING`.
- `AC-02` (REQ-002): The guard test passes for all 26 module files and fails with the module name in its test id when a command module raises at import (shown once by reverting the fix locally).
- `AC-03` (REQ-003): `tests/agent/commands/`, `tests/agent/test_repl.py`, `tests/agent/test_repl_error_handling.py`, `tests/agent/test_repl_shutdown_machine.py`, `tests/agent/test_mcp_health_posture.py`, and `tests/docs/test_command_docs_sync.py` pass, and the full suite shows no failure that the 2026-11-26 run did not show.

## Tests
- T-01 (REQ-001, AC-01): the import commands above, and the existing `tests/agent/commands/test_cmd_mcp.py`.
- T-02 (REQ-002, AC-02): `uv run pytest tests/agent/commands/test_command_modules_import.py`; write it first and confirm it fails on the current code for `cmd_mcp`.
- T-03 (REQ-003, AC-03): the listed test files, then the full suite once with `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.
- Run ruff format and check, mypy (CI invocation), `lint-imports`, and bandit on the changed files.

## Documentation Impact
N/A: no `docs/*.md` file describes the import mechanism of this module.

## Assumptions
- `from __future__ import annotations` leaves the behavior of `_McpMixin` unchanged because no code reads its annotations at run time (no `get_type_hints`, pydantic, or dataclass use in the module); the implementation phase confirms this with `rg` before the edit.
- The guard enumerates module files with the file system, not with `pkgutil`, so a failing module cannot break test collection of the guard itself.
- Importing command modules in tests is safe: the other tests of the directory already do it under the isolation of `tests/conftest.py`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the deployed `/opt/llm` Agent runs a copy that contains commit `f0334b72f` | The deployed commit is not visible from the repository | Compare the deployed revision with `f0334b72f` before the next deployment; deploying the fix is the user's decision | False |
| UNK-02 | Why the gate of `f0334b72f` reported a green full suite while the import fails on Python 3.13.5 | No record of the interpreter used for that gate | Note the interpreter in the implementation procedure's validation; the system default is 3.14 (`uv python find` lists 3.13.5 and 3.14.8), where annotations are evaluated lazily, which would explain it (unverified) | False |
| UNK-03 | Whether other packages under `scripts/` have an import-time annotation defect of the same kind | Only `scripts/agent/commands/` was checked; importing all of `scripts/` has side effects (log files under `/opt/llm`) | A separate issue can add a guard for a wider scope if the owner wants it | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/commands/cmd_mcp.py | Modify | Medium (imported by the command registry at startup; no caller of its annotations) | 3 | 3 authors | not applicable (rsynced) |
| tests/agent/commands/test_command_modules_import.py | Create | Low | N/A (new) | N/A (new) | not applicable (rsynced) |

## Design
Path A (two files, no public or runtime interface change, no schema change). Baselines (checked in Step 5): `radon cc scripts/agent/commands/cmd_mcp.py -s -n C` reports no block of complexity C or worse; `bandit scripts/agent/commands/cmd_mcp.py` reports no finding (repository-wide `bandit` and `vulture` findings are pre-existing and outside the target); `cmd_mcp.py` is 15960 B, below the 24576 B module size gate and unchanged in size beyond one line. The diff-cover baseline is `N/A` for the new test and counts the one added import line, which runs on import.

Decisions:
- **D-1 Mechanism.** Add `from __future__ import annotations` to `cmd_mcp.py`. Alternative: quote the two annotations (a two-line change). Rejected as the default because 19 sibling modules use the future import, so the module then follows the directory's convention; the alternative stays valid if `rg` finds a run-time annotation reader.
- **D-2 Guard discovery.** Build the module list from `scripts/agent/commands/*.py` file names and call `importlib.import_module` inside each test, so the failure message names the module and collection never imports the package.

Consumer scan: no persisted schema, public API, or shared constant changes (`not applicable`). Predictable fallout check: module size gate `not affected`; pinned counts `not affected` (no inventory changes); tool inventory `not affected`; generated blocks: a source change under `scripts/agent/` triggers `uv run python tools/generate_reference_table.py --check`, which the implementation phase runs once (the API reference is generated from signatures and annotations are not rewritten by this change).

Persisted schema check: `not applicable`.

## Implementation steps
1. **Phase 1: Guard test first (REQ-002)**
   - [ ] Write `tests/agent/commands/test_command_modules_import.py` and confirm it fails for `cmd_mcp` on the current code (REQ-002; `tests/agent/commands/test_command_modules_import.py`)
2. **Phase 2: Fix the import (REQ-001, REQ-003)**
   - [ ] Confirm with `rg` that nothing reads the annotations of `cmd_mcp.py` at run time, then add the future import (REQ-001; `scripts/agent/commands/cmd_mcp.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Run the tests, the validators, and the full suite once as in the Tests section (REQ-001 to REQ-003; `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/test_command_modules_import.py`)
   - [ ] Hand off to `skills/deploy/SKILL.md` once the change is committed and pushed; deploying is the user's decision and has an approval gate. `scripts/` is rsynced and no config file changes, so `deploy.sh` needs no change; check UNK-01 before the restart (REQ-001; `scripts/agent/commands/cmd_mcp.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/commands/cmd_mcp.py | Import check and existing unit tests | `uv run pytest tests/agent/commands/test_cmd_mcp.py` | Pass |
| tests/agent/commands/test_command_modules_import.py | Guard over all command modules | `uv run pytest tests/agent/commands/test_command_modules_import.py` | Fails first on `cmd_mcp`, then passes |
| Affected tests of the 2026-11-26 failure set | Regression | `uv run pytest tests/agent/commands tests/agent/test_repl.py tests/agent/test_repl_error_handling.py tests/agent/test_repl_shutdown_machine.py tests/agent/test_mcp_health_posture.py tests/docs/test_command_docs_sync.py` | Pass |
| Changed Python | Format, lint, type, architecture, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `lint-imports`, `uv run bandit scripts/agent/commands/cmd_mcp.py -c pyproject.toml` | No new finding |
| Full suite and coverage | Regression | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No failure outside the 2026-11-26 set; the set is gone |

## Risks
- **Risk**: A run-time reader of the annotations (for example `get_type_hints`) changes behavior under lazy annotations (likelihood: low) → **Mitigation**: `rg` for annotation readers in the module before the edit; otherwise use the quoting alternative (D-1).
- **Risk**: The guard imports a module with an import-time side effect that is not isolated in tests (likelihood: low) → **Mitigation**: the other tests of the directory already import all of these modules under the conftest isolation; the guard adds no new import path.
- **Risk**: The full suite still shows a failure unrelated to this defect and is mistaken for a regression (likelihood: medium) → **Mitigation**: compare with the 2026-11-26 failure list recorded in Background and Acceptance AC-03.
- **Risk**: The fix reaches production only on deployment (likelihood: certain if the deployed copy has the defect) → **Mitigation**: the deploy hand-off step and UNK-01.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Guard test first | In Progress | — | — |  |
| 2 | Fix the import | In Progress | — | — |  |
| 3 | Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261126-153439_01_scripts_agent_commands_cmd_mcp.py.md | 1, 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261126-151436_wfeff001_cmd-mcp-import-nameerror.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-152751
- **Related target files**: scripts/agent/commands/cmd_mcp.py, tests/agent/commands/test_command_modules_import.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `cmd_mcp.py:35-36,264,356` | scripts/agent/commands/cmd_mcp.py | Phase 2 | AC-01 | T-01 | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 3 | tests/agent/commands/test_command_modules_import.py | Phase 1 | AC-02 | T-02 | Explicit in issue |
| REQ-003 | Acceptance Criteria bullet 2 | scripts/agent/commands/cmd_mcp.py | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-153439 -->