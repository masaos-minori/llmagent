> **Superseded**: This plan was the initial draft of Issue `issues/20261115-183024_lintgate001_ruff-check-local-gate.md`. It was superseded by `plans/done/20261115-202908_lintgate001_ruff-check-local-gate.md`, which adopts a different approach (a routing-source gate scoped to changed `scripts/` files instead of a toolchain-source gate over all of `scripts/`) and was frozen and implemented. No implementation procedure was generated for this plan; it is archived here without procedures.

## Goal
- Make the pre-commit validation gate (`tools/run_validation_gates.py`, fast mode, the one `git-commit-and-sync` Phase 4 runs) fail on a ruff finding in `scripts/`, with the same two commands the required CI `lint` job runs, so a lint error is caught before the commit and not first on master.

## Priority
Medium

## Scope
- **In-Scope**: one new non-mutating gate (`ruff format --check scripts/` then `ruff check scripts/`) that fast mode selects when a `scripts/` Python file or `pyproject.toml` changed; the selection change in `select_gates`; tests for both; the matching text in `rules/toolchain.md`.
- **Out-of-Scope**: fixing other lint errors; mypy, bandit or other CI `lint` job steps; changing the ruff configuration or isort settings; changing branch protection or the required checks; installing or documenting the git pre-commit hook (the option not taken, see Design); making CI run the local gate.
- **Dependencies**: N/A: none (no open Issue or Plan named; `plans/20261115-043850_dbreview005_helper-open-leak.md` only cites `rules/toolchain.md` as a reference, so there is no overlap).

## Background
The CI `lint` job runs `ruff format --check scripts/`, `ruff check scripts/`, mypy and a security scan, and is a required status check on master. The `lint` job failed on every sampled master run from 2026-11-14 04:27 UTC until seven `I001` errors in `scripts/rag/ingestion/` were fixed on 2026-11-15 (commit `963d85408`). A local `ruff check` at the pre-fix commit reported the same error. This checkout has no git pre-commit hook (`.git/hooks/` holds only `*.sample` files, `core.hooksPath` unset), and `tools/run_validation_gates.py` runs ruff only in full mode: the `ruff-format-lint` toolchain gate is `mode=MODE_FULL`, and `git-commit-and-sync` Phase 4 runs fast mode unless the user asks for `--full`.

