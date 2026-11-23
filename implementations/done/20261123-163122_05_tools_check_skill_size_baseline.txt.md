## Goal

Lower the recorded ceilings of the two workflows after the split and record the measurement in the header.

## Scope
**Release unit**: pipeline-edge-split

In scope: the baseline file. `uv run python tools/check_skill_size.py --update-baseline` rewrites the entries; the existing header lines are preserved by re-adding them (the tool writes entries only).

## Assumptions

- Verified: the baseline has entries for both workflows (39108 and 45620 at the planning commit) and a header with the Stage 2 and Stage A lines.
- Each edge file is under 16,384 B and has no entry.

## Design decisions

- Add one header line: date, the two workflows before and after, and the edge file sizes.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`tools/check_skill_size_baseline.txt`

### Procedure
1. Run `--update-baseline` after procedures 01-04.
2. Re-add the existing header lines and the new measurement line.
3. Run `uv run python tools/check_skill_size.py`; it must pass.

### Method
Compute the sizes with `wc -c` before (39,108 B and 45,620 B) and after.

### Details
- Re-run `--update-baseline` once more right before the commit if another session changed a covered file.

## Compatibility considerations

N/A: ceilings only.

## Security considerations

N/A: sizes only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skill_size.py`
- `uv run pytest tests/tools/test_check_skill_size.py -q`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The two ceilings are lowered by at least 4,000 B and 3,000 B, the header records the measurement, and the size check passes.

## Out of Scope

Other entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-163225 | 20261123-163505 | Lowered both ceilings (34876 and 42540) and added the measurement header line |
| 2 | Run the config loading test and the comment-length checker named in Validation plan | Completed | 20261123-163505 | 20261123-163505 | check_skill_size passes; 19 tool tests pass; gates pass |

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
- **Requirement ID**: `REQ-004` (lowered size baseline)
- **Source issue**: issues/20261123-161834_skillsize003_compress-skill-workflows-remaining.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-162854_skillsize003_compress-skill-workflows-remaining.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-163122
- **Related target files**: `tools/check_skill_size_baseline.txt`
