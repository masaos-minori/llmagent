## Goal

Update the two `run_validation_gates.py` rows and add a `_validation_gate_report.py` row in
`tools/TOOL_DESCRIPTIONS.md` so the inventory states the new default output and the
`--verbose` flag.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 5 of the plan's frozen `Implementation Target Files` table:
`tools/TOOL_DESCRIPTIONS.md` (REQ-006 tool description update and new module row, AC-6).

## Assumptions
- The two runner rows are the Index row (`## Index` table) and the detail row (the `## Work
  Items` table); the new module row goes in the Index table next to the
  `_validation_gate_defs.py` row (category `Shared base`).
- UNK-02 stays: the rows' other claims (`--fast`, stop-on-first-`Fail`) are a recorded
  follow-up issue; this edit changes only the sentences about the default output, the flag,
  and the header.
- Overlap with the sibling Plans and `implementations/20261117-180831_03_tools_TOOL_DESCRIPTIONS.md.md`
  on this file is row-level and compatible (plan Assumptions and UNK-01). Verified 20261117:
  the `180831` and `110514` batch procedures, including `180831_03`, are archived under
  `implementations/done/` and their rows have landed; the overlap claim holds as a history note.

## Design decisions
- Sentence-level edits inside existing rows; no row reordering, no new section.

## Alternatives considered
N/A: documentation-only row edits.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`
### Procedure
- In both runner rows, state: the default summary omits gates whose command needs a runtime
  argument and prints their count plus the flag; `--verbose` prints every row; the header
  names the base ref the run used.
- Add an Index row for `_validation_gate_report.py` (new): category `Shared base`,
  description: the summary renderer of `run_validation_gates.py` (hide rule, count line,
  verbose form, header base).
### Method
Land after or with the seq 01/02 code so the rows state true facts.
### Details
Keep each row one line and match the neighboring rows' density.

## Compatibility considerations
`check_tool_descriptions_sync.py` requires exactly one row per `tools/*.py`; the new private
module gains one row, no duplicates.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — no finding (run after the new
  module file exists).

## Completion criteria
Both runner rows describe the hidden-rows default, the count line, and `--verbose`; the new
module has one row; no other row changed; the sync checker passes (AC-6).

## Out of Scope
The UNK-02 prose drift in the same rows; all other rows; the commit-workflow note (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261117-231500 | run after the seq 01/02 code lands Index row for _validation_gate_report.py + both runner rows; UNK-02 prose untouched |
| 2 | Run the documentation checker named in Validation plan | Completed | — | 20261117-231500 | `check_tool_descriptions_sync.py` check_tool_descriptions_sync.py: no issues |

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
- **Requirement ID**: `REQ-006` (runner rows and new module row)
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125737_wftool006_gate-output-noise.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-201532
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`