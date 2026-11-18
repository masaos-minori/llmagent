# Procedure: tools/check_workitem_structure.py - call the plan and procedure leftover rules

## Goal

Wire the new leftover rule module into the structure checker so that top-level plans and procedures are reported under the same `template-leftover` category in `--file` mode and in the directory scan, while archived files stay unscanned.

## Scope
**Release unit**: N/A: not part of a release unit

- Import the rule module and call its plan and procedure entry points from the kind branching of `collect_single_file_findings`, next to the existing `issue` leftover call. (REQ-002)
- Derive the plan bracket set once per directory scan and pass it into each plan call, mirroring the reusable `rule` parameter pattern of `find_template_leftovers`. (REQ-002)
- Keep exit `1` on findings and keep `done/` out of the scan (existing `--include-done` boundary). (REQ-002)
- Import the issue leftover rule from the rule module instead of defining it here, and delete the two moved functions (verification addition, 20261118-133100: this file measures 24275 B of the 24576 B gate — 301 B of headroom, below the ~600 B the wiring alone costs — so the issue rule's relocation per `implementations/20261118-072547_01_tools__workitem_leftover_rules.py.md` is what keeps this wiring landable; the moved code is verbatim, only its root becomes a call argument).

## Assumptions

- The prerequisite Plan's infrastructure is in place (verified 20261118): `collect_single_file_findings` branches on kind, `find_template_leftovers` accepts a reusable `rule` parameter, and `--file` already accepts several paths.
- The status-value Plan (sibling of this batch) also edits this checker and its test module; the edits touch different functions, and this procedure reads the then-current file before editing (UNK-03). Resolved 20261118-133100: the status-value Plan landed (commit `74a4e1f3a`) and its checker additions were re-read as part of this verification.
- The checker is not in the `tools/` size baseline; its current size is 21266 B of the 24576 B gate (re-measured 20261118), so this wiring stays small: a kind branch and a per-scan cache, no new rule logic in this file. Corrected 20261118-133100: the file measures 24275 B (the status-value Plan grew it); the wiring plus the issue rule's departure keeps it back near 23 KB.

## Design decisions

- Keep rule logic out of the checker (in `tools/_workitem_leftover_rules.py`, the sibling procedure document) so the checker grows by call sites only; this is the Plan's stated reason for the new module.
- In a directory scan, load the bracket set once at scan start and pass it down, so thousands of plans do not re-read the template per file; in `--file` mode a single call may read the template on the spot (the rule module's default).
- `find_release_unit_findings` (the existing grade C function) is not extended: the new calls are separate branches, keeping AC-6's "no new grade C or worse" and the Plan's baseline note.
- Verification (20261118-133100, pre-execution stale detection passed): the infrastructure assumptions are current — `find_template_leftovers(doc_path, rule)` at line 288 with the reusable `rule` parameter, `_issue_template_leftover_lines` at line 265, `collect_single_file_findings` kind branching (plan: release-unit findings; issue: leftover call; plan/implementation: status-value findings), `collect_findings` loading the issue rule once per scan, `--file` accepting several paths, and `--include-done` skipping `done/` by default. The kind value for procedures is `implementation` (`_WORK_ITEM_KINDS`), so the new branches read `kind == "implementation"`. The docstring's issue-worded leftover paragraph is at lines 27–32.

## Alternatives considered

- Extend `find_template_leftovers` with a kind parameter. Rejected: it is the issue verbatim-line rule with an issue-specific fence; plans and procedures use structural rules from a different module, and mixing them would grow the one function the size gate is already guarding.
- Report plan/procedure leftovers under a new finding category. Rejected: the Plan keeps one `template-leftover` category so existing hooks, gate reports, and the routing row vocabulary stay unchanged.

## Implementation

### Target file

`tools/check_workitem_structure.py` (exists, 24275 B as re-measured 20261118-133100)

### Procedure

1. Import the plan and procedure entry points and the bracket-set loader from `tools/_workitem_leftover_rules.py` (module-private import of the checker's own helper family is the established `tools/_workitem_*` pattern; no new bootstrap is needed since the checker already carries the `_tool_common` guarded import used by its siblings).
2. In `collect_single_file_findings`, extend the kind branching: `plan` gains the leftover findings in addition to the release-unit findings it already adds, and `procedure` gains its leftover findings; each call receives the pre-derived bracket set when the caller has one.
3. In `collect_findings` (directory scan), load the plan bracket set once before the per-file loop and pass it to every plan file; keep the existing skip of `done/` paths (archived leftovers stay unreported per the Plan Assumption, and `--archived-status` behavior is untouched).
4. Leave the report, exit-code, and `--format` layers unchanged: findings of the new call sites already carry `category` `template-leftover` and flow through them without edits (exit 1 on any finding is existing behavior).
5. Confirm `radon cc -n C` still reports only the pre-existing `find_release_unit_findings` entry for this file.

### Method

Targeted edits to the two collection functions; no function extraction or reformatting beyond what the calls require.

### Details

- The call sites must not run the leftover rules under `--archived-status` (that mode checks Execution Status rows only) and must not run them for archived paths in a directory scan.
- The checker's module docstring sentence about `template-leftover` (currently issue-worded) gains the plan and procedure kinds; the external documentation rows belong to the `routing.md` and `tools/TOOL_DESCRIPTIONS.md` procedure documents, and the `--help` text if it names the kinds.

## Compatibility considerations

- New findings appear for currently-clean active documents only if they are unfilled scaffolds; the AC-4 measurement must show zero reports on the newest filled documents and the active set before this lands in the pre-commit hook and structure gate.
- Command-line surface unchanged; callers (pre-commit hook, gate table, `run_validation_gates.py`) need no changes.

## Security considerations

- No new I/O beyond reading work-item files and the plan template; `bandit` clean.

## Rollback considerations

- Reverting this file removes the call sites; leftover findings disappear while the rule module stays dormant. Revert both files together for a clean state.

## Validation plan

- `uv run pytest tests/tools/test_check_workitem_structure.py -v` (`--file` and directory-scan scaffold tests, archived-not-scanned test).
- `uv run python tools/check_workitem_structure.py` on the live active set: exit 0 (smoke run).
- Scaffold smoke: generate a plan and a procedure skeleton with `tools/generate_workitem.py` outside the work-item tree (dry run or a temporary root) and confirm the checker reports them.
- ruff, mypy, bandit, `uv run radon cc tools/check_workitem_structure.py -s -n C` (only the pre-existing grade C entry), and both `tools/check_module_size.py` invocations.

## Completion criteria

- AC-2: plan and procedure scaffolds are reported as `template-leftover` with exit 1 in `--file` mode and in the directory scan; archived files are not scanned.
- AC-6: no new grade C or worse function; the size gates pass.

## Out of Scope

- The rule implementations (sibling procedure document for `tools/_workitem_leftover_rules.py`).
- Issue leftover behavior, `--archived-status`, the baseline file, and external documentation rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 2 | Add or update tests per Validation plan | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261117-132204_wftoolfu004_plan-leftover-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134334_wftoolfu004_plan-leftover-detection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-072547
- **Related target files**: `tools/check_workitem_structure.py`, `tools/_workitem_leftover_rules.py`
