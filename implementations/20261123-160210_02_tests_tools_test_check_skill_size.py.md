## Goal

Test the size-budget tool, including every failure case.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new test module. It builds temporary file trees and baselines; it does not read the real repository except in one live-run test marked like the config comment lint's.

## Assumptions

- Verified: `tests/tools/test_check_config_comment_length.py` imports the tool as `from tools import ...` and uses small fixtures plus one live-repository test marked `repo_scan`; this test follows that convention.

## Design decisions

- Fixtures create a root with `skills/x/workflow.md`, `rules/a.md`, `routing.md`, and a baseline file under `tmp_path`.

## Alternatives considered

N/A: plain pytest.

## Implementation
### Target file
`tests/tools/test_check_skill_size.py` (new)

### Procedure
1. Test `collect_covered`: finds the covered patterns, ignores other files, returns sorted relpaths.
2. Test `evaluate`: a new file over the limit is a violation; a file within the limit is clean; a baselined file above its ceiling is a regression; a baselined file below its ceiling is `shrunk` and not a failure; a baseline entry for a missing file, or for a file at or under the limit, is stale.
3. Test `main`: exit 0 clean, exit 1 on a violation or stale entry, exit 2 for a missing root; `--update-baseline` rewrites the baseline from the over-limit files and exits 0; `--no-baseline` reports every over-limit file; a malformed baseline line is reported and dropped (it cannot grandfather a file).
4. Add one `repo_scan` test that the live repository passes with the recorded baseline (it needs procedure 13 and is the only live read).

### Method
Call `main` with explicit `--root`, `--baseline`, and `--limit` arguments and capture stdout and stderr with `capsys`.

### Details
- Use small limits (for example 100 B) so fixtures stay tiny.

## Compatibility considerations

N/A: new tests.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_check_skill_size.py -q`
- Coverage of the new tool at least 90 percent on changed lines (diff-cover at the end of the batch)

## Completion criteria

- Every failure case listed above is tested and the module passes.

## Out of Scope

Production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (baseline-gated size check)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `tests/tools/test_check_skill_size.py`
