## Goal

Add `confirmed-not-applied` to the write-outcome vocabulary and to the no-auto-retry set, so a write that is confirmed not to have landed is reported separately from a write whose effect is unknown (REQ-004, AC-4).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- `confirmed-not-applied` is the outcome for a write whose postcondition confirms the repository did not change, as opposed to `outcome_unknown`, where the effect cannot be determined.
- The term appears nowhere else in the repository today, so adding it is a vocabulary extension only; no existing consumer changes behavior.
- `scripts/mcp_servers/git/git_server.py` (procedure 05) is the consumer that writes the value into the audit record; `scripts/mcp_servers/github/exception_handlers.py` and `scripts/mcp_servers/github/github_service_security.py` read the existing members and are not modified.
- Per-tool `retry_policy` values in `scripts/mcp_servers/git/git_tools.py` stay aligned with the classification: `same_logical_call_only` for write tools, which is consistent with the no-auto-retry set. That file is a reference, not a target.

## Design decisions

- The no-auto-retry rule is stated once in this module and read by every server that performs writes (module docstring), so the new member is added to the same set rather than to a per-server list.
- `WriteOutcome` stays a `Literal` of the vocabulary members, so a value outside the vocabulary is a type error rather than a runtime string.

## Alternatives considered

- Keep `confirmed-not-applied` as a separate flag outside the outcome vocabulary — rejected: AC-4 requires the two outcomes to be reported separately, and a flag would let a consumer treat a confirmed non-application as retryable.

## Implementation
### Target file
`scripts/shared/write_outcome.py`

### Procedure
- Add `confirmed-not-applied` to the `WriteOutcome` `Literal` at line 20.
- Add the module-level constant `CONFIRMED_NOT_APPLIED` (new) with value `"confirmed-not-applied"`, next to `OUTCOME_UNKNOWN` and `APPLIED_AUDIT_FAILED`.
- Add the new constant to `NO_AUTO_RETRY_OUTCOMES`.

### Method
- `NO_AUTO_RETRY_OUTCOMES` stays a `frozenset[str]`; the new member is added to the existing set literal.
- Update the module docstring: the vocabulary now names three outcomes, including the case where the effect is confirmed absent.
- Update the comment above `NO_AUTO_RETRY_OUTCOMES` to state why a confirmed non-application is not retried automatically: the caller's request was refused by the guard, so replaying it is a new write, not a replay of the same logical call.

### Details

- `AUDIT_PHASES` and `build_write_audit_fields()` are unchanged; the field contract accepts identifiers only.
- The constant naming style follows the existing members (upper-case name, lower-case value).

### Companion test files

- `tests/shared/test_write_outcome.py`
  - Procedure: extend `test_constants_match_the_vocabulary()` with the new constant, and change `test_no_auto_retry_set_contains_both_outcomes()` to assert the set contains all three members; add a case asserting the new member is in the no-auto-retry set and that the automatic-retry path does not treat it as retryable.
  - Validation: `uv run pytest tests/shared/test_write_outcome.py -v` — `confirmed-not-applied` present, `outcome_unknown` still not auto-retried.

## Compatibility considerations

- `tests/shared/test_write_outcome.py:24` asserts the set equals exactly the two current members and must change with this procedure.
- `scripts/agent/shutdown_budget.py` and `scripts/agent/services/maintenance_jobs.py` define their own `OUTCOME_UNKNOWN` members; they are unrelated to this vocabulary and are not touched.

## Security considerations

- No behavior change; the module is a vocabulary and field contract, not an enforcement point.

## Rollback considerations

- Revert the commit; the vocabulary addition is additive and no consumer depends on it before procedure 05 lands.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Vocabulary and no-auto-retry set | `uv run pytest tests/shared/test_write_outcome.py -v` | `confirmed-not-applied` present and in the no-auto-retry set |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- `confirmed-not-applied` is a member of `WriteOutcome` and of `NO_AUTO_RETRY_OUTCOMES`, and is reported separately from `outcome_unknown` (AC-4).
- No write outcome in the vocabulary is retried automatically.

## Out of Scope

- The audit-record mapping (`scripts/mcp_servers/git/git_server.py`, procedure 05).
- Per-tool `retry_policy` values (`scripts/mcp_servers/git/git_tools.py`, reference only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion `tests/shared/test_write_outcome.py`) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation is procedure 11 |

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
- **Requirement ID**: `REQ-004` (write-outcome vocabulary and no-auto-retry rule)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/shared/write_outcome.py`, `tests/shared/test_write_outcome.py`
