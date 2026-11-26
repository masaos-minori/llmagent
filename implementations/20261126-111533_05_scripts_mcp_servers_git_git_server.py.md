## Goal

The audit record reports the write outcome from the shared vocabulary instead of the current `ok`/`rejected`/`error` mapping only, and the two snapshots this file opens are released (REQ-004, REQ-005, AC-4, AC-5).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- The outcome reaches this file through the `GitServiceError` subclass defined in `scripts/mcp_servers/git/git_service.py` (procedure 03); `DispatchResult` carries `result` and `is_error` only, so no other channel exists.
- `outcome` values already in use (`ok`, `rejected`, `error`) keep their meaning; the vocabulary values are added for write calls whose effect cannot be confirmed, so existing consumers of the audit record are unaffected.
- `tests/mcp_servers/test_write_dangerous_audit.py:232` asserts `outcome == "ok"` for a successful write, so the success mapping must not change.
- Overlap with `plans/20261126-072155_mcpai012_mcp-design-docs-update.md` on `docs/22_mcp/mcp_04_05_git.md` is a sequencing dependency, not a conflict: that plan's row states the wording is final "after mcpai008 lands", so this plan's documentation step (procedure 11) runs first and mcpai012 performs a consistency sweep afterwards.

## Design decisions

- The audit is written before the exception is re-raised, so an outcome-unknown write is recorded. Today `except GitServiceError` at line 354 raises before `_audit_log_safe()` at line 364, so a failed write produces no audit record at all; AC-4 cannot be met without moving the audit call ahead of the re-raise.
- The handler keeps `GitServiceError` → HTTP 500 and `GitPolicyError` → HTTP 200 with `is_error=True`; the outcome-carrying subclass is caught before the generic handler only to read its `outcome` attribute.

## Alternatives considered

- Read the outcome from the result string — rejected: message text is not a stable contract (`docs/22_mcp/mcp_04_05_git.md`, "Callers must not depend on message text").
- Add an `outcome` field to `DispatchResult` in `scripts/mcp_servers/dedup_gate.py` — rejected: that file is not a row of the frozen `Implementation Target Files` table and the change would affect every MCP server.

## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`

### Procedure
- In `call_tool()`, catch the outcome-carrying `GitServiceError` subclass first and set `outcome` to `exc.outcome` (a `shared.write_outcome` value); keep the existing `GitPolicyError` and generic `GitServiceError` mappings.
- Move `_audit_log_safe()` so it runs on the exception path as well as the success and rejection paths.
- Wrap `pre_state` (line 338) and `post_state` (line 359) in the context-manager form of `RepositoryState` so both handles are released (REQ-005).

### Method
- Import `WriteOutcomeError` from `mcp_servers.git.git_service` and the vocabulary constants from `shared.write_outcome`.
- `post_condition` continues to serialize the post-operation snapshot; for a write the serialized post-state is the pipeline's fresh post-state, so the audit record shows the state the postcondition was checked against.
- Keep `_serialize_state()` unchanged; the outcome is a separate field of the record.

### Details

- Outcome values written for a write call: `ok` (confirmed applied), `rejected` (policy guard), `error` (exception without a classified outcome), `outcome_unknown`, `confirmed-not-applied`.
- Read tools keep `ok`/`rejected`/`error`.
- Audit failure must never propagate: `_audit_log_safe()` already swallows exceptions.

## Compatibility considerations

- `tests/mcp_servers/test_write_dangerous_audit.py` asserts one record per write call with `outcome == "ok"`; the new audit-on-exception path adds records for failed writes, so the test's record-count assertion must be checked against the new behavior for the failure cases.
- `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` and `docs/22_mcp/mcp_04_05_git.md` describe the outcome values; the documentation update is procedure 11.

## Security considerations

- No change to path containment, protected-branch, or remote-allowlist enforcement; the audit record carries identifiers only.

## Rollback considerations

- Revert the commit; the outcome mapping and the audit-order change are confined to `call_tool()`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Outcome values in the audit record | `uv run pytest tests/mcp_servers/test_write_dangerous_audit.py -v` | `ok` unchanged; `outcome_unknown` and `confirmed-not-applied` recorded for the designed cases |
| Handle release on the five paths | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | No leaked `git.Repo` handle |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- An outcome-unknown write and a confirmed non-application are reported separately in the audit record (AC-4).
- Both snapshots this file opens are released on every path (AC-5).

## Out of Scope

- The outcome-carrying exception itself (`scripts/mcp_servers/git/git_service.py`, procedure 03).
- The vocabulary member (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (write outcome in the audit record), `REQ-005` (handle release on every path)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/git_server.py`
