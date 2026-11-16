## Goal
- Add a fast-mode lint gate to the local pre-commit validation gate (`tools/run_validation_gates.py`) so a `ruff check` / `ruff format --check` regression in changed `scripts/` Python files fails locally before push, mirroring the required CI `lint` job.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a fast-mode routing gate that runs `ruff format --check` then `ruff check` on the changed `scripts/` Python files and reports `Fail` (naming the file) on any finding.
  - Add unit tests for the passing and failing changed-file cases (including an `I001` import-order error).
  - Add the gate to the `routing.md` "When to run which tool" table so the drift parity invariant holds.
  - Document the new gate in `rules/toolchain.md`.
- **Out-of-Scope**:
  - Other CI `lint` job steps (mypy, bandit, architecture, security).
  - Fixing the seven already-fixed lint errors in `scripts/rag/ingestion/`.
  - Installing or documenting the git pre-commit hook (Option B below).
  - Changing branch protection or the required checks.
  - Making CI itself run the local gate.
- **Dependencies**: `N/A: none`

## Background
The CI `lint` job (`.github/workflows/ci.yml`) runs `ruff format --check scripts/` and `ruff check scripts/`, and is a required status check on master (branch protection contexts: `test`, `lint`). The repository declares a `ruff` / `ruff-format` pre-commit hook in `.pre-commit-config.yaml`, and `rules/toolchain.md` section 1 documents `uv run ruff check scripts/` as the lint step. `skills/git-commit-and-sync` runs `tools/run_validation_gates.py` in fast mode before committing (Phase 4, "Check Staged").

## Problem
A required check that no local step mirrors means every lint regression is found late, after a push, and blocks unrelated work. Evidence (verified 2026-11-15):

- The `lint` job failed on every master CI run in the sampled history (25 runs, 2026-11-14 04:27 UTC until the fix landed 2026-11-15 09:08 UTC). The cause was seven `I001` import-order errors in `scripts/rag/ingestion/`. A local `ruff check` at the pre-fix commit reported the same error, so it was detectable locally.
- The `ruff` hook in `.pre-commit-config.yaml` is a remote repo hook with no `entry`, so `tools/run_validation_gates.py`'s `parse_precommit_hooks` skips it and it never creates a ruff gate-mapping requirement. This checkout's `.git/hooks/` does hold a `pre-commit` framework hook (installed 2026-09-21), but `git-commit-and-sync` Phase 4 runs `run_validation_gates.py`, not the framework, and the framework hook is not installed on every checkout — so no local step reliably runs ruff for the skill flow.
- `tools/run_validation_gates.py` does not run ruff in fast mode: the only ruff gate (`ruff-format-lint`) lives in `TOOLCHAIN_GATES`, which fast mode never selects. Fast mode is what `git-commit-and-sync` Phase 4 runs by default.
- Result: the required `lint` check blocked the merge of an unrelated PR and was the only place the error surfaced.

## Reason for Change
A required check that no local step mirrors means every lint regression is found late, after a push, and blocks unrelated work. The fix itself is trivial (`ruff check scripts/ --fix`); the cost was the delay and a master that was red for over a day. Adding a fast-mode ruff gate catches the regression locally at commit time with the least new machinery.

## Implementation Intent
Adopt Option A: add a fast-mode routing gate to `tools/run_validation_gates.py` (defined in `tools/_validation_gate_defs.py`) that runs `ruff format --check` then `ruff check` on the changed `scripts/` Python files, reusing the orchestrator's existing changed-file selection and `Pass`/`Fail` classification (no second runner, per the Issue's AI Implementation Instruction). The gate must scope ruff to the changed files rather than scanning the whole repository. Because a new routing gate extends `ROUTING_GATES`, the `routing.md` "When to run which tool" table must gain a matching row to keep the drift parity invariant (`actual == expected`) green. See the `Design` section for the Option A vs B decision and the scoping mechanism.

