## Goal

Give the guarded marker tool the batch capability of the retired tool: `list` and `mark` of `tools/mark_procedure_new_symbols.py` accept one or more procedure paths, every path is validated before any write, the refusal guard applies per path, and the exit code aggregates across paths (Plan REQ-001: preserve the retired tool's batch capability in the kept tool).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: multi-path `list`/`mark` in `tools/mark_procedure_new_symbols.py`; all-paths validation before the first write; per-path refusal guard; exit-code aggregation (`0` all paths succeeded, `1` any path had nothing to mark, `2` any unusable path, checked before any write); single-path behavior unchanged (AC-1).
- Out of scope: removing `tools/fix_procedure_new_markers.py` (seq 03 document); `tools/TOOL_DESCRIPTIONS.md` and workflow edits (seq 03/05/06/07 documents); `tools/stale_detector.py` (Plan Scope Out-of-Scope).

## Assumptions

- `tools/stale_detector.py` output format and `(new)` rules stay as they are; the kept tool keeps invoking it as a subprocess per procedure path (Plan Reference Files).
- Plan Assumptions: validating every path before any write keeps a multi-path `mark` all-or-nothing for usage errors; per-path refusals do not stop the other paths.
- No module imports this tool except its companion test; it is run by hand (Plan Design — Dependency graphing).
- The Plan's dependency on `plans/20261117-124614_wftool002_status-vocabulary-unify.md` phase 4 is satisfied: that Plan is archived in `plans/done/` and its writer-list edits are already in `tools/TOOL_DESCRIPTIONS.md` (verified at revalidation).

## Design decisions

- Per-path guard: the allowed-name set is computed per procedure path (`reported_missing_symbols(proc)` per path) and refusals are reported per path, so one refused name does not block the other files (Plan Decision 2).
- Validation order: every path is checked (`is_file`) before any file is written; one unusable path exits `2` with nothing written (REQ-001, AC-2).
- Only the CLI layer changes (`list_parser`, `mark_parser`, `_print_list`, `_print_mark`, `main`); the pure helpers `reported_missing_symbols`, `_name_pattern`, `unmarked_lines`, `mark_names` and their tests stay untouched.

## Alternatives considered

- Keep `tools/fix_procedure_new_markers.py` as the batch entry point and leave the kept tool single-path: rejected — the unguarded tool can mark an existing symbol as new and silence the staleness check (Plan Problem), and an alias or wrapper is Out-of-Scope in the Plan.

## Implementation
### Target file
`tools/mark_procedure_new_symbols.py`
### Procedure
1. In both subparsers, change the positional `path` to `paths` with `nargs="+"` (`list_parser` and `mark_parser`).
2. In `main`, validate every path in `args.paths` (`is_file`) before dispatch; on any unusable path print `ERROR: not a file: {path}` for each unusable path and return `2` without processing any path.
3. `list`: call `_print_list` per path and print its report as today.
4. `mark`: call `_print_mark` per path — each call computes its own allowed-name set, applies the refusal guard per name for that path, and writes with `atomic_write_text`; collect the per-path return codes.
5. Aggregate: return `1` if any path returned `1` (nothing to mark), else `0`.
6. Update the module docstring usage lines to the multi-path form.

### Method
- CLI-level restructuring only; no complexity above grade B (Plan Baseline: `radon` reports nothing at grade C or worse — re-confirmed at revalidation).
- Preserve the exact single-path code path semantics: same messages, same exit codes, same marker rules (AC-1).

### Details
- Anchors in the current file: `list_parser.add_argument("path", ...)` and `mark_parser.add_argument("path", ...)`; the `if args.command == "list":` branch; `_print_mark`'s refusal loop and its `return 1` on "Nothing to mark."; `main`'s "ERROR: not a file" check.
- Per-path meanings kept: refusal of every requested name for a path prints `Nothing to mark.` for that path and contributes `1`; `--symbols` and `--all` selection logic stays global (the same name list applies to every path, matching the retired tool's one-symbol-list-per-call form).
- The `--dry-run` flag stays per the shared `add_dry_run_argument` pattern already used by this tool.

### Companion test files
- `tests/tools/test_mark_procedure_new_symbols.py`
  - Procedure: add multi-path `list`, multi-path `mark`, all-paths-validation-before-write, per-path guard, and aggregated-exit-code cases (AC-1, AC-2); migrate the cases of `tests/tools/test_fix_procedure_new_markers.py` that this module does not already cover (a real run writes UTF-8, an already-marked name is left alone); write the multi-path tests first — they fail before the CLI change lands (Plan Phase 1).
  - Validation: `uv run pytest tests/tools/test_mark_procedure_new_symbols.py -v` — all cases pass and the existing refusal test `TestPrintMark.test_refuses_an_existing_symbol` still passes (AC-3).

## Compatibility considerations

- Existing single-path invocations and the existing tests must pass unchanged (AC-1); the refusal message format is unchanged.
- `tools/TOOL_DESCRIPTIONS.md` names this tool's single-path form (line 141); the seq 07 document updates that row. Running `tools/check_tool_descriptions_sync.py` between seq 03 and seq 07 is expected to report the retired-tool row mismatch; the plan-batch end-of-batch run covers both members.

## Security considerations

- No new input surface beyond extra positional paths; subprocess call to `tools/stale_detector.py` unchanged; writes stay atomic via `atomic_write_text`.

## Rollback considerations

- N/A: revert the commit; no persisted state or file moves are involved.

## Validation plan

- `uv run pytest tests/tools/test_mark_procedure_new_symbols.py -v` → all pass (AC-1..AC-3).
- `uv run bandit tools/mark_procedure_new_symbols.py` → clean.
- `uv run radon cc tools/mark_procedure_new_symbols.py -s -n C` → no blocks.
- `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` → clean.
- Smoke run: `list` and `mark --dry-run` on copies of two real procedure documents (Plan Tests).

## Completion criteria

- `list` reports each of two paths and `mark --symbols a,b` marks both; single-path output and exit codes are unchanged (AC-1).
- A name the detector does not report missing for one path is refused for that path only; an unusable path exits `2` before any file is written (AC-2).
- The companion module's migrated and new cases pass, the refusal test still passes (AC-3), and the smoke run succeeds.

## Out of Scope

- Removing `tools/fix_procedure_new_markers.py` and its test (seq 03 document).
- Naming the tool in the two workflow documents (seq 05/06 documents) and the tool description (seq 07 document).
- `tools/stale_detector.py` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-094700 | 20261118-094700 | Multi-path list/mark: positional `path`→`paths` nargs="+" in both subparsers; main validates every path before dispatch, iterates _print_list/_print_mark per path, aggregates exit codes (0 all ok, 1 any nothing-to-mark, 2 any unusable). --all unions missing names across paths. main complexity reduced via _unusable_paths/_resolve_names helpers (radon: no grade C+). |
| 2 | Add or update tests per Validation plan | Completed | 20261118-094700 | 20261118-094700 | Added TestMultiPathCli: multi-path list, multi-path mark write, unusable-path-exits-2-before-write, per-path refusal aggregation, all-succeed-zero, UTF-8 round-trip across paths, already-marked-left-alone at CLI. Migrated retired-tool UTF-8 + already-marked cases. 19 passed (12 original + 7 new). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-094700 | 20261118-094700 | ruff format+check clean; mypy clean (569 files); bandit B404 subprocess pre-existing (not introduced); radon no block ≥ C; smoke: list + mark --all --dry-run on two real procedure copies succeed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docs (TOOL_DESCRIPTIONS.md, workflows) handled by seq 05/06/07; this member is code-only. |

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
- **Requirement ID**: `REQ-001` (multi-path `list`/`mark` in the guarded tool); `REQ-002` (companion test coverage)
- **Source issue**: issues/20261117-123332_wftool003_new-marker-tools-merge.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-124834_wftool003_new-marker-tools-merge.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-041553
- **Related target files**: `tools/mark_procedure_new_symbols.py`, `tests/tools/test_mark_procedure_new_symbols.py`
