## Goal

Lower the recorded ceiling of `skills/code-implementation/workflow.md` after the split, and record the measured saving in the header.

## Scope
**Release unit**: code-implementation-edge-split

In scope: the baseline file. `uv run python tools/check_skill_size.py --update-baseline` rewrites the entries; the header comment lines are re-added because the tool writes entries only.

## Assumptions

- Verified: the baseline has the entry `skills/code-implementation/workflow.md\t52593` (line 9) and a four-line header (written by procedure 13 of the skillsize001 Plan).
- `workflow-edge.md` is about 11 KB, under the 16,384 B limit, so it has no entry.

## Design decisions

- Header gains one line: date, `workflow.md` before and after, the edge file size, and the net repeated-load saving for `code-implementation` (workflow, SKILL.md, prompt).

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
Compute the saving from `wc -c` of `workflow.md` before (52,593 B) and after plus the edge file.

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

- The ceiling of `workflow.md` is lowered by at least 8,000 B, the header records the saving, and the size check passes.

## Out of Scope

Other entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-162340 | 20261123-162624 | Lowered the workflow.md ceiling to 42118 and added the measurement header line |
| 2 | Run the config loading test and the comment-length checker named in Validation plan | Completed | 20261123-162624 | 20261123-162624 | check_skill_size passes; 19 tool tests pass; gates pass |

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
- **Requirement ID**: `REQ-004` (lowered size baseline and passing checks)
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-162003
- **Related target files**: `tools/check_skill_size_baseline.txt`