## Problem
No local step in the default commit flow runs ruff, although a required CI check does. Every lint regression is therefore found after a push, and it blocked the merge of an unrelated PR (#17).

## Reason for Change
The error was trivially fixable with `ruff check scripts/ --fix`; the cost was a master that was red for over a day and a blocked merge. A gate that takes well under a second removes that cost.

## Implementation Intent
Add a fast-mode gate that mirrors the CI `lint` job's ruff steps exactly (same commands, same `scripts/` scope), non-mutating. It is a toolchain-source gate with its own path patterns, selected only in fast mode; full mode keeps running the existing `ruff-format-lint` gate. `select_gates` gains one branch for it. No change to `.pre-commit-config.yaml` or to the drift check.

## Requirements
- `REQ-001`: Fast mode selects a ruff gate when a changed path is a Python file under `scripts/` or is `pyproject.toml`; the gate runs `uv run ruff format --check scripts/` and `uv run ruff check scripts/` and fails if either exits non-zero.
- `REQ-002`: The new gate never modifies files (it uses `--check` and no `--fix`), so a gate run cannot edit the working tree during a commit flow.
- `REQ-003`: Full mode still selects every toolchain gate (the new gate included, which costs one extra cached ruff run), so "fast-mode selection is a subset of full-mode selection" keeps holding, and the existing full-mode gates are unchanged.
- `REQ-004`: Tests cover the selection (selected for `scripts/` Python files and `pyproject.toml`; not for other paths; the other toolchain gates stay absent from fast mode), the commands (non-mutating), and a failing result classification; the two existing tests that assert no toolchain gate in fast mode are updated to the new rule.
- `REQ-005`: `rules/toolchain.md` states that fast mode runs the ruff check for `scripts/` changes, and the module docstring of `tools/run_validation_gates.py` matches.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tools/_validation_gate_defs.py | Define the new fast-mode ruff gate | Add a `Gate` named `ruff-check` (source toolchain, mode fast, patterns `scripts/*.py`, `scripts/**/*.py`, `pyproject.toml`) with the two `--check` commands | REQ-001, REQ-002; AC-1, AC-2 | `TOOLCHAIN_GATES` at line 139 holds `ruff-format-lint` with `mode=MODE_FULL` and no patterns; `Gate` fields at lines 15-27 (checked in Step 3) | tests/tools/test_run_validation_gates.py | Verified |
| tools/run_validation_gates.py | Select the new gate in fast mode only | `select_gates` (line 202) adds a branch: a toolchain gate with `mode == MODE_FAST` is selected in fast mode when a pattern matches (full mode already selects every toolchain gate); update the module docstring | REQ-001, REQ-003, REQ-005; AC-1, AC-3, AC-5 | `select_gates` at lines 202-223 selects toolchain gates only when `mode == MODE_FULL`; radon B (9) (checked in Step 3 and Step 5) | tests/tools/test_run_validation_gates.py | Verified |
| tests/tools/test_run_validation_gates.py | Cover the new selection and update two assertions | Add selection, command and failure tests; update `test_selection_scripts_fast_excludes_toolchain` (line 150) and `test_modes_full_adds_toolchain_sequence` (line 268), which assert no toolchain-source gate in fast mode | REQ-004; AC-4 | Both tests exist with `assert not any(gate.source == SOURCE_TOOLCHAIN ...)` at lines 153 and 274 (checked in Step 3) | tests/tools/test_run_validation_gates.py | Verified |
| rules/toolchain.md | Document that fast mode runs ruff for `scripts/` changes | Edit the "Standard validation sequence" intro (line 32) and section 1 (line 34) | REQ-005; AC-5 | Line 32 describes fast mode as the default and `--full` as the complete run; section 1 lists the ruff commands (checked in Step 3) | N/A: documentation | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| .pre-commit-config.yaml | Its remote `ruff` hook has no `entry`, so `parse_precommit_hooks` skips it; confirms the drift check needs no change | tools/run_validation_gates.py; REQ-003 |
| .github/workflows/ci.yml | The CI `lint` job's exact ruff commands (lines 22-25) that the gate must mirror | tools/_validation_gate_defs.py; REQ-001 |
| pyproject.toml | `[tool.ruff]` configuration (`exclude`, `select`, `ignore`); a change to it can change ruff's result | tools/_validation_gate_defs.py; REQ-001 |
| skills/git-commit-and-sync/workflow.md | Phase 4 runs `run_validation_gates.py` in fast mode and states the gate selection | tools/run_validation_gates.py; REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): With a changed `scripts/` Python file that has an `I001` error, `uv run python tools/run_validation_gates.py` (fast mode) reports `Fail` for `ruff-check` and names it in the summary.
- AC-2 (REQ-001, REQ-002): With no ruff finding in `scripts/`, the gate reports `Pass`; running it leaves `git status` unchanged.
- AC-3 (REQ-003): For `scripts/x.py`, the fast selection is a subset of the full selection, and the full selection contains every gate in `TOOLCHAIN_GATES` (as `test_modes_full_adds_toolchain_sequence` asserts today).
- AC-4 (REQ-004): The new and updated tests pass; `uv run python tools/run_validation_gates.py drift` still exits 0.
- AC-5 (REQ-005): `rules/toolchain.md` and the module docstring state the fast-mode ruff check; `uv run ruff check tools/ tests/tools/` and `uv run mypy` on the touched tools report nothing new; `tools/check_module_size.py` passes (both `tools/` files stay under 24576 B).

## Tests
- `REQ-001`: select_gates(["scripts/x.py"], fast), (["scripts/pkg/x.py"], fast) and (["pyproject.toml"], fast) include `ruff-check`; (["docs/a.md"], fast) and (["tests/t.py"], fast) do not.
- `REQ-002`: assert none of the gate's argv tokens is `--fix` and that `format` is paired with `--check`.
- `REQ-003`: select_gates(["scripts/x.py"], full) contains `ruff-format-lint` and `ruff-check`; every fast-mode gate is in the full selection.
- `REQ-004`: `run_gate` with an injected runner returning exit 1 yields `Fail`; exit 0 yields `Pass`; change the two existing assertions to say that the only toolchain-source gate in fast selection is the one with `mode == MODE_FAST`.
- Manual: with a deliberate `I001` error in a copy of a `scripts/` file, run the gate once and revert the change afterwards.

## Documentation Impact
`rules/toolchain.md` (REQ-005) only. No `docs/*.md` change: the validation sequence is documented in `rules/`, not `docs/`.

