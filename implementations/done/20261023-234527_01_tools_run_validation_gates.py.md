## Goal

Create `tools/run_validation_gates.py` — a new thin orchestration entry point that, given a base ref, discovers the changed files (staged plus unstaged), maps them to the validation gates each change needs, runs those gates in the documented order, and prints one `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` summary. It reuses the existing checkers via subprocess rather than reimplementing them, embeds the path-to-gate mapping as data (fed by `rules/toolchain.md` and `routing.md`), supports fast/full modes, and exposes a drift check. (`REQ-001`–`REQ-007`)

## Scope

- **In-Scope**: create `tools/run_validation_gates.py` and its unit tests `tests/tools/test_run_validation_gates.py` — both belong to the `tools/run_validation_gates.py` row of `plans/done/20261023-231525_plan.md` (that plan's Implementation Target Files lists the test file under this row, and its Implementation steps 1-3 each include unit tests).
- **Out-of-Scope**: registering the tool in `tools/TOOL_DESCRIPTIONS.md` (seq 02), adding the pointer to `routing.md` (seq 03), adding the pointer to `rules/toolchain.md` (seq 04), changing any gate or its thresholds, or modifying `.github/workflows/ci.yml` / `.pre-commit-config.yaml` hook sets.

## Assumptions

- `tools/` is not under `scripts/`, so the import-layer contract does not constrain this file; it imports nothing from `scripts/` and shells out to the existing commands.
- The changed files are derived from `git diff <base>` with `--staged` included; `master` is the default base and `--base` overrides it for feature branches.
- Every mapped gate corresponds to an existing, runnable command or tool (verified by the inventory in the four reference sources); the tool runs them as subprocesses.
- `ast-grep` (toolchain step 4) is a local-only gate (not a pre-commit hook or CI job) and is included explicitly.
- A full `pytest` run may be slow locally, so full mode is gated behind an explicit flag (resolves UNK-02).

## Design decisions

- **Thin orchestrator, embedded mapping as data.** The file discovers changed paths, looks up an embedded path-pattern → gate table, and runs each gate's canonical command via subprocess. The mapping is one data structure fed by both sources: `rules/toolchain.md`'s linear 9-step order (canonical run / full mode) and `routing.md`'s ~29 path-keyed conditional checkers (fast mode selects only what the changed files trigger). Each gate records its command and which source it belongs to, so fast mode is a subset of the same gates full mode runs.
- **Source-of-truth discipline + drift guard.** `rules/toolchain.md` stays the canonical command list; the tool's embedded commands mirror it and are not editable elsewhere. The drift check (REQ-006) fails when a `routing.md` checker has no mapping entry, so `routing.md` cannot advance ahead of the tool silently. If the inventory and `rules/toolchain.md` ever contradict, stop and report rather than choosing silently (UNK-04).

## Alternatives considered

- Reading the mapping from an external TOML under `config/`: cleaner drift detection but adds a convention; the in-tool data table is the least-surprising default (resolves UNK-01).
- Parsing `routing.md` prose at runtime to build the mapping: brittle; the embedded table is preferred.

## Implementation

### Target file

`tools/run_validation_gates.py` (new)

### Procedure

Implement in four phases mirroring the plan's Implementation steps.

**Phase 1 — Inventory + mapping data.** Build the gate inventory from `rules/toolchain.md`, `routing.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `tox.ini`; record which gate runs where (pre-commit, CI, tox, local-only). Embed the path-to-gate mapping as data keyed by path-pattern, feeding one structure from both the linear toolchain sequence and the routing table.

**Phase 2 — Discovery + modes + runner + summary.** Discover changed files via `git diff <base>` (default `master`, `--base` override), staged plus unstaged. Provide fast mode (changed-file gates only) and full mode (adds full `pytest` + `diff-cover --fail-under=90`), selected by flag. Run selected gates in the documented order; stop with a non-zero exit on the first `Fail`, printing the exact failing command. Emit one summary using the `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` vocabulary; a skipped or unavailable gate is never shown as `Pass`.

**Phase 3 — Drift check.** Expose a drift check that fails when a checker listed in `routing.md` has no mapping entry.

**Phase 4 — Registration** is covered by seq 02/03/04; this file's part is the code plus its own validation sequence (see Validation plan).

**Commit coordination.** `run_validation_gates.py` is a new `tools/` file, so the `tool-descriptions-sync` pre-commit hook (which runs `check_tool_descriptions_sync.py`) fails on this file's first commit until the tool is documented. This procedure therefore implements and validates the tool and its tests but defers the *commit* until `tools/TOOL_DESCRIPTIONS.md` gains its row (seq 02) in the same change, so the tool, its tests, and its documentation row land in one commit. The drift check (`run_validation_gates.py drift`) needs no documentation and can be run now as evidence.

### Method

1. **Mapping data.** Define a gate registry: a list/dict of entries, each `{patterns: [path-globs], command: [str...], source: "toolchain"|"routing", mode: "fast"|"full"|"both"}`. Populate `patterns`/`command` from the four inventory sources, keyed by the path-patterns `routing.md` uses (e.g. `docs/*.md`, `scripts/**/*.py`, DB schema paths, module-size, Needs-confirmation markers, `tools/`, `skills/`, workitems, ADRs, Japanese prose). Keep `rules/toolchain.md`'s 9 steps as the canonical ordered list used by full mode and as the fallback ordering.
2. **Discovery.** A `_changed_files(base)` helper runs `git diff --name-only --staged --diff-filter=AMRC <base>` (plus the working-tree unstaged set) and returns the changed repo-relative paths. `--base` defaults to `master`.
3. **Selection.** Map each changed path to matching gates by glob against each entry's `patterns`; fast mode keeps `mode in ("fast","both")`, full mode additionally includes `mode == "full"`. Deduplicate while preserving the documented order.
4. **Runner.** For each selected gate, run its command via `subprocess.run(..., check=False)`; classify the exit into `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` (a missing local tool such as `ast-grep`/`diff-cover` is `Not available`, never `Pass`). On the first `Fail`, print the exact command and exit non-zero immediately.
5. **Summary.** Print one consolidated summary table (gate → result + command), using the canonical vocabulary from `rules/ai-execution.md` item 11.
6. **Drift check.** A separate entry (e.g. `run_validation_gates.py drift` or a `--drift` flag) reads the real `routing.md` "When to run which tool" checkers and asserts each has a mapping entry; exit non-zero if any is unmapped.
7. **CLI.** `argparse` with a positional/`--base` interface and `--fast`/`--full` mode flag; expose the drift check as a subcommand or flag.

### Details

- Import nothing from `scripts/`; call existing tools/commands as subprocesses so the tool cannot silently disagree with their checks (REQ-007).
- Mirror `rules/toolchain.md` exactly: the embedded commands must equal the canonical list, and the drift/contradiction guard (UNK-04) catches any future divergence.
- Fast mode stays cheap (no full `pytest`/`diff-cover`); full mode adds them behind the explicit flag (UNK-02).
- Smoke-run on the current working tree and on the historical diff `d388529d1`; record the output as evidence.

## Compatibility considerations

New file; additive with no impact on existing `tools/` scripts, which share the called checkers but do not import this one. No change to CI or pre-commit hook sets.

## Security considerations

Runs external validation commands as subprocesses. Use `subprocess` with a list argument (no shell) and validate the base-ref argument to avoid injection via `git diff` arguments. Unavailable local tools are reported as `Not available`, never silently passed.

## Rollback considerations

Delete the new file. Single-file, additive change; `git checkout -- tools/run_validation_gates.py` or removing the file fully restores the prior state.

## Validation plan

- Unit test path-to-gate selection with fixed fixtures (docs-only vs `scripts/**` diffs) and result classification into the five buckets (`-k selection`, `-k classify`).
- A fast-mode vs full-mode selection test (`-k modes`).
- A drift test against the real `routing.md` that fails when a listed checker has no mapping entry (`-k drift`).
- `uv run ruff format` / `ruff check` clean; `uv run mypy tools/run_validation_gates.py` clean; `uv run bandit tools/run_validation_gates.py` clean (no high/medium).
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.
- Smoke run on the current working tree and on `d388529d1`; record output as evidence.

## Completion criteria

- `run_validation_gates.py` discovers changed files, maps them to gates from the two-source mapping, runs fast/full modes in documented order, stops non-zero on the first `Fail` printing the command, and emits the canonical-vocabulary summary.
- The drift check fails when a `routing.md` checker has no mapping entry.
- `ruff`, `mypy`, and `bandit` are clean on the file.

## Out of Scope

The `tools/TOOL_DESCRIPTIONS.md` registration row, the `routing.md` and `rules/toolchain.md` pointers, and any change to CI/pre-commit hook sets or gate thresholds. The test file (`tests/tools/test_run_validation_gates.py`) is IN-scope (see `## Scope` above); listing it here was a mistake and has been removed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: gate inventory from toolchain.md/routing.md/pre-commit/ci/tox; embed path-to-gate mapping data | Completed | 2026-10-24 | 2026-10-24 | mapping embedded from toolchain.md + routing.md; smoke run current tree + d388529d1 both exit 0 |
| 2 | Phase 2: git diff discovery, fast/full modes, ordered runner, vocabulary summary | Completed | 2026-10-24 | 2026-10-24 | discovery/fast+full modes/runner verified via smoke runs; placeholder cmds classify Not available |
| 3 | Phase 3: drift test against real routing.md | Completed | 2026-10-24 | 2026-10-24 | drift OK: 29 routing.md checkers all mapped (exit 0) |
| 4 | Phase 4: validation sequence (ruff/mypy/bandit); registration is seq 02/03/04 | Completed | 2026-10-24 | 2026-10-24 | ruff format/check + mypy + bandit clean; 18/18 unit tests pass |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`
- **Source issue**: `issues/20261023-173529_gate001_one-entry-point-for-the-pre-commit-validation-gates.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-231525_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-234527
- **Related target files**: `tools/run_validation_gates.py`