## Requirements
- `REQ-001`: A fast-mode routing gate runs `ruff format --check` then `ruff check` on the changed `scripts/` Python files and reports `Fail` (naming the file) on any finding.
- `REQ-002`: With no ruff finding in the changed files, the gate reports no ruff `Fail`.
- `REQ-003`: The gate uses the repository's pinned ruff via `uv run ruff`, the same version the CI `lint` job uses.
- `REQ-004`: The gate scopes ruff to the changed `scripts/` Python files; it does not run ruff over the whole repository.
- `REQ-005`: The drift parity invariant between `routing.md`'s checker table, the gate mapping, and the tool-backed pre-commit hooks keeps passing.
- `REQ-006`: Unit tests cover the passing case and the failing case (a changed `scripts/` file carrying an `I001` error produces `Fail`).
- `REQ-007`: `rules/toolchain.md` documents which ruff checks the pre-commit gate runs.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_validation_gate_defs.py` | Modify | Add a fast-mode routing gate to `ROUTING_GATES` that runs `ruff format --check` then `ruff check` on the changed `scripts/` Python files; defined alongside the existing `ruff-format-lint` toolchain gate (lines 141-148) and the `ROUTING_GATES` tuple (line 251). Patterns match `scripts/*.py` and `scripts/**/*.py`. The static command carries a non-placeholder sentinel marking the changed-file position so the gate stays auto-runnable (`requires_context` stays False). | REQ-001, REQ-002, REQ-003, REQ-004 | Verified in Step 3 (read); `ROUTING_GATES`/`TOOLCHAIN_GATES` structure and the fast/full selection in `select_gates` | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/run_validation_gates.py` | Modify | Expand the ruff gate's changed-file sentinel to the changed `scripts/` Python files from the orchestrator's existing `_changed_files` selection, and run ruff via the existing `_subprocess_runner` (no second runner), so the gate scopes to changed files (REQ-004). Additive sentinel-guard: every other gate without the sentinel is unaffected. | REQ-001, REQ-004 | Verified in Step 3 (read); `select_gates`/`run_gate`/`_run_gates`/`_subprocess_runner` read; 59 gate tests pass at baseline | `tests/tools/test_run_validation_gates.py` | Verified |
| `routing.md` | Modify | Add a row to the "When to run which tool" table whose "Run" cell derives to the new gate's `checker_id`, so the drift invariant `actual == expected` stays green. | REQ-005 | Drift baseline: 43 routing checkers mapped, in parity (Step 3); adding a routing gate makes `actual - expected` non-empty without the row | None | Verified |
| `tests/tools/test_run_validation_gates.py` | Modify | Add a passing changed-file test and a failing changed-file test (an `I001` error yields `Fail` and names the file), a scoping assertion (argv carries the changed paths, not `scripts/` bare), and a drift-still-passes assertion after the routing.md row is added. | REQ-001, REQ-004, REQ-005, REQ-006 | Existing test file structure and injected-runner pattern (`_runner_for`) read in Step 3 | `tools/run_validation_gates.py` | Verified |
| `rules/toolchain.md` | Modify | State in the standard validation sequence which ruff checks the fast-mode pre-commit gate runs and when. | REQ-007 | Section 1 documents `uv run ruff check scripts/` as the lint step (Step 3) | None | Verified |

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
| `.pre-commit-config.yaml` | Confirm the `ruff` / `ruff-format` hooks are remote (entry-less) hooks that `parse_precommit_hooks` skips, so Option A (not the hook route) is the working path and no hook-parity entry is needed. | `tools/_validation_gate_defs.py` (REQ-005) |

