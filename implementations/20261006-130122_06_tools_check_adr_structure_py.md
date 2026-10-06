## Goal

Update `tools/check_adr_structure.py` so its Implementation Notes-vs-References drift
warning reads the new **top-level** `## Implementation References` section (promoted from
the old `### Implementation References` body-block subsection), while keeping the
`## Known Deviations` presence check (`REQ-005`: the drift warning still works on the new
top-level section; AC-5).

## Scope

- **In-Scope**: `tools/check_adr_structure.py` — update the Implementation References
  heading regex and its section scoping in the drift check; keep the `## Known Deviations`
  presence check. And its test file `tests/tools/test_check_adr_structure.py` (its own
  row).
- **Out-of-Scope**: other checks in this tool; the 20 ADR bodies; other tools.

## Assumptions

- The ADR migration promotes `Implementation References` to a top-level `## ` section
  (part of the coordinated change; see the governance_01 / ADR-migration rows).
- `## Implementation Notes` stays a `## ` section, so the drift comparison source is
  unchanged.
- `rel001` has landed (prerequisite for the whole plan; see the
  `check_docs_structure.py` row).

## Design decisions

- Change `_IMPLEMENTATION_REFERENCES_RE` from matching `### Implementation References`
  (level 3) to `## Implementation References` (level 2).
- Ensure the drift check's section scoping covers the full new top-level section (up to
  the next `## ` heading) rather than a level-3 subsection.
- Leave `check_known_deviations_heading` (`## Known Deviations` presence, ERROR)
  untouched.

## Alternatives considered

- Adding a second regex for both levels — rejected: the old level-3 subsection no longer
  exists after migration; only the top-level section remains.

## Implementation

### Target file

`tools/check_adr_structure.py`

### Procedure

1. In the module-level regex definitions, change
   `_IMPLEMENTATION_REFERENCES_RE` from `r"^### Implementation References\s*$"` to
   `r"^## Implementation References\s*$"`.
2. In `check_notes_references_drift` (current lines 107-112), verify the References
   section is scoped to the new top-level section: the boundary regex passed to
   `_section_paths` must stop at the next `## ` heading and still capture the section
   body. If the current boundary regex (`_H1_TO_H3_HEADING_RE`) truncates at an inner
   `### ` heading inside `## Implementation References`, change it to stop only at `## `
   headings. Confirm `## Implementation References` has no `### ` subheadings that would
   require a boundary change.
3. Confirm `check_known_deviations_heading` (the `## Known Deviations` ERROR presence
   check) is unchanged.

### Method

- Read `check_adr_structure.py` lines 45-47 (`_IMPLEMENTATION_REFERENCES_RE`,
  `_KNOWN_DEVIATIONS_RE`) and 95-127 (`check_notes_references_drift`, `_section_paths`
  usage).
- Make the regex edit (step 1) and any boundary adjustment (step 2).
- Confirm the drift check still compares `## Implementation Notes` paths against the new
  `## Implementation References` section.

### Details

- Current `_IMPLEMENTATION_REFERENCES_RE` (line 47): `r"^### Implementation References\s*$"`.
- `check_notes_references_drift` builds `references_paths` from
  `_section_paths(doc.lines, _IMPLEMENTATION_REFERENCES_RE, _H1_TO_H3_HEADING_RE)`; the
  first argument now matches the top-level section.

## Compatibility considerations

- Callers: CI, `.pre-commit-config.yaml`, `tests/tools/`. No production-runtime import.
- The drift WARNING message and severity are unchanged.

## Security considerations

N/A: static documentation-checker behavior change.

## Rollback considerations

Revert `tools/check_adr_structure.py` (and its test file) to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `check_adr_structure.py` | Unit: drift check reads the new top-level `## Implementation References` | `uv run pytest tests/tools/test_check_adr_structure.py -q -p no:cacheprovider -p no:randomly` | Passes; new case confirms the top-level section is read |
| Changed tool file | Static analysis | `uv run ruff format` / `uv run ruff check --fix` / `uv run mypy` / `uv run bandit` | Clean |
| ADR structure | Integration | `uv run python tools/check_adr_structure.py` | Pass on migrated ADRs; `## Known Deviations` presence check intact |

## Completion criteria

- `_IMPLEMENTATION_REFERENCES_RE` matches the top-level `## Implementation References`.
- The drift warning compares `## Implementation Notes` against the new top-level section.
- The `## Known Deviations` presence check is unchanged.
- Unit tests and static analysis pass.

## Out of scope

- The 20 ADR bodies; other tools; the CI workflow file.

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
- **Requirement ID**: `REQ-005` — `check_adr_structure.py` reads the new top-level `## Implementation References`; drift warning still works (AC-5)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tools/check_adr_structure.py`