## Assumptions
- The gate option is chosen over the git-hook option: `git-commit-and-sync` Phase 4 runs the gates on every commit it makes, whereas a hook protects only checkouts that installed it. A hook can still be added later without conflicting with this gate.
- Running ruff over all of `scripts/` is acceptable, though the Issue preferred scoping to changed files "where ruff allows it": measured `uv run ruff check scripts/` and `ruff format --check scripts/` take about 0.07 s each (cached), the same commands as the CI job, so matching CI exactly is chosen over a changed-file scope that could pass locally and still fail in CI.
- The CI ruff steps name only `scripts/` (`.github/workflows/ci.yml` lines 22-25), so `tools/` and `tests/` are outside the CI ruff scope; the new gate follows CI and checks `scripts/` only. This plan does not widen that scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether other checkouts or machines have the git pre-commit hook installed | Only this checkout's `.git/hooks/` was inspected | Ask the user; if some do, the hook can stay as a second layer and no change is needed here | False |
| UNK-02 | Whether the red `lint` job before 2026-11-14 04:27 UTC had the same cause | The sampled CI history starts at that time | `gh run list` for older runs, only if the user wants the history | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tools/_validation_gate_defs.py | Modify | Low: imported only by `tools/run_validation_gates.py` and its test | 1 | N/A | not applicable (rsynced): `tools/` is not deployed (`deploy/deploy.sh` rsyncs `scripts/` only) |
| tools/run_validation_gates.py | Modify | Medium: every gate selection goes through `select_gates`; used by `git-commit-and-sync`, `code-implementation` and review skills | 12 | N/A | not applicable (rsynced): `tools/` is not deployed (`deploy/deploy.sh` rsyncs `scripts/` only) |
| tests/tools/test_run_validation_gates.py | Modify | Low: tests only | 7 | N/A | not applicable (rsynced): `tests/` is not deployed |
| rules/toolchain.md | Modify | Low: documentation; loaded by many skills but changes only one sentence | 20 | N/A | not applicable (rsynced): `rules/` is not deployed |

## Design
- Path B (4 target files). Architecture (checked in Step 5): `tools/_validation_gate_defs.py` imports only `re` and `dataclasses`; `tools/run_validation_gates.py` imports it, `tools._tool_common` and `yaml`; the only other importer of either module is `tests/tools/test_run_validation_gates.py`. `.importlinter` has no contract for `tools/`, so there is no layering to preserve.
- Why a toolchain-source gate and not a routing gate: `drift_report` requires every `ROUTING_GATES` entry to match a row of `routing.md`'s "When to run which tool" table, and a ruff command has no `tools/*.py` checker id. A toolchain gate is not drift-checked against `routing.md`, and `.pre-commit-config.yaml`'s remote `ruff` hook is skipped by `parse_precommit_hooks`, so the drift check needs no change.
- Why a separate gate and not a fast-mode `ruff-format-lint`: that gate's first command is `ruff format scripts/`, which rewrites files; a gate that edits the working tree during the pre-commit run is wrong. The new gate uses `--check` and no `--fix`.
- Selection rule: in `select_gates`, the existing rule (full mode selects every toolchain gate) is kept, and one branch is added: in fast mode, a toolchain gate whose `mode` is `MODE_FAST` is selected when a pattern matches. The new gate therefore also runs in full mode, after `ruff-format-lint` (it is placed right after it in `TOOLCHAIN_GATES`); the duplicate costs one cached ruff run, and it keeps the documented invariant that fast mode is a subset of full mode and the existing `test_modes_full_adds_toolchain_sequence` assertions on it.
- Patterns: `scripts/*.py` and `scripts/**/*.py` (the glob `scripts/**/*.py` needs a directory below `scripts/`, so both are listed, as the existing gate at `tools/_validation_gate_defs.py:287` does) and `pyproject.toml` (holds `[tool.ruff]`).
- Consumer scan: not applicable (no persisted schema, public API or shared constant changes); the importers above were found with `rg`.
- Size: `tools/run_validation_gates.py` is 21202 B and `tools/_validation_gate_defs.py` is 22587 B against the 24576 B limit; neither is in the baseline, so the change must stay within roughly 3 KB and 2 KB.

## Implementation steps
1. **Phase 1: Add the gate and the selection rule**
   - [ ] Add the `ruff-check` `Gate` to `TOOLCHAIN_GATES` (REQ-001, REQ-002; tools/_validation_gate_defs.py)
   - [ ] Add the fast-mode toolchain branch to `select_gates` and update the module docstring (REQ-001, REQ-003, REQ-005; tools/run_validation_gates.py)
2. **Phase 2: Tests**
   - [ ] Add the selection, command and result tests; update the two assertions that forbid a toolchain gate in fast mode (REQ-001 to REQ-004; tests/tools/test_run_validation_gates.py)
