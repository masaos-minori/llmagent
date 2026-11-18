## Goal
Add the Status value tests to `tests/tools/test_check_workitem_structure.py`: value-rule cases, baseline cases, the live active set, and the template-equality assertion — written first (Plan Phase 1) so they fail until the rule and vocabulary land.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-01 of the Plan is confirmed before the Phase 2 code lands; the tests themselves are written in Phase 1 and may stay red until then.
- The existing test file's pattern is reused: fixtures install the real templates under tmp_path and monkeypatch the checker's ROOT_DIR, so new tests follow the same fixture style rather than touching repository state.

## Design decisions
- One parametrized test for the value rule: a Status outside the vocabulary in an active procedure and in an active plan is reported with category `status-value` and the step and value named in the detail; each of the six vocabulary values passes; `N/A: reason` is reported while a bare N/A passes (AC-3).
- Checker wiring tests: one `--file` call over several paths reports the holder in one of them and the mixed run still exits 1; the directory scan reports a planted holder (AC-3).
- Baseline tests: a planted archived holder is reported by the archived-status mode and not reported once its path is in the status-value baseline fixture; the loader ignores blank lines and `#` comment lines, mirroring the existing archived-status baseline tests (AC-4).
- Live set test: the directory scan over the real active documents reports nothing today (AC-4); it is the regression guard that the vocabulary matches every live active row.
- Template-equality test: the `Status options:` line of `templates/execution-status.md`, split on the separator, equals the vocabulary constants as a set (AC-5).

## Alternatives considered
- Testing the rule module in its own new test file: rejected by the Plan's target table — the row owner is the existing checker test file, which already hosts the archived-status tests the new ones sit beside.
- Snapshot-counting the live archived baseline size in a test: rejected; 647 today, it only shrinks, and a size assertion would break on every legitimate shrink.

## Implementation
### Target file
`tests/tools/test_check_workitem_structure.py`

### Procedure
1. Add the parametrized value-rule cases (active procedure and plan fixtures).
2. Add the `--file` multi-path and directory-scan wiring cases.
3. Add the archived in/out-of-baseline cases and the loader cases.
4. Add the live active-set case.
5. Add the template-equality case.

### Method
Fixture-driven additions in the file's existing style; no repository file is read or written by the tests except the read-only live active-set and template-equality cases.

### Details
- Keep each planted holder small: one Execution Status table with one bad row is enough to trigger the rule.
- The all-red Phase 1 state is expected: the vocabulary, rule module, and checker calls land in Phases 2 to 4.

## Compatibility considerations
- Existing tests in the file keep passing; nothing existing is renamed.

## Security considerations
Not applicable: test-only change.

## Rollback considerations
Delete the added test functions; the code procedures remain independently revertable.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -v` — red in Phase 1, green after Phase 4 (AC-3, AC-4, AC-5).

## Completion criteria
- All five test groups exist; after the code phases, the file passes and the live active set and live archived set report nothing (AC-3 to AC-5).

## Out of Scope
- `N/A` outcome tests for the sync tool and the terminal-set test for the batch-close tool (covered by the companion sections of the two consumer procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tests/tools/test_check_workitem_structure.py`
