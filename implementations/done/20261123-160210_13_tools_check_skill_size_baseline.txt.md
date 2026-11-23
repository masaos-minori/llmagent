## Goal

Record the size baseline and the measurement header after the runtime split, and verify the measured per-invocation reduction.

## Scope
**Release unit**: skill-size-gate

In scope: the new baseline file, written last by `uv run python tools/check_skill_size.py --update-baseline`, plus a header comment of a few lines stating the measurement.

## Assumptions

- The file lists `<relpath>\t<size>` for every covered file over the default limit, as the module baseline does; `#` lines are comments.
- Reduction check (REQ-004): compute the per-invocation load of `plan-to-implementation-procedure` and `issue-to-plan` from the Step 0 file lists with the same method as the Plan's Background (167 KB and 146 KB before); each must be at least 12 KB lower, and the totals are recorded in the header.

## Design decisions

- Header lines: date, number of covered files, total bytes, and the two per-invocation figures before and after.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`tools/check_skill_size_baseline.txt` (new)

### Procedure
1. Run `--update-baseline` once from the final tree of procedures 01-12.
2. Add the header comment lines at the top (the tool preserves comment lines only if it writes them; if `write_baseline` drops comments, write the header after the update and confirm `load_baseline` still parses the file).
3. Run the tool without options; it must pass and report the shrunk files as advisory only.

### Method
Run the tool, then add the header; confirm `uv run python tools/check_skill_size.py` exits 0.

### Details
- Rerun `--update-baseline` once more right before the commit if another session changed a covered file.

## Compatibility considerations

New file.

## Security considerations

N/A: sizes only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skill_size.py`
- `uv run pytest tests/tools/test_check_skill_size.py -q` including the live-repository test
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The baseline exists, the tool passes on the final tree, and the header records at least 12 KB lower per-invocation loads for the two skills.

## Out of Scope

Lowering other files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160634 | 20261123-161116 | Recorded the baseline (17 entries) and the header; plan-to-implementation-procedure 166871 to 152099 B, issue-to-plan 145745 to 130991 B (each 14.7 KB lower, above the 12 KB target) |
| 2 | Run the config loading test and the comment-length checker named in Validation plan | Completed | 20261123-161116 | 20261123-161116 | check_skill_size passes; 19 tool tests pass incl. the live-repository test; gates pass |

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
- **Requirement ID**: `REQ-004` (recorded baseline and measured reduction)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `tools/check_skill_size_baseline.txt`
