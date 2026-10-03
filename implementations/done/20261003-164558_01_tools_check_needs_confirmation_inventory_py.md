## Goal

Make a definitive decision on whether `check_needs_confirmation_inventory.py` should exit non-zero when it finds orphaned Needs Confirmation markers (WARNING severity), and implement that decision in the checker (REQ-001, REQ-002).

## Scope

- Decide whether WARNING-level findings from `check_needs_confirmation_inventory.py` should cause a non-zero exit code.
- Implement the decision in the checker's exit logic or document it if detection-only.
- Consider CI gate implications (UNK-01, UNK-02).

## Assumptions

- The decision can be made without additional information beyond what's available in the current repository state.
- The checker's current behavior (exit 0 for WARNINGs) is the default assumption unless the decision is to change it.
- If the checker is already used in CI gates, changing the exit behavior may require coordination with CI pipeline owners.

## Design decisions

- Classify the checker's purpose based on governance intent:
  - **Detection (informational)**: Exit 0 is appropriate. Add a decision comment documenting this intent.
  - **Enforcement (blocking)**: Exit non-zero is appropriate. Modify `report_and_exit()` in `_docs_consistency_lib.py` to return 1 when WARNING-level findings exist.
- The approach depends on the outcome of unknowns (UNK-01, UNK-02).

## Alternatives considered

- Leave the decision unresolved — rejected because the ambiguity affects CI/CD pipelines and automated verification workflows.
- Default to the current behavior (exit 0) without explicit documentation — rejected because it perpetuates the ambiguity.

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Investigate CI configuration to determine if this checker is used in CI gates (UNK-02).
2. Determine the checker's intended role: detection vs enforcement (UNK-01).
3. Make the decision based on available evidence.
4. Implement the decision:
   - If enforcement: modify `report_and_exit()` in `_docs_consistency_lib.py` to return 1 when WARNING-level findings exist.
   - If detection: add a decision comment to the checker's docstring or configuration documenting the intent.

### Method

- Search CI configuration files (e.g., `.github/workflows/`, `ci/`) for references to `check_needs_confirmation_inventory.py`.
- Review governance owner intent for the checker's role.
- Based on the investigation:
  - **Enforcement path**: Modify line 427 of `_docs_consistency_lib.py`:
    ```python
    # Current: return 1 if errors else 0
    # New: return 1 if errors or warnings else 0
    ```
  - **Detection path**: Add a docstring comment or configuration flag indicating that exit 0 does NOT mean "all clean."

### Details

Current state of `report_and_exit()`:
```python
def report_and_exit(all_issues: list[Issue]) -> int:
    """Print issues sorted by (file, line), summarize, and return the exit code."""
    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    if all_issues:
        for issue in sorted(all_issues, key=lambda i: (i.file, i.line_no)):
            print(f"[{issue.severity}] {issue.file}:{issue.line_no}: {issue.message}")
        parts = []
        if errors:
            parts.append(f"{len(errors)} error(s)")
        if warnings:
            parts.append(f"{len(warnings)} warning(s)")
        print(f"\nFound {', '.join(parts)}.", file=sys.stderr)
    else:
        print("No issues found.")
    return 1 if errors else 0  # <-- Line 427: only ERROR causes non-zero exit
```

Investigation required:
1. Check if `check_needs_confirmation_inventory.py` is referenced in any CI workflow files.
2. Determine governance owner's intent for the checker's role (detection vs enforcement).

## Compatibility considerations

- Changing the exit behavior would affect any downstream consumers that rely on exit 0 even with warnings.
- If the checker is used in CI gates, the exit status determines whether CI passes or fails.

## Security considerations

N/A: tooling change only.

## Rollback considerations

Reverting the exit code change is straightforward — restore the original `return 1 if errors else 0` line. If the decision was made incorrectly, revert and re-evaluate.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_needs_confirmation_inventory.py | Exit code validation | `uv run python tools/check_needs_confirmation_inventory.py; echo $?` | Exit code matches the decision |
| tests/tools/test_check_needs_confirmation_inventory.py | Unit test suite | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py` | All tests pass |

## Completion criteria

- A clear decision is recorded (either "warnings → exit 0" or "warnings → exit non-zero").
- The decision is reflected in the checker's code or documentation.
- Any affected CI configuration is updated accordingly.

## Out of scope

- Resolving the actual orphaned markers themselves (handled by other issues).
- Changing the checker's warning format or severity levels.
- Adding new checks beyond the exit-status decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate CI usage of this checker | Pending | — | — | |
| 2 | Determine checker's intended role (detection vs enforcement) | Pending | — | — | |
| 3 | Implement the decision | Pending | — | — | |
| 4 | Validate exit code matches decision | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261002-155701_ncinv002_exit_status_for_untracked_markers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-150911_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-164558
- **Related target files**: tools/check_needs_confirmation_inventory.py
