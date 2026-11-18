## Goal
Define the Execution Status vocabulary as public constants in `tools/_workitem_status_table.py` (including `N/A` as a terminal, not-done status) and let `_normalize_status` read that one definition, so the template, the writers, and the consumers share a single source.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-01 of the Plan (accept `N/A` as a terminal, not-done status) is confirmed by the maintainer before this document lands; the Plan's Phase 2 starts only after that confirmation.
- The vocabulary is the six values Pending, In Progress, Blocked, Completed, Superseded, N/A (the current five in `_VALID_STATUSES` plus N/A).
- The module is 13934 B of the 24576 B `tools/` size gate today; this change adds a constant block and touches one function, keeping the module under the gate.

## Design decisions
- The public names added beside the existing COMPLETED_STATUS are: PENDING_STATUS, IN_PROGRESS_STATUS, BLOCKED_STATUS, SUPERSEDED_STATUS, NOT_APPLICABLE_STATUS, STATUS_VOCABULARY (frozenset of the six), and TERMINAL_STATUSES (frozenset of COMPLETED_STATUS and NOT_APPLICABLE_STATUS). `tools/close_procedures_batch.py` and the value-rule module read these instead of repeating literals.
- The private `_VALID_STATUSES` becomes STATUS_VOCABULARY plus N/A; `_normalize_status` keeps its alias handling (`_STATUS_ALIASES`) and its exact-match step, and now maps and validates against the vocabulary that contains N/A, so `set-status` can write N/A (Decision 1).
- `_UNFINISHED_STATUSES`, `pending_rows`, and `batch_blocking_rows` are untouched: N/A is terminal and must not enter the unfinished or batch-blocking sets.
- `parse_execution_status_rows`, `update_execution_status`, `parse_execution_status_table`, and `supersede_procedure` are not extended (they are the Plan's recorded radon baseline: D 30, C 14, C 14, C 12).

## Alternatives considered
- Rejecting `N/A` and keeping the vocabulary at five values: rejected by Decision 1; 360 archived rows already hold N/A and the batch-close tool already accepts it, so rejection would require rewriting archived rows.
- Keeping the vocabulary private and exporting only accessor functions: rejected; the Plan requires the consumers to build sets from the shared constants, and the module already exports COMPLETED_STATUS publicly for the same reason.

## Implementation
### Target file
`tools/_workitem_status_table.py`

### Procedure
1. Next to COMPLETED_STATUS, add the single-word status constants PENDING_STATUS, IN_PROGRESS_STATUS, BLOCKED_STATUS, SUPERSEDED_STATUS, and NOT_APPLICABLE_STATUS.
2. Replace the private `_VALID_STATUSES` definition with the public STATUS_VOCABULARY built from the six constants, and define TERMINAL_STATUSES as frozenset of COMPLETED_STATUS and NOT_APPLICABLE_STATUS.
3. Keep a private `_VALID_STATUSES = STATUS_VOCABULARY` alias if needed by the in-module error message, so no in-module call site changes behavior.
4. Confirm `_normalize_status` raises for any trimmed value outside the six and maps the two aliases as before; it now accepts N/A.

### Method
Constant block plus a one-token change in the frozenset the function already reads. No parser or writer logic changes.

### Details
- The module docstring names COMPLETED_STATUS as "the completed-status name every status writer imports"; extend it to name the vocabulary and terminal constants too.
- `tools/manage_workitem_stage.py` re-exports a selected list of this module's names (line 86), not all public names; no new re-export is in scope — the sibling procedures import the new constants directly from this module. `tools/plan_dependency_order.py` keeps its own `_OPEN_STATUSES` literal (Pending, In Progress, Blocked); N/A is not an open status and that file is not a target.
- Status strings are compared trimmed; `_normalize_status` itself does not trim the caller's cell whitespace — consumers trim before calling, as today.

## Compatibility considerations
- Importers (`tools/_detect_unexecuted_archive.py`, `tools/_workitem_stage_parser.py`, `tools/check_workitem_structure.py`, `tools/manage_workitem_stage.py`, `tools/sync_plan_workitem_status.py`, `tools/complete_doc_procedure.py`) see new names only; no removed or renamed public name. `complete_doc_procedure.py` imports `COMPLETED_STATUS` alone (line 44) and is unaffected.
- `set-status` begins accepting the literal N/A. Nothing writes it yet; the template note (sibling procedure) documents the meaning.
- `tools/check_workitem_structure.py --archived-status` does not read `_VALID_STATUSES`, so the archived-status gate behavior is unchanged by this document.

## Security considerations
No new I/O, network, or eval; no bandit-relevant construct.

## Rollback considerations
Revert the file; the added constants are read only by the sibling procedures' code, so reverting this file alone requires reverting `tools/close_procedures_batch.py` and `tools/_workitem_status_check.py` too (do them together if rolling back).

## Validation plan
- `uv run pytest tests/tools/test_sync_plan_workitem_status.py tests/tools/test_close_procedures_batch.py tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py tests/tools/test_amend_plan.py tests/tools/test_plan_dependency_order.py -q` — importer regression, expected Pass.
- Vocabulary behavior (AC-1) is asserted by the tests owned by `implementations/20261118-050931_11_tests_tools_test_check_workitem_structure.py`.
- `uv run ruff format tools tests/tools`, `uv run ruff check tools tests/tools`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit tools`, both `tools/check_module_size.py` invocations.

## Completion criteria
- STATUS_VOCABULARY and TERMINAL_STATUSES are public and contain the six and two values respectively; `_normalize_status("N/A")` returns N/A and an unknown value still raises (tests).
- All importer tests pass and both size gates pass.

## Out of Scope
- Template, checker, consumer, and baseline edits (sibling procedures of the same Plan).
- Aliases for Complete, Skipped, Deferred, or Done (Decision 2: rejected, no alias).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261118-121300 | vocabulary constants landed; importer tests 241 pass |
| 2 | Add or update tests per Validation plan | N/A | — | — | vocabulary tests owned by procedure 11 (Plan Phase 1 row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-121300 | ruff/mypy/bandit/size gate OK |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | docs rows owned by sibling procedures 09/10 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/_workitem_status_table.py`