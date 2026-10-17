# Implementation Procedure — `scripts/mcp_servers/mdq/mdq_security_validation.py`

## Goal

Confirm mdq's command-specific guard (path/symlink) and postcondition coverage, and
extend it only if a gap remains (`REQ-002`, `REQ-003`).

## Scope

Modify only `scripts/mcp_servers/mdq/mdq_security_validation.py`. Verify the existing
path/symlink guards and postcondition coverage; add a guard/check only where a concrete
gap is found, otherwise leave it unchanged and document as implemented (separate doc row).

## Assumptions

- `validate_mdq_security` (line 93) orchestrates checks including `_db_path_check`,
  `_allowed_dirs_configured_check`, `_allowed_dirs_exist_check`, `_auth_token_check`.
- The plan asserts mdq implements path/symlink command guards; verify this against current
  source rather than trusting the assertion.

## Design decisions

- Treat this as primarily a verify-and-document row. Only extend the validation if the
  re-audit finds a real gap in path/symlink handling or postcondition coverage.
- Any addition must follow the existing check-result pattern
  (`SecurityCheckResult`) used by the other checks.

## Alternatives considered

- Adding a full postcondition layer like git: rejected — mdq's model differs; only extend
  where a genuine gap exists.

## Implementation

### Target file

`scripts/mcp_servers/mdq/mdq_security_validation.py`

### Procedure

1. Read `validate_mdq_security` (93+) and its checks to enumerate the current
   command-specific guards (path/symlink/db-path) and confirm they reject disallowed
   paths/symlinks.
2. Assess postcondition coverage (REQ-003) for mdq's operations; if absent and needed,
   add a minimal check.
3. If no gap, make no code change and record "implemented" in the tool doc (separate row).

### Method

- Locate the path/symlink rejection logic; add a guard only if a bypass is found.
- Keep additions consistent with the existing check structure.

### Details

- Document precisely which layers are implemented vs. not applicable for mdq.

## Compatibility considerations

If a guard is added, ensure it fails closed and integrates with the existing validation
orchestration without changing results for allowed inputs.

## Security considerations

Any new guard must fail closed on ambiguous path/symlink input.

## Rollback considerations

Revert the commit to `mdq_security_validation.py` (no change if assessed compliant).

## Validation plan

- Negative test: assert disallowed path/symlink inputs are rejected.
- Regression: allowed inputs still validate successfully.
- Command: `uv run pytest tests/mcp_servers/mdq/ -q`.

## Completion criteria

mdq's command-specific guard and postcondition coverage are confirmed; any identified gap
is closed, otherwise documented as implemented.

## Out of scope

Other servers' validation, the audit schema doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm/extend mdq guards + postcondition | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: tool doc is a separate row |

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
- **Requirement ID**: `REQ-002` (command guard), `REQ-003` (postcondition)
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-133731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-155408
- **Related target files**: `scripts/mcp_servers/mdq/mdq_security_validation.py`