## Acceptance Criteria
- **AC-001** (`REQ-001`): With a deliberate `I001` import-order error in a changed `scripts/` Python file, the fast-mode gate that `git-commit-and-sync` Phase 4 runs reports `Fail` and names the offending file in the gate detail.
- **AC-002** (`REQ-002`): With no ruff finding in the changed `scripts/` Python files, the gate reports no ruff `Fail`.
- **AC-003** (`REQ-003`): The gate invokes `uv run ruff` (the repository's pinned ruff, the same version the CI `lint` job resolves — currently 0.15.16).
- **AC-004** (`REQ-004`): The gate scopes ruff to the changed `scripts/` Python files; it does not run ruff over the whole repository (the argv passed to the runner carries the changed paths, not `scripts/` as a bare directory).
- **AC-005** (`REQ-005`): The drift parity invariant between `routing.md`'s checker table, the gate mapping, and the tool-backed pre-commit hooks keeps passing (`uv run python tools/run_validation_gates.py drift` exits 0).
- **AC-006** (`REQ-006`): Unit tests cover the passing changed-file case and the failing case (an `I001` error yields `Fail`).
- **AC-007** (`REQ-007`): `rules/toolchain.md` states which ruff checks the fast-mode pre-commit gate runs, matching the gate.

## Tests
- **REQ-001 / REQ-006 (AC-001, AC-002)**: A passing changed-file case (a clean changed `scripts/` file yields `Pass`) and a failing changed-file case (a changed `scripts/` file carrying an `I001` import-order error yields `Fail` and names the file), using the injected-runner pattern already in `tests/tools/test_run_validation_gates.py` (`_runner_for`), so no module-level patch target is introduced and `check_mock_patch_targets` stays clean.
- **REQ-004 (AC-004)**: An assertion that the ruff argv the runner receives carries the changed `scripts/` Python paths (not a bare `scripts/` directory), proving the gate is scoped.
- **REQ-003 (AC-003)**: A gate assertion that the ruff command starts with `uv run ruff`.
- **REQ-005 (AC-005)**: After the `routing.md` row is added, `test_drift_all_routing_checkers_mapped` and `test_live_precommit_config_has_no_drift` still pass — the new gate's `checker_id` has a matching `routing.md` row and no hook-parity entry is required (the ruff hooks are remote/entry-less, so `parse_precommit_hooks` skips them).
- **Regression**: `uv run pytest tests/tools/test_run_validation_gates.py` (59 tests at baseline) and the CI `lint` job still pass.

## Documentation Impact
`rules/toolchain.md` (`REQ-007`) documents the new gate, but it is a `rules/` file, not a `docs/*.md` file, so `docs/00_index.md`'s "Document References by Task" table is not touched. No `docs/*.md` requires updating for this Plan. `N/A: no docs/*.md change` — the only documentation target is `rules/toolchain.md`, outside the Docs-by-Task scope.

## Assumptions
- The gate reuses `tools/run_validation_gates.py`'s changed-file selection (`_changed_files` / `select_gates`) and its `classify`/`run_gate` `Pass`/`Fail` classification; the ruff argv is built from the changed files through the existing `_subprocess_runner` (no second runner), per the Issue's AI Implementation Instruction.
- The ruff hooks in `.pre-commit-config.yaml` stay entry-less (remote repo), so `parse_precommit_hooks` skips them and no `COMMIT_ONLY_HOOKS` hook-parity entry is required for ruff.
- `uv run ruff` resolves to the same ruff the CI `lint` job uses (currently 0.15.16), satisfying `REQ-003` without pinning a new version.
- The `pre-commit` framework hook present in this checkout's `.git/hooks/` (installed 2026-09-21) is orthogonal: `git-commit-and-sync` Phase 4 runs `run_validation_gates.py`, not the framework, so the gate fills the gap the issue describes regardless of whether a given checkout installed the framework hook.
- The static `Gate.command` carries a non-placeholder sentinel (`__CHANGED_FILES__`) marking the changed-file position, so the gate stays auto-runnable (`requires_context` stays `False`) instead of being reported `Not available`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Option A (ruff inside `tools/run_validation_gates.py`) vs Option B (document/install the git pre-commit hook). The Issue lists both and marks the choice 不明. | Resolved by analysis: `git-commit-and-sync` Phase 4 runs `run_validation_gates.py` (not the framework), and the framework hook is inconsistently installed across checkouts, so documenting/installing it would not reliably cover the skill flow. | Choose Option A (recorded in `Design`); close UNK-01 as resolved. | False |
| UNK-02 | Exact mechanism to inject the changed-file list into the ruff argv: expand a sentinel in `run_gate`/`_run_gates` (Design 1) versus a small scoped-ruff helper that imports `_changed_files` (Design 2). | Implementation detail; not needed to fix scope. | Resolve in `plan-to-implementation-procedure`; keep it inside `tools/` and reuse the existing runner. | False |
| UNK-03 | Whether `uv run ruff` in the dev venv matches the CI `lint` ruff version. | Verified locally: `uv run ruff --version` = 0.15.16, matching the CI-resolved version. | Confirm at implementation; no version pin needed if aligned. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_validation_gate_defs.py` | Add one fast-mode routing `Gate` to `ROUTING_GATES` (data-only tuple member; no signature change) | Low — imported only by `tools/run_validation_gates.py`; new tuple member cannot break callers | 1 | N/A: `git-fame` is not on PATH; no per-path breakdown obtainable | None |
| `tools/run_validation_gates.py` | Expand the ruff gate's changed-file sentinel to the changed `scripts/` Python files via the existing `_subprocess_runner` (orchestrator change that enables REQ-004 scoping) | Low — additive sentinel-guard; every other gate without the sentinel is unaffected | 12 | N/A: `git-fame` is not on PATH; no per-path breakdown obtainable | None |
| `routing.md` | Add one row to "When to run which tool" (drift parity) | Low — documentation table only | 19 | N/A: `git-fame` is not on PATH; no per-path breakdown obtainable | None |
| `tests/tools/test_run_validation_gates.py` | Add passing/failing/scoped changed-file tests plus a drift-still-passes assertion | Low — test-only | 7 | N/A: `git-fame` is not on PATH; no per-path breakdown obtainable | None |
| `rules/toolchain.md` | Document the new gate in the standard validation sequence | Low — documentation table only | 20 | N/A: `git-fame` is not on PATH; no per-path breakdown obtainable | None |

## Design
### Option A vs B (UNK-01)
Adopt **Option A**: add a fast-mode routing gate to `tools/run_validation_gates.py` (defined in `tools/_validation_gate_defs.py`) that runs `ruff format --check` then `ruff check` when `scripts/` Python files change. Reject **Option B** (document/install the git pre-commit hook) because:
- `git-commit-and-sync` Phase 4 ("Check Staged") runs `tools/run_validation_gates.py` in fast mode, never the `pre-commit` framework, so the framework hook does not cover the skill's commit path regardless of whether a checkout installed it.
- The framework hook is inconsistently installed across checkouts (this one has it from 2026-09-21; the Issue's checkout did not). Documenting/installing it would not reliably cover the gate the Issue asks for.
- Option A adds the least new machinery: a data-only gate definition plus a scoped argv expansion, no per-contributor install step, no branch-protection change.

### Scoping mechanism (UNK-02) — Design 1 (chosen)
The defs module (`_validation_gate_defs.py`) is pure data and cannot compute changed files, so scoping lives in the orchestrator:
- The gate is selected by `select_gates` when a changed path matches its patterns (`scripts/*.py`, `scripts/**/*.py`).
- `_run_gates` already computes the changed paths once via `_changed_files`. It passes those paths to `run_gate`, which expands the gate's `__CHANGED_FILES__` sentinel to the changed `scripts/` Python files and runs `uv run ruff format --check <files>` then `uv run ruff check <files>` through the existing `_subprocess_runner`. No second runner is introduced.
- The sentinel is a non-placeholder token (no `<`, `[`, `]`, `...`), so `Gate.requires_context` stays `False` and the gate is auto-runnable rather than reported `Not available`.
- **Design 2 (alternative, not chosen):** a small scoped-ruff helper under `tools/` that imports `_changed_files` and runs ruff itself. Rejected in favor of Design 1 because a new tool triggers the "Adding a new tool" routing.md sequence (including `check_tool_descriptions_sync` / `tools/TOOL_DESCRIPTIONS.md`) and gives a cleaner `checker_id`; Design 1 keeps the change to existing tools only and most literally reuses the orchestrator's own changed-file selection.

### Gate shape and `checker_id`
- `mode=MODE_FAST`, `source=SOURCE_ROUTING`, `patterns=("scripts/*.py", "scripts/**/*.py")`, command = `("uv","run","ruff","format","--check","__CHANGED_FILES__")` then `("uv","run","ruff","check","__CHANGED_FILES__")`.
- `checker_id` is auto-derived from `command[0]`; with no `tools/<name>.py` token it returns the first token, `uv`. Verified unique among the current 43 routing gates (none currently derive to `uv`), and a `routing.md` Run cell `` `uv run ruff format --check <changed files>` `` derives to the same `uv`, so the drift invariant holds.
- The two-command form mirrors the existing `ruff-format-lint` toolchain gate (`ruff format` then `ruff check`); `run_gate` stops at the first non-zero exit, so a format finding fails before the check runs.

### Drift parity (REQ-005)
Adding a routing gate extends `ROUTING_GATES`, making `actual - expected` non-empty until `routing.md` gains a matching row. The row's "Run" cell derives to `uv`, restoring `actual == expected`. The ruff hooks stay remote/entry-less, so `parse_precommit_hooks` skips them and no `COMMIT_ONLY_HOOKS` entry is needed — the hook-parity half of the drift check is unchanged. `.pre-commit-config.yaml` is therefore a Reference File (confirm remote status), not a modification target.

### Why `run_validation_gates.py` is a target (not read-only)
The Issue's AI Implementation Instruction says to *read* `run_validation_gates.py` and reuse its selection/classification; scoping ruff to changed files requires the orchestrator to expand the changed-file list into the ruff argv, so it is modified (additive sentinel-guard) rather than left untouched. This keeps blast radius low and avoids adding a new tool.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Preparation / Refactoring (if needed)**
   - [ ] Confirm the dev-venv `uv run ruff --version` matches the CI `lint` ruff (UNK-03); record the version in the plan notes if it differs. (`tools/run_validation_gates.py`, `REQ-003`)
   - [ ] Decide the scoping mechanism (UNK-02): Design 1 (sentinel expansion in `run_gate`/`_run_gates`) is assumed; if Design 2 is chosen instead, add the helper as a new target row via `amend_plan` and drop the `run_validation_gates.py` row. (`tools/_validation_gate_defs.py`, `tools/run_validation_gates.py`)
2. **Phase 2: Core Logic Implementation**
   - [ ] Add the fast-mode routing `Gate` to `ROUTING_GATES` in `tools/_validation_gate_defs.py`: `ruff format --check` then `ruff check`, `patterns=("scripts/*.py", "scripts/**/*.py")`, non-placeholder `__CHANGED_FILES__` sentinel. (`tools/_validation_gate_defs.py`, `REQ-001`, `REQ-003`, `REQ-004`)
   - [ ] In `tools/run_validation_gates.py`, expand the sentinel to the changed `scripts/` Python files from `_changed_files` and run ruff via `_subprocess_runner`; guard so gates without the sentinel are unaffected. (`tools/run_validation_gates.py`, `REQ-001`, `REQ-004`)
3. **Phase 3: Deployment & Verification**
   - [ ] Add unit tests to `tests/tools/test_run_validation_gates.py`: passing changed-file case, failing `I001` case (names the file), a scoping assertion (argv carries the changed paths, not bare `scripts/`), and a drift-still-passes assertion. (`tests/tools/test_run_validation_gates.py`, `REQ-001`, `REQ-004`, `REQ-005`, `REQ-006`)
   - [ ] Document the gate in `rules/toolchain.md`'s standard validation sequence. (`rules/toolchain.md`, `REQ-007`)
   - [ ] Validate: `uv run python tools/check_workitem_structure.py --file <plan>` (Step 8 freeze), `uv run python tools/check_plan_target_overlaps.py`, `uv run pytest tests/tools/test_run_validation_gates.py`, `uv run python tools/run_validation_gates.py drift` (exits 0), `uv run ruff check tools/_validation_gate_defs.py tools/run_validation_gates.py` and `uv run mypy tools/`, and one manual gate run against a file with a deliberate `I001` error (reverted after). (`tools/run_validation_gates.py`, `REQ-001`–`REQ-007`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_validation_gate_defs.py` | Unit: gate exists in `ROUTING_GATES`, `mode=MODE_FAST`, patterns match `scripts/*.py`, `requires_context=False`, `checker_id` derives to `uv` | `uv run pytest tests/tools/test_run_validation_gates.py` | gate present and auto-runnable; id matches a `routing.md` cell |
| `tools/run_validation_gates.py` | Integration: passing changed-file case, failing `I001` case (names the file), scoping assertion (argv carries changed paths, not bare `scripts/`) via injected runner | `uv run pytest tests/tools/test_run_validation_gates.py` | `Pass` clean; `Fail` names file; argv scoped |
| `routing.md` + gate mapping | Drift parity after adding the row (routing + hook-parity halves) | `uv run python tools/run_validation_gates.py drift` | exits 0, all checkers mapped |
| `tests/tools/test_run_validation_gates.py` | Regression of the whole gate suite | `uv run pytest tests/tools/test_run_validation_gates.py` | 59+ pass (59 at baseline) |
| `tools/_validation_gate_defs.py`, `tools/run_validation_gates.py` | Lint + type | `uv run ruff check tools/_validation_gate_defs.py tools/run_validation_gates.py`, `uv run mypy tools/` | clean |
| Manual end-to-end | One real gate run against a file with a deliberate `I001` error, reverted after | `uv run python tools/run_validation_gates.py` (fast, against the fixture) | reports `Fail` and names the file |
| `rules/toolchain.md` | Doc parity: documented checks match the gate | read vs gate command | documented checks match gate |

## Risks
- **Risk**: The additive sentinel-expansion in `run_gate`/`_run_gates` accidentally changes behavior for existing gates. → **Mitigation**: expansion is guarded on the presence of the `__CHANGED_FILES__` sentinel, which no existing gate carries; the 59-test regression suite (`test_run_validation_gates.py`) catches any behavioral change.
- **Risk**: A contributor's changed `scripts/` file carries a pre-existing (non-regression) ruff error, so the gate fails them on something they did not introduce. → **Mitigation**: this mirrors CI semantics on the changed surface and is the intended behavior; the gate only scans files the commit touches, not the whole repo (REQ-004).
- **Risk**: `checker_id` `uv` (auto-derived, non-descriptive) could collide with a future non-`tools/` gate. → **Mitigation**: `uv` is currently unique among routing gates; a collision would make `actual != expected` and fail the drift check immediately, surfacing it.
- **Risk**: ruff version drift between the dev venv and CI. → **Mitigation**: `REQ-003` verified aligned (both resolve 0.15.16); re-confirm at implementation, no version pin needed if still aligned.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / refactoring (confirm ruff version parity; decide scoping mechanism) | Pending | — | — |  |
| 2 | Core logic: add the fast-mode ruff routing gate, expand changed-file scoping in the orchestrator, add the `routing.md` drift row | Completed | — | 20261116-211642 |  |
| 3 | Deployment & verification: tests, `rules/toolchain.md` doc, drift + lint + type + manual gate run | Completed | — | 20261116-211642 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-095520_01_tools__validation_gate_defs_py.md | 2 | Procedure | Completed | — | — |
| implementations/20261116-095520_02_tools_run_validation_gates_py.md | 2 | Procedure | Completed | — | — |
| implementations/20261116-095520_03_routing_md.md | 2 | Procedure | Completed | — | — |
| implementations/20261116-095520_04_tests_tools__test_run_validation_gates_py.md | 3 | Procedure | Completed | — | — |
| implementations/20261116-095520_05_rules_toolchain_md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261115-183024_lintgate001_ruff-check-local-gate.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-205018
- **Related target files**: `tools/_validation_gate_defs.py`, `tools/run_validation_gates.py`, `routing.md`, `tests/tools/test_run_validation_gates.py`, `rules/toolchain.md` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