3. **Phase 3: Documentation and verification**
   - [ ] Update the fast-mode description in the standard validation sequence (REQ-005; rules/toolchain.md)
   - [ ] Run the validation plan below; deploy step: N/A, no file under `scripts/` or `config/` changes (`deploy/deploy.sh` rsyncs `scripts/` only)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/run_validation_gates.py, tools/_validation_gate_defs.py | Unit | `uv run pytest tests/tools/test_run_validation_gates.py -q` | All tests pass, including the new ones |
| tools/run_validation_gates.py | Drift invariant | `uv run python tools/run_validation_gates.py drift` | Exit 0 |
| tools/run_validation_gates.py, tools/_validation_gate_defs.py | Integration (manual) | Add an `I001` error to a `scripts/` file, run `uv run python tools/run_validation_gates.py`, then revert the file | `ruff-check` reports `Fail`; after the revert it reports `Pass` |
| tools/ and tests/tools/ | Lint and types | `uv run ruff check tools/ tests/tools/`; `uv run mypy --no-namespace-packages tools` | No new finding |
| tools/ | Module size | `uv run python tools/check_module_size.py` | Both files under 24576 B |
| rules/toolchain.md | Documentation consistency | `uv run python tools/run_validation_gates.py` after the edit | No `Fail` |

## Risks
- **Risk**: The gate adds a ruff run to every fast-mode pass that touches `scripts/`. → **Mitigation**: measured about 0.07 s per command (cached); the same commands run in CI anyway.
- **Risk**: The gate runs over all of `scripts/`, so another session's unstaged lint error can fail this session's gate (the same effect the existing gates have, per `skills/git-commit-and-sync/workflow.md` "What the gates see"). → **Mitigation**: the summary names the failing file; the existing rule to compare it with the staged set applies, and the failure is real in CI too.
- **Risk**: Changing the two fast-mode assertions could hide an accidental fast-mode selection of another toolchain gate. → **Mitigation**: the replacement assertions name the allowed fast-mode toolchain gate (`ruff-check`) and require every other toolchain gate to be absent from fast mode.
- **Risk**: A future change to ruff settings outside `pyproject.toml` (for example a new `ruff.toml`) would not select the gate. → **Mitigation**: none needed now: `pyproject.toml` is the only ruff configuration file (checked in Step 3); revisit if another is added.
- **Risk**: Module size headroom is small (about 2 KB in `_validation_gate_defs.py`). → **Mitigation**: the added code is a single `Gate` entry and one branch; `check_module_size.py` is part of the validation plan.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `ruff-check` gate and the fast-mode selection rule (tools/_validation_gate_defs.py, tools/run_validation_gates.py) | Pending | — | — | |
| 2 | Add and update tests (tests/tools/test_run_validation_gates.py) | Pending | — | — | |
| 3 | Update rules/toolchain.md and run the validation plan | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-183024_lintgate001_ruff-check-local-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-184253
- **Related target files**: tools/_validation_gate_defs.py, tools/run_validation_gates.py, tests/tools/test_run_validation_gates.py, rules/toolchain.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1); `TOOLCHAIN_GATES` line 139 | tools/_validation_gate_defs.py | Phase 1 | AC-1, AC-2 | tests/tools/test_run_validation_gates.py selection tests; manual `I001` run | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes (1); `select_gates` lines 202-223 | tools/run_validation_gates.py | Phase 1 | AC-1 | tests/tools/test_run_validation_gates.py selection tests | Confirmed by repository evidence |
| REQ-002 | Issue Constraints (pinned ruff, small runtime); `ruff-format-lint` runs `ruff format` (rewrites files) | tools/_validation_gate_defs.py | Phase 1 | AC-2 | command-shape test; `git status` unchanged after a run | Derived from confirmed evidence |
| REQ-003 | Issue Constraints (parity check keeps passing); `select_gates` full-mode rule | tools/run_validation_gates.py | Phase 1 | AC-3 | full-mode selection test; drift command | Derived from confirmed evidence |
| REQ-004 | Issue Required Changes (2), Acceptance Criteria, Testing Expectations | tests/tools/test_run_validation_gates.py | Phase 2 | AC-4 | `uv run pytest tests/tools/test_run_validation_gates.py -q` | Explicit in issue |
| REQ-005 | Issue Required Changes (3), Documentation Impact | rules/toolchain.md | Phase 3 | AC-5 | validation plan: gates run after the edit | Explicit in issue |
| REQ-005 | Issue Documentation Impact; module docstring states fast mode runs routing gates only | tools/run_validation_gates.py | Phase 1 | AC-5 | docstring read-back; gates run | Derived from confirmed evidence |
