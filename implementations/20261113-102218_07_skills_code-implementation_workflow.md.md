## Goal
- Add `and not repo_scan` to the Step 4 `--testmon-forceselect` command that determines the targeted scope (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one command in the first bullet of Step 4.
- Not in scope: the full-suite wording, the coverage command (it carries no `-m`), the other Step 4 bullets, Row mapping, the Final Report.

## Assumptions
- The first bullet of Step 4 gives `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed" tests/`, wrapped over two lines, and already refers to `skills/python-test-and-fix/workflow.md` Step 10. Falsifier: the text moved; locate it with `rg -n "testmon-forceselect"`.
- Overlap judged sequencing (Plan Step 2): the Plans for `testspeed004` (full-suite wording) and `testspeed006` (documentation-only case) also edit Step 4 of this file; this procedure changes one command line only. Implement this Plan first; re-read Step 4 before the others.

## Design decisions
- Change the command only; the reference to Step 10 of the test-and-fix workflow already points at the rule.

## Alternatives considered
N/A: no alternative; the targeted-scope command is the iteration selection.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. In the first bullet of Step 4, change the command to `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed and not repo_scan" tests/`, keeping the existing line wrapping style.
2. Add nothing else; the following clause (impact-based selection, see `skills/python-test-and-fix/workflow.md` Step 10) already points at the rule.
3. Run the two skill checkers.

### Method
Edit the bullet in place.

### Details
- Do not touch the "repository-defined full test suite" bullet or the coverage command.
- Keep the file's Step numbering and headings.

## Compatibility considerations
Targeted-scope selection excludes the scans; the once-per-cycle full run keeps selecting them.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The Step 4 `--testmon-forceselect` command carries the exclusion and nothing else in Step 4 changed (`AC-004`).
- Both skill checkers pass.

## Out of Scope
- Documentation-only case (separate Plan), parallel wording (separate Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Pending | — | — |  |

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
- **Requirement ID**: REQ-005 (consistent Step 4 command)
- **Source issue**: issues/20261112-183738_testspeed001_mark-repo-scan-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093307_testspeed001_mark-repo-scan-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102218
- **Related target files**: `skills/code-implementation/workflow.md`
