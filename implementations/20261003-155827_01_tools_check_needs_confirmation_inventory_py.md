# Implementation Procedure: Exit-Status Decision Recording in check_needs_confirmation_inventory.py

## Goal

Record the owner decision classifying the needs-confirmation inventory checker's exit behavior: warnings → exit 0 (detection mode), only ERROR findings cause failure.

## Scope

Add a concise note to the module docstring of `tools/check_needs_confirmation_inventory.py` recording the exit-status decision and pointing to the rationale in the source plan's Design section. No change to `report_and_exit()` or any function body.

## Assumptions

- The owner decision is recorded: warnings → exit 0 (detection mode), grounded in deliberate WARNING-severity design + backward-compat considerations.
- The module docstring currently lacks any mention of exit-status behavior.
- No additional files require modification beyond this single file.

## Design decisions

- The checker author deliberately assigned `severity="WARNING"` to untracked inline markers (`check_needs_confirmation_inventory.py:274,288`), distinct from `severity="ERROR"` used for declared-field-count mismatches (`:318`). Combined with `report_and_exit()` failing only on ERROR (`tools/_docs_consistency_lib.py:414-427`), this is a deliberate non-blocking design.
- Backward compatibility: `check-needs-confirmation` is a registered `[project.scripts]` console script invoked as a workflow gate. Retroactively flipping warnings to non-zero would turn already-passing runs red without migration.

## Alternatives considered

- If the team later decides warnings should block CI, reassign the untracked-marker and missing-field findings from WARNING to ERROR severity in `check_untracked_inline_markers()` / `check_missing_nc_fields()`. That single-class change makes `report_and_exit()` fail on those findings, converting detection into an enforcement gate. The regression test added under REQ-003 covers whichever posture is adopted.

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Locate the module docstring (lines 1–24 of the file).
2. Add a concise note after the existing usage example documenting the exit-status decision:
   - Warnings (including untracked inline markers) do not cause a non-zero exit.
   - Only ERROR findings produce a non-zero exit.
   - Point to the rationale in the source plan's Design section.
3. Do not modify any function body, including `report_and_exit()`.

### Method

Edit the module docstring using targeted insertion after the existing content. Preserve all existing text; append only the new paragraph.

### Details

**Before edit — module docstring (current state):**

```python
"""check_needs_confirmation_inventory.py — Verify the NC inventory stays in sync with docs/.

docs/00_governance/governance_03_issue-and-uncertainty-management.md Part 2 is meant
to be the single, centralized place where every "Needs confirmation" item across
docs/ is tracked to resolution. Two failure modes were found by manual
review (docs_review_governance.md):

  1. An NC entry is marked "resolved" in the inventory, but its cited
     Source File still contains an inline "Needs confirmation" marker --
     the source doc was never updated to remove the now-stale caveat.
  2. A doc contains an inline "Needs confirmation" marker for a file that
     has no corresponding entry in the inventory at all -- an untracked
     item that the inventory's stated purpose ("centralized inventory ...
     preventing them from being silently accepted as facts") fails to
     cover.

A third, self-contained check catches the inventory document contradicting
itself: governance_03 states its entries "must contain the following
eleven fields" while actually enumerating a different number.

Usage:
    python tools/check_needs_confirmation_inventory.py
"""
```

**After edit — module docstring (proposed state):**

```python
"""check_needs_confirmation_inventory.py — Verify the NC inventory stays in sync with docs/.

docs/00_governance/governance_03_issue-and-uncertainty-management.md Part 2 is meant
to be the single, centralized place where every "Needs confirmation" item across
docs/ is tracked to resolution. Two failure modes were found by manual
review (docs_review_governance.md):

  1. An NC entry is marked "resolved" in the inventory, but its cited
     Source File still contains an inline "Needs confirmation" marker --
     the source doc was never updated to remove the now-stale caveat.
  2. A doc contains an inline "Needs confirmation" marker for a file that
     has no corresponding entry in the inventory at all -- an untracked
     item that the inventory's stated purpose ("centralized inventory ...
     preventing them from being silently accepted as facts") fails to
     cover.

A third, self-contained check catches the inventory document contradicting
itself: governance_03 states its entries "must contain the following
eleven fields" while actually enumerating a different number.

Exit-status contract: warnings (including untracked inline markers) do not
cause a non-zero exit; only ERROR findings produce a non-zero exit. This
is a deliberate detection-mode design (not enforcement): the checker's role
is detection/remediation-triggering, not gating. See the source plan's
Design section for the full rationale.

Usage:
    python tools/check_needs_confirmation_inventory.py
"""
```

## Compatibility considerations

- This is a documentation-only change to the module docstring. No behavioral change.
- The exit-contract is confirmed as-is; future refactorers must not invert it without updating both this docstring and the regression test.

## Security considerations

- No security impact: this is a documentation recording of an existing owner decision.

## Rollback considerations

- Revert the docstring addition via git checkout if the classification is disputed.
- The rollback restores the original docstring without the exit-status note.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_needs_confirmation_inventory.py` | Manual: verify the exit-status note is present and accurate | Read module docstring | Note records: warnings → exit 0, ERROR → non-zero |
| `tools/check_needs_confirmation_inventory.py` | Integration: run against live docs/ with known WARNING findings | `uv run python tools/check_needs_confirmation_inventory.py; echo $?` | Exit code 0 |

## Completion criteria

- The module docstring contains a clear statement of the exit-status contract (warnings → exit 0; ERROR → non-zero).
- The docstring points to the source plan's Design section for the rationale.
- Running the checker against live docs/ produces exit code 0 with WARNING findings present.

## Out of scope

- Changing the checker's warning messages or severity levels.
- Resolving the actual orphaned markers themselves.
- Changing inventory entry format.
- Altering `report_and_exit()` logic or any other checker function.
- Modifying CI configuration files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add exit-status decision note to module docstring | Pending | — | — | REQ-001 |
| 2 | Verify exit code is 0 with WARNING findings present | Pending | — | — | AC-002 |

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
- **Source issue**: issues/20261002-155701_ncinv002_exit_status_for_untracked_markers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-144238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-155827
- **Related target files**: tools/check_needs_confirmation_inventory.py
