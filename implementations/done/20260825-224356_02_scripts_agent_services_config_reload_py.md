## Goal

Make `ApprovalConfig.gitops_push_blocked` updateable via `/reload`. Add one diff-apply line to `_reload_approval_config()` following the same pattern as the existing 9 fields.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py`: add `gitops_push_blocked` handling to `_reload_approval_config()`.
- Add a new test case verifying the reload behavior.

**Out-of-Scope**:
- Changes to the meaning/default value of `gitops_push_blocked`.
- Changes to the other 9 fields handled by `_reload_approval_config()`.
- Validation execution mechanism (tracked separately as `issues/20260825_cfgreload_missing_validator_reexecution_issue.md`).

## Assumptions

- `_reload_approval_config()`'s "applied" report reflection is automatic — it follows the same mechanism as the existing 9 fields without requiring separate report-addition code.
- The field type (`bool`) and default (`False`) are already defined in `ApprovalConfig` dataclass.

## Design decisions

- Follow the exact same pattern as the existing boolean fields in `_reload_approval_config()`: `if (vb := _get_bool(new_cfg, "...")) is not None: approval.<field> = vb`.
- No signature changes to any method.
- No changes to the "applied" report mechanism — relies on existing infrastructure.

## Alternatives considered

- Add explicit "applied" report logic for this field: rejected because the existing 9 fields rely on implicit report propagation from `apply_config_dict()`, and adding explicit logic would diverge from the established pattern.
- Add validation function for `gitops_push_blocked`: rejected because no existing `validate_*` function exists for this field, and validation is tracked as a separate issue.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. In `_reload_approval_config()` (line ~405), after the last existing field handler (line 429), add the `gitops_push_blocked` diff-apply block.
2. Add a new test case in `tests/agent/services/test_config_reload*.py` verifying that `gitops_push_blocked = true` in the reload payload updates `ctx.cfg.approval.gitops_push_blocked == True`.

### Method

```python
# --- Phase 2: Core Logic Implementation ---

# REQ-001: Add gitops_push_blocked to _reload_approval_config()
# After line 429 (approval.approval_github_allowed_repos), add:

        if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None:
            approval.gitops_push_blocked = vb

# --- Phase 3: Deployment & Verification ---

# New test case (REQ-001):
# In tests/agent/services/test_config_reload*.py, add:
#
# def test_reload_gitops_push_blocked():
#     """Verify gitops_push_blocked can be updated via /reload."""
#     ctx = make_context()  # or use existing fixture
#     outcome = ctx.services.config_reload.apply_config_dict({
#         "gitops_push_blocked": True,
#     })
#     assert ctx.cfg.approval.gitops_push_blocked is True
#     assert "gitops_push_blocked" in outcome.applied
```

### Details

- **Line placement**: Insert after line 429 (`approval.approval_github_allowed_repos`), before the closing of `_reload_approval_config()`.
- **Pattern match**: Uses `_get_bool` exactly like other boolean fields in this function.
- **Assignment target**: `approval.gitops_push_blocked` where `approval = ctx.cfg.approval` (bound at line 411).
- **Test**: New test case only — no modifications to existing 9-field tests. Test verifies both the state change (`ctx.cfg.approval.gitops_push_blocked == True`) and the "applied" report inclusion.

## Compatibility considerations

- Public API unchanged (`ConfigReloadRequest`, `ConfigReloadOutcome`).
- Existing 9 fields in `_reload_approval_config()` are unaffected.
- No config schema changes required — `gitops_push_blocked` already exists in `ApprovalConfig`.

## Security considerations

- `gitops_push_blocked` is a security-sensitive flag (guards repository-content and PR mutations per `tool_approval.py:43`).
- Making it reloadable means the gate can be toggled at runtime without restart — this is intentional (see Plan's Reason for Change).
- No new secrets or credentials introduced.

## Rollback considerations

- Revert: remove the single added line from `_reload_approval_config()`.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | New test green, existing 9-field tests pass |

## Completion criteria

- [ ] `gitops_push_blocked` diff-apply line exists in `_reload_approval_config()` after `approval_github_allowed_repos` handler.
- [ ] New test case verifies `ctx.cfg.approval.gitops_push_blocked == True` after reload with `gitops_push_blocked: True`.
- [ ] Existing 9-field tests in `test_config_reload*.py` still pass.
- [ ] `mypy scripts/` reports no new type errors.

## Out of scope

- Adding `gitops_push_blocked` to `ConfigReloadRequest` mask validation.
- Changing the meaning/default value of `gitops_push_blocked`.
- Modifying field update logic semantics for other fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260825_cfgreload_gitops_push_blocked_not_reloadable_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-141653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
