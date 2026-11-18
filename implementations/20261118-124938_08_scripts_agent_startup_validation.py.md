## Goal
Correct the startup comment that claims a downstream fail-closed behavior and apply the decision to the timeout and exception branches (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit
- The comment of the exception branch of the RAG consistency step; the branches change only if the decision says so.

## Assumptions
- Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text.
- Under option A or B the behavior is unchanged: the timeout, the exception, and DEGRADED findings add a warning and startup continues. The comment must state that, and refer to ADR-004 for the classification.
- No module consumes the `rag_consistency` outcome except the startup reporter's counts, so the existing claim that the unverified state is fail-closed downstream has no code support.
- The open startup-fail-closed issue also edits this module and relies on this decision; the order is the owner's call (UNK-07).

## Design decisions
- Keep the `noqa` justification in the required form (rule code, em dash, reason); change only the wording that is false.

## Alternatives considered
Making the unverified state FATAL was excluded: option C is a Plan amendment.

## Implementation
### Target file
`scripts/agent/startup_validation.py`
### Procedure
1. Confirm the gate.
2. In the exception branch, replace the two comment lines that say the check is non-critical and that the unverified state is fail-closed downstream with a comment that says: the check reports through a warning and startup continues with RAG consistency unverified, as ADR-004 classifies it; keep the `noqa` rule code and a justification.
3. Leave the timeout branch and the DEGRADED routing as they are under option A or B.
4. Run the startup tests.
### Method
Edit comments only; no code statement changes under option A or B. Follow `rules/coding.md` Suppression governance.
### Details
- Run `uv run python tools/check_suppression_justification.py` after the edit.

## Compatibility considerations
N/A: comment-only change; startup behavior is unchanged.

## Security considerations
N/A: comment-only change.

## Rollback considerations
Revert only this procedure's own changes with `git checkout -- <path>` on each changed path (single-path revert; no bulk form).

## Validation plan
- `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_validation.py`
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run python tools/check_suppression_justification.py`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- The comment states what the code does and no longer claims a downstream fail-closed behavior (AC-7).
- The startup tests pass and no behavior changed.

## Out of Scope
- Changing startup behavior (option C).
- Editing the reporter or other branches.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the maintainer decision (UNK-01) | Pending | — | — | Stop and ask if absent; option C is a Plan amendment |
| 2 | Correct the comment (REQ-008) | Pending | — | — |  |
| 3 | Run the startup tests | Pending | — | — |  |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-008`: startup comment and branches follow the decision
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `scripts/agent/startup_validation.py`
