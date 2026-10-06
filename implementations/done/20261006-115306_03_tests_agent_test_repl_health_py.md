## Goal

Add a test asserting the audit result for the checked-in shell config, and retain existing `none` → `RuntimeError` assertions. (REQ-004 / AC-4)

## Scope

- Add a new test that loads the repository's checked-in shell config and asserts the audit outcome per Option A
- Retain existing tests that assert `sandbox_backend == "none"` raises `RuntimeError`

## Assumptions

- The checked-in config will have `shell_sandbox_backend = "firejail"` after SEQ-01 is applied
- The audit will raise `RuntimeError` if firejail binary is missing (expected fail-fast)
- Existing tests for `none` → `RuntimeError` remain valid

## Design decisions

- Add a single test that validates the audit against the real checked-in config
- Do not modify existing `none` → `RuntimeError` tests — they validate the audit's unchanged behavior

## Alternatives considered

- Adding multiple tests for different scenarios — rejected because a single test covering the checked-in config is sufficient for the acceptance criterion

## Implementation

### Target file

`tests/agent/test_repl_health.py`

### Procedure

1. Add a new test method that loads the repository's checked-in shell config via `ShellAuditConfig` and asserts the audit outcome
2. Verify existing `none` → `RuntimeError` assertions are retained

### Method

- Add a new test class or method under the existing `test_repl_health.py` test suite
- Use `ShellAuditConfig` to load the checked-in config and assert the audit result

### Details

**New test to add (after the existing firejail tests, ~line 563):**
```python
def test_checked_in_shell_config_audit_result(self):
    """Checked-in shell config resolves to firejail (Option A: none never permitted)."""
    # Load the repository's checked-in shell config via the audit loader
    from agent.security_audit_config import load_shell_audit_config

    shell_cfg = load_shell_audit_config()
    assert shell_cfg is not None
    # Option A: the checked-in backend is firejail, never none
    assert shell_cfg.sandbox_backend == "firejail"
```

**Existing tests to retain (do not modify — they assert the audit's unchanged behavior):**
- `test_shell_sandbox_none_warns` (line 485)
- `test_shell_sandbox_none_raises_in_production` (line 501)
- `test_shell_sandbox_non_firejail_warns` (line 517)

## Compatibility considerations

- The new test depends on the checked-in config having `shell_sandbox_backend = "firejail"` (SEQ-01)
- If firejail is not installed on the host, the audit will raise — this is expected fail-fast, not a test failure

## Security considerations

- This test validates the security audit behavior — it must not be weakened or removed
- The existing `none` → `RuntimeError` tests must remain to ensure the audit's enforcement is not accidentally relaxed

## Rollback considerations

- If the new test fails due to firejail not being installed, the test should be skipped or adjusted to expect the fail-fast behavior
- Reverting the new test would lose coverage for the checked-in config

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl_health.py` | Unit: audit against the real checked-in config | `uv run pytest tests/agent/test_repl_health.py` | Audit passes when firejail present / raises firejail-missing when absent; no `none` value present |

## Completion criteria

- New test exists and asserts the audit result for the checked-in config
- Existing `none` → `RuntimeError` tests are retained
- All tests pass (or are skipped when firejail is not installed)

## Out of scope

- Changes to the audit logic itself (see Reference Files: `security_audit.py`)
- Changes to the sandbox implementation (`init_sandbox`, `build_argv`)
- Other security-audit checks (auth_token, allowlists)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add checked-in-config audit test | Completed | 20261006-191358 | 20261006-191358 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261006-191358 | 20261006-191358 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-191358 | 20261006-191358 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-191358 | 20261006-191358 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-222431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115306
- **Related target files**: tests/agent/test_repl_health.py