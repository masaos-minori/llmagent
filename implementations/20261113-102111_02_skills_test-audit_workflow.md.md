## Goal
- Keep the sentence of `skills/test-audit/workflow.md` that quotes the CI test commands true after the CI merge (`REQ-004`: it names the single merged CI command).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one sentence that starts "Run pytest the way CI does".
- Not in scope: the rest of the file, including the rule that Step 3 and Step 4 do not use `-n`.

## Assumptions
- After the sibling procedure for `.github/workflows/ci.yml` lands, CI runs only `uv run coverage run -m pytest -v tests/` (one process, with coverage) and no longer `uv run pytest -v`. Falsifier: that procedure is not implemented; then the current sentence is still true and this change must wait.
- Implement this procedure after the CI procedure (filename order does so).

## Design decisions
- Name the one CI command and say it also collects coverage; keep "one process, no `-n`" and the ordering reason unchanged.

## Alternatives considered
N/A: the sentence is rewritten, not deleted, because the "do not add `-n`" rule depends on its lead-in.

## Implementation
### Target file
`skills/test-audit/workflow.md`

### Procedure
1. Locate the sentence with `rg -n "Run pytest the way CI does" skills/test-audit/workflow.md`.
2. Replace its CI part so it reads: run pytest the way CI does (`.github/workflows/ci.yml`: `uv run coverage run -m pytest -v tests/`, which also collects coverage): one process, no `-n`. Keep the following sentences (the `-n` and `--randomly-seed` rule) as they are.
3. Run `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.

### Method
Edit the one sentence in place; the file path reference to `ci.yml` stays and resolves.

### Details
- Do not copy the CI step list; name only the command.
- Do not change the neighbouring paragraph about the coverage command sequence from `rules/toolchain.md`.

## Compatibility considerations
N/A: skill text only.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The sentence names the single merged CI command and no longer names `uv run pytest -v` as a CI command (`AC-004`).
- Both skill checkers pass.

## Out of Scope
- `rules/toolchain.md`, other skills, and the CI file (sibling procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (keep the CI sentence true)
- **Source issue**: issues/20261112-183953_testspeed005_run-ci-suite-once.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-092617_testspeed005_run-ci-suite-once.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102111
- **Related target files**: `skills/test-audit/workflow.md`
