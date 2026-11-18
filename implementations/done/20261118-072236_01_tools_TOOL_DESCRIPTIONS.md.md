# Procedure: tools/TOOL_DESCRIPTIONS.md - run_validation_gates.py rows

## Goal

Make the two `tools/TOOL_DESCRIPTIONS.md` rows for `tools/run_validation_gates.py` state what the runner actually does: no `--fast` option, no stop-at-first-failure claim across gates, the real changed-file discovery, and only the statuses the runner produces.

## Scope
**Release unit**: N/A: not part of a release unit

- Correct the two rows that describe `run_validation_gates.py`: the summary-table row and the detailed row in the tool reference table (re-verified 20261118 after the prerequisite Plan's documentation phase). (REQ-001 to REQ-004)
- Record the claim-by-claim confirmation of every remaining statement of both rows. (REQ-004)
- No runner behavior or option changes; other rows are out of scope.

## Assumptions

- The prerequisite Plan (`plans/20261117-125737_wftool006_gate-output-noise.md`, archived, every step `Completed`) already rewrote these two rows for the new default output and `--verbose`; the sentences it introduced (hidden-argument-gate count line, `--verbose`, header base ref) are kept and only re-verified, not reworded. (Plan Assumption)
- Stop-at-first-failure was never a runner mode; documentation follows the code. (Plan Assumption, UNK-01)
- The five-status wording elsewhere (`routing.md`, the runner's module docstring, its `--help` description) is reported after this lands, not edited here. (UNK-02)

## Design decisions

- State the observable behavior instead of deleting sentences: all selected gates run and each result is reported, the run exits 1 when any gate is `Fail` and 0 otherwise, and within one gate the commands stop at the first non-zero exit. (Plan Decision, wording)
- Two targeted cell edits, one per row, keeping the row layouts and the sentences the prerequisite Plan introduced; this file's rows are shared with two other open Plans of this batch at row level (report-only overlap).
- Verification (20261118-125800, pre-execution stale detection passed): every referenced construct exists and every claim was confirmed against current source. `--help` shows no `--fast` option, `--full` as an additive flag, fast mode as the default, and `--verbose`, `--jobs`, `--base`, and the `drift` subcommand; `_changed_files` runs `git diff --staged --diff-filter=AMRC <base>` plus `git diff --diff-filter=AMRC` (unstaged against the index), so untracked and deleted paths are never seen; `classify` produces only `Not available`, `Pass`, and `Fail`, and `Partial`/`Blocked` appear nowhere outside `VOCAB`, the docstrings, and the `--help` description; `run_gate` stops at the first non-zero exit with `exit code {n}` as the `Fail` detail; `_run_gates` runs every selected gate and returns 1 when any gate is `Fail`; `rules/toolchain.md` has nine numbered steps; the five-status wording exists in `routing.md`, the runner docstring, and `--help` (UNK-02: report-only). UNK-01 confirmed: no stop-at-first-failure mode exists in the code.

## Alternatives considered

- Change the runner to match the rows (add `--fast`, stop at first `Fail`). Rejected: the code and `rules/toolchain.md` describe all selected gates running; the drift is in the documentation. (Plan Assumption)
- Rewrite both rows from scratch. Rejected: high-churn shared file; targeted edits minimize conflict surface with the sibling Plans, same rationale as the sibling tool-document procedure of this batch.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (exists; the two `run_validation_gates.py` rows)

### Procedure

1. Re-read both rows in full before editing (they were last rewritten by the prerequisite Plan), and list each claim with its confirming source; the confirmed list drives the edit and the commit message body (REQ-004, plan Phase 1).
2. In both rows, remove `--fast` and state: fast mode is the default and `--full` adds the `rules/toolchain.md` sequence (REQ-001).
3. Replace the stop claim in both rows with the confirmed behavior: every selected gate runs and each result is printed; the run exits 1 when any gate is `Fail`, otherwise 0; within one gate the commands run in order and stop at the first non-zero exit (REQ-002). Drop "printing the failing command" from the detailed row: the summary prints every gate's row with its detail, and a `Fail` row carries the exit code as its detail.
4. Replace "discovers changed files from `git diff <base>`" with the confirmed discovery: staged changes against the base and unstaged changes against the index, added, modified, renamed, and copied paths only (the `--diff-filter=AMRC` diff in `_changed_files`); untracked and deleted files are never seen (REQ-003).
5. In both rows, state that the produced statuses are `Pass`, `Fail`, and `Not available`; `Partial` and `Blocked` are vocabulary entries no code path produces (REQ-003). Keep the five-status summary sentence in the `--help`-quoting sentence untouched (it is the runner's own wording; UNK-02 handles it).
6. Keep the prerequisite Plan's sentences (hidden-argument-gate count line, `--verbose`, header base ref, concurrency and `exclusive` gate sentences, `drift` subcommand sentence) after verifying them against `--help` and the code.

### Method

Targeted cell edits with the edit tool, one row at a time; verify with the checker after each row.

### Details

- Confirming sources for the claim list: `--help` output (options and subcommand), `_changed_files` (discovery), `classify` (produced statuses), `run_gate` (per-gate stop, `exit code` detail), `_run_gates` (all gates run, exit rule), and `tools/_validation_gate_defs.py` (`Gate` type, `exclusive`, `requires_context`).
- AC-1's `rg` check must stay empty for the runner rows; note that other rows quoting other tools' flags are not in scope.

## Compatibility considerations

- Documentation-only change; readers get corrected claims. No tool, hook, or gate command changes.
- The corrected rows must describe the shipped runner after the prerequisite Plan; landing this before that Plan's documentation phase would describe an output the runner does not have (satisfied: the prerequisite Plan is archived and complete).

## Security considerations

- None beyond keeping the Markdown table structure intact for the checkers.

## Rollback considerations

- Reverting this file restores the previous two rows; no runtime state is involved.

## Validation plan

- `uv run python tools/run_validation_gates.py --help` compared row-by-row with the edited rows.
- `uv run python tools/check_tool_descriptions_sync.py` reports no finding.
- `rg -n -- "--fast" tools/TOOL_DESCRIPTIONS.md` reports nothing for the runner rows (AC-1).
- Claim-by-claim confirmation list recorded in the commit message body (AC-4).
- Report UNK-02 (the same five-status wording in `routing.md`, the runner docstring, and `--help`) to the owner after this lands.

## Completion criteria

- AC-1: neither row mentions `--fast`; fast mode is stated as the default.
- AC-2: both rows state the all-gates run, the exit rule, and the per-gate stop.
- AC-3: discovery and produced-status statements equal the code.
- AC-4: every remaining claim has a recorded confirming source and the sync checker passes.

## Out of Scope

- Runner behavior or options (no `--fast`, no stop-at-first-failure mode).
- The five-status wording in `routing.md`, the runner's docstring, and its `--help` text (UNK-02; a separate issue covers any change).
- Other rows of `tools/TOOL_DESCRIPTIONS.md` owned by sibling Plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | both rows corrected against --help and source; claim list recorded in procedure Verification |
| 2 | Add or update tests per Validation plan | N/A | — | — | no tests owned here; sync checker validates |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | full suite 12759 passed/7 skipped; diff-cover exit 0; sync checker and --fast rg clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no docs/*.md in scope per routing mapping |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261117-132203_wftoolfu003_runner-description-drift.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134238_wftoolfu003_runner-description-drift.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-072236
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`