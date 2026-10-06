## Goal

Update `tests/tools/test_check_adr_structure.py` so its drift-check fixtures use the new
top-level `## Implementation References` section (promoted from the old `### Implementation
References` body-block subsection) and add a case confirming the drift warning fires on the
new top-level section (REQ-005 / AC-5).

## Scope

- **In-Scope**: `tests/tools/test_check_adr_structure.py` — the three tests in
  `TestCheckNotesReferencesDrift` (their `### Implementation References` headings), plus one
  new case. And the tool under test `tools/check_adr_structure.py` (its own row).
- **Out-of-Scope**: the other two tool test files; the tool source itself.

## Assumptions

- `check_adr_structure.py` reads the top-level `## Implementation References` (see its own
  row: `_IMPLEMENTATION_REFERENCES_RE` changes to match level 2). The current fixtures use
  `### Implementation References` (level 3), which the new regex will no longer match — so
  these tests must be updated or they will fail.

## Design decisions

- Replace each fixture's `## Related Documents` / `### Implementation References` pair with a
  single top-level `## Implementation References` heading (the block wrapper is gone).
- Keep the three existing assertions (path absent → WARNING; path present → no finding; zero
  paths → no finding).
- Add `test_drift_warning_on_new_top_level_section`: a doc with `## Implementation Notes`
  citing a scripts path that the top-level `## Implementation References` does not list
  yields the WARNING — proving the check reads the new section.

## Alternatives considered

- Adding a second fixture that keeps `### Implementation References` — rejected: the old
  level-3 subsection no longer exists after migration; only the top-level section remains.

## Implementation

### Target file

`tests/tools/test_check_adr_structure.py`

### Procedure

1. In `TestCheckNotesReferencesDrift.test_notes_path_absent_from_references_flagged_warning`
   (lines 55-73), replace
   ```
   "## Related Documents",
   "",
   "### Implementation References",
   ```
   with
   ```
   "## Implementation References",
   ```
   (the `scripts/bar.py` bullet stays under the now-top-level section).
2. Apply the same replacement in `test_notes_path_present_in_references_not_flagged`
   (lines 75-89) and `test_notes_with_zero_paths_not_flagged_regardless_of_references`
   (lines 91-107): drop the `## Related Documents` blank-line/heading lines, keep
   `## Implementation References` as the section the bullet belongs to.
3. Add `test_drift_warning_on_new_top_level_section` to `TestCheckNotesReferencesDrift`:
   build a doc with `## Implementation Notes` citing `` `scripts/foo.py` `` and a top-level
   `## Implementation References` listing a *different* path; assert
   `check_notes_references_drift([doc])` returns one WARNING mentioning `scripts/foo.py`.

### Method

- Read `test_check_adr_structure.py` lines 54-107 (`TestCheckNotesReferencesDrift`).
- Apply the three fixture edits (steps 1-3) and add the new test (step 3).

### Details

- `check_notes_references_drift` compares `## Implementation Notes` paths against the
  `## Implementation References` section; the fixtures must therefore contain that top-level
  heading for the check to read anything.
- `_doc(...)` builds a `DocFile` from line tuples; keep using it.

## Compatibility considerations

- These tests target `tools/check_adr_structure.py`; update them together with that tool's
  regex change (same coordinated commit).

## Security considerations

N/A: test-only change.

## Rollback considerations

Revert `tests/tools/test_check_adr_structure.py` to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_check_adr_structure.py` | Unit: drift check reads the new top-level `## Implementation References` | `uv run pytest tests/tools/test_check_adr_structure.py -q -p no:cacheprovider -p no:randomly` | Passes; new case confirms the top-level section is read |
| Changed tool file | Static analysis | `uv run ruff` / `uv run mypy` / `uv run bandit` on `check_adr_structure.py` | Clean |

## Completion criteria

- All three existing drift tests use the top-level `## Implementation References`.
- The new case confirms the drift warning fires on the new top-level section.
- Unit tests and static analysis pass.

## Out of scope

- The other two tool test files; the tool source itself (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-005 / AC-5 |
| 2 | Add or update tests per Validation plan | Pending | — | — | test_check_adr_structure.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/bandit + pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-005` — drift check reads the new top-level `## Implementation References` (AC-5)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tests/tools/test_check_adr_structure.py`
