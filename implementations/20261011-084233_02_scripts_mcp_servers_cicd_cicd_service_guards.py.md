## Goal

Reject workflow values containing a path separator before allowlist matching, preventing path traversal into the allowlist (`REQ-002`: reject `../ci.yml` / `org/repo/.github/workflows/ci.yml` with `CicdAuthorizationError`).

## Scope

- Modify only `scripts/mcp_servers/cicd/cicd_service_guards.py`: add a separator check inside `_assert_allowed_workflow()`.

## Assumptions

- Both `/` and `\` must be rejected (Windows compatibility), per the plan's Assumptions.
- The fail-closed empty-allowlist check takes priority over the separator check.

## Design decisions

- Insert the separator check after the existing empty-allowlist fail-closed block (lines 63-67) and before the `if workflow not in self._workflow_allowlist:` test (line 68), so fail-closed remains the highest-priority guard.
- Reject if the value contains `/` or `\`; raise `CicdAuthorizationError` with a clear message.

## Alternatives considered

- Strip the directory prefix and match on the base name: rejected — `REQ-002` requires rejection, not silent normalization; stripping could mask traversal attempts.
- Check separators in the caller/tool layer: rejected — the guard is the enforcement boundary; keep the check here.

## Implementation

### Target file

`scripts/mcp_servers/cicd/cicd_service_guards.py`

### Procedure

1. In `_assert_allowed_workflow()` (lines 58-71), after the empty-allowlist block (ends line 67) and before the `if workflow not in self._workflow_allowlist:` test (line 68), insert:

```python
if "/" in workflow or "\\" in workflow:
    raise CicdAuthorizationError(
        f"Workflow value contains a path separator and is rejected: {workflow}",
    )
```

2. Keep the existing empty-allowlist check first and the exact-match check after the inserted block.

### Method

Add the block in place. Do not alter `_assert_allowed_repo` or `__init__`. `CicdAuthorizationError` is already imported (line 13) — reuse it; do not add a new import.

### Details

- Current evidence: `_assert_allowed_workflow()` has the empty-list check (lines 63-67) then `if workflow not in ...` (lines 68-71); no separator check present.
- Insertion point verified at top-of-match, after the fail-closed check.

## Compatibility considerations

- Requests that previously passed a full-path value are now rejected earlier (before matching) — consistent with `REQ-001`'s config change and the migration note in `mcp_05_01`.

## Security considerations

- Blocks path traversal (`../`) before any allowlist match; fail-closed empty allowlist still denies all. No widening of the allow-list.

## Rollback considerations

- Remove the inserted block; behavior reverts to pre-change matching.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/cicd/cicd_service_guards.py | Unit: `_assert_allowed_workflow` with `ci.yml` (allowed), `nope.yml` (rejected), `../ci.yml` (rejected), empty allowlist (deny all) | pytest | Four-scenario unit test passes |
| scripts/mcp_servers/cicd/cicd_service_guards.py | Lint/type | ruff, mypy | No lint/type errors |

## Completion criteria

- `_assert_allowed_workflow()` raises `CicdAuthorizationError` for any value containing `/` or `\` before matching; file-name match still allowed; mismatch still rejected; empty allowlist still deny-all.

## Out of scope

- Config value (`REQ-001`), documentation (`REQ-003`). Other cicd guards.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add path-separator rejection in cicd_service_guards.py::_assert_allowed_workflow() (REQ-002) | Completed | — | 20261011-091023 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261011-091023 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261011-091023 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261011-091023 |  |

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
- **Requirement ID**: REQ-002 — add path separator rejection before matching so `../ci.yml` is rejected
- **Source issue**: issues/done/20261007-154047_cicdallow01_unify-cicd-mcp-workflow_allowlist-to-file-name-form.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162442_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-084233
- **Related target files**: scripts/mcp_servers/cicd/cicd_service_guards.py