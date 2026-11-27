## Goal
- Create `tools/finalize_procedures.py`, a read-only orchestrator that runs the three procedure checks for a Plan, prints only failing rows, classifies `symbol_missing` findings, and applies the unambiguous actions only with `--apply` (`REQ-001` run and report; `REQ-002` classification; `REQ-003` opt-in edits; `REQ-004` one summary line; `REQ-005` equals the manual run).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module. Tests (`tests/tools/test_finalize_procedures.py`), the inventory row, and the skill text are separate documents; the test file is not a companion because `tools/TOOL_DESCRIPTIONS.md` also names it in `Related Tests`.
- Out of scope: changes to `tools/stale_detector.py`, `tools/check_workitem_structure.py`, `tools/check_workitem_traceability.py`, `tools/mark_procedure_new_symbols.py`.

## Assumptions
- The tool runs the three checkers unchanged as subprocesses with default arguments (`sys.executable`, the tool path, no weakening option such as `--no-siblings` or `--sibling-order any`), as `tools/mark_procedure_new_symbols.py:57-70` already runs `tools/stale_detector.py`.
- Procedure discovery follows `tools/check_workitem_traceability.py:_procedures_of_plan` (`Source plan` base name equals the Plan's base name); per-document checks run on active procedures under `implementations/` by default and also on `implementations/done/` with `--include-done`; the coverage check runs once per Plan and counts archived procedures by its own rule.
- The summary's counts are computed by this tool (procedures checked, Plan target rows), because `--plan-coverage` prints only `No findings.` on success.
- The module must stay at or below 24576 B (`check-module-size-tools`; a new file has no baseline entry). If the draft passes about 20000 B, move the classifier to `tools/_procedure_symbols.py` and raise it as a Plan amendment (fallout class).
- `mark_names` is imported from `tools/mark_procedure_new_symbols.py` as a library; the repository convention is `from tools.mark_procedure_new_symbols import mark_names` with `sys.path.insert(0, <repo root>)` when `__package__` is empty (`tools/rename_doc.py:36-39`).

## Design decisions
- One pure function per concern so each classification is unit-testable without subprocesses: `find_procedures(plan, root, include_done)`, `run_check(argv)` returning `CheckResult(tool, exit_code, output)`, `parse_missing_symbols(output)`, `classify_symbol(text, name)` returning `created here`, `not a code symbol`, or `ambiguous`, `apply_actions(text, actions)`.
- Failure rows are `{document} | {tool} | exit {code} | {first finding line}`; the full output of a failing check is printed below its row (existing exit semantics stay visible).
- `classify_symbol` (new) works only on backticked occurrences of the name inside the document's `## Implementation` section up to `## Compatibility considerations` and decides by the first rule that matches across all occurrences, in this order: `created here` when an occurrence is an assignment or annotation inside its backticks (`NAME = ...`, `name: type`), is preceded or followed within the same line by `def`, `class`, or a creating verb (`create`, `add`, `define`, `introduce`) together with a noun (`function`, `constant`, `field`, `parameter`, `method`, `dataclass`), or sits inside the parentheses of a backticked `identifier(...)` signature span; `not a code symbol` when every occurrence is attribute access (`something.name`), inside a quoted literal, or the value of `key=name`; otherwise `ambiguous`.

- Functions this module creates and that the tests import: `parse_missing_symbols` (new) and `apply_actions` (new), plus the three marked above.

## Alternatives considered
- Put the classifier in `tools/mark_procedure_new_symbols.py`: rejected (Plan Assumptions): its `mark --all` behavior stays documented, and the Plan's target list does not include it.
- Import the checkers as libraries: rejected for `tools/stale_detector.py` (41036 B, `StaleResult` internals) and for exit-code fidelity; subprocess keeps the real exit codes visible.

## Implementation
### Target file
`tools/finalize_procedures.py` (new)

### Procedure
1. Module docstring (usage, exit codes: 0 every check passes, 1 any check fails or the Plan has no procedures, 2 usage error), `from __future__ import annotations`, the `sys.path` fix, imports, constants `CREATED = "created here"`, `NOT_SYMBOL = "not a code symbol"`, `AMBIGUOUS = "ambiguous"`, the `(new)` marker taken from `mark_procedure_new_symbols.NEW_MARKER`.
2. `find_procedures` (new) reads the Plan's base name, scans `implementations/*.md` (and `done/*.md` with `--include-done`) for a `**Source plan**` Traceability value whose base name matches, and returns paths sorted by name (so `seq` order).
3. For each procedure run `check_workitem_structure.py --file {doc}` and `stale_detector.py {doc}`; run `check_workitem_traceability.py --plan-coverage {plan}` once. Every check runs even after a failure. Exit code 0 means pass, anything else a failing row.
4. For each stale output parse `Symbol '<name>' not found in source` lines (the pattern of `tools/mark_procedure_new_symbols.py:_MISSING_SYMBOL_RE`, restated in this module), classify each name, and print `{document}: {name} -> {class}; suggested: add (new) | remove backticks | report only`. A stale line that is not `symbol_missing` is printed as found, unclassified.
5. `--apply`: for `created here` names call `mark_names`; for `not a code symbol` names remove the backticks of every exact backticked occurrence (`` `name` `` becomes `name`; a name inside a longer backticked span is left); `ambiguous` names are never edited; write through `atomic_write_text`; `--dry-run` prints the unified diff with `print_dry_run` and writes nothing; re-run the checks for every changed document and report them.
6. When every check passes print exactly one line: `OK: {n} procedure(s) checked, {rows} Plan row(s), coverage exit 0`, where `rows` is the number of backticked paths in the Plan's `Implementation Target Files` table; return 0.
7. `main(argv: list[str] | None = None) -> int` with `argparse` (`plan`, `--apply`, `--include-done`, `--root`, `add_dry_run_argument`), `__main__` calls `sys.exit(main())`. A missing Plan path returns 2; zero procedures prints `no procedures found for {plan}` and returns 1.

### Method
- Subprocess: `subprocess.run([sys.executable, str(root / "tools" / name), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, check=False, cwd=root)`; mark with `# nosec B603 — fixed argv, no shell`.
- `--root` lets tests point the tools at a temporary tree: the checkers resolve `implementations/` and `plans/` from their own repository root, so tests of the checkers use the real tools against fixtures created under the real repository root's `tmp_path` only where unavoidable; pure functions are tested without subprocesses. If a checker cannot be pointed at a temporary tree, the integration test stubs `run_check` (new) and a separate smoke run covers the real tools (documented comparison in Plan Phase 4).
- Classification regexes live in one tuple per class so each rule has a test.

### Details
- Type annotations on every function; English comments; line length 88.
- A stale finding for a name that the document marks `(new)` cannot appear (the detector already skips it); `--apply` is idempotent.

## Compatibility considerations
- New file; no caller. It runs existing tools with their existing output; a change in their stale line format would break parsing, which a test pins.

## Security considerations
- Fixed argv, no shell, input closed; the only writes are the procedure documents of the named Plan, atomically, and only with `--apply`.

## Rollback considerations
- Revert the commit; nothing else references the tool until the skill text (separate procedures) points to it.

## Validation plan
- `uv run ruff format tools/finalize_procedures.py`, `uv run ruff check tools/finalize_procedures.py --fix`, then confirm `uv run ruff check`.
- `uv run mypy tools/finalize_procedures.py`; `uv run bandit tools/finalize_procedures.py`.
- `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- Comparison run (Plan `REQ-005`): `uv run python tools/finalize_procedures.py plans/done/20261127-085326_wfeff005_affected-areas-tool.md --include-done` against the three tools by hand on the same procedures; pass/fail and exit codes must be equal.

## Completion criteria
- The tool prints one summary line for a passing Plan, failing rows with exit codes otherwise, classifies each `symbol_missing` into the three classes, edits only with `--apply`, never edits `ambiguous`, and lint, type, bandit, and the size gate pass.

## Out of Scope
- The checkers themselves; generating procedure content; the repeated-row generator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tools/finalize_procedures.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `tests/tools/test_finalize_procedures.py` (written by its own procedure) | Pending | — | — | Needs the procedure for seq 02 |
| 3 | Run ruff, mypy, bandit, and the tools size gate on the file | Pending | — | — | |
| 4 | Comparison run on an existing Plan against the three tools by hand (Plan `REQ-005`); stop and report on a disagreement | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (checks, classification, `--apply`, summary, equality with the manual run)
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100214
- **Related target files**: `tools/finalize_procedures.py`
