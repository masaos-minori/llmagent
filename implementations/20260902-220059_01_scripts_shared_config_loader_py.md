## Goal

Make `ConfigLoader.load_all()`'s missing-required-file behavior unconditional — a missing `agent.toml` raises `ConfigMissingError` regardless of the `strict` parameter value.

## Scope

Modify `scripts/shared/config_loader.py` only. Change the default value of `strict` from `False` to `True` in `load_all()`, so that a missing file in `_REQUIRED_CONFIG_FILES` always raises `ConfigMissingError`.

## Assumptions

- `_REQUIRED_CONFIG_FILES` and `_BASE_CONFIG_FILES` are currently identical single-element tuples `("agent.toml",)` — confirmed by repository evidence at lines 68-89.
- `ConfigParseError`/`ConfigReadError` are not caught by the existing `except ConfigMissingError` block and already propagate unconditionally — confirmed by direct read.
- Changing the default to `True` does not break any caller that legitimately relies on graceful degradation for a missing `agent.toml`.

## Design decisions

- Change the default parameter value (`strict: bool = False` → `strict: bool = True`) rather than adding explicit `strict=True` callsites. This is a single-line change with minimal blast radius and avoids the risk of forgetting to update one of the 5 callers.
- If a caller legitimately needs non-strict mode in the future, it can pass `strict=False` explicitly.

## Alternatives considered

- Adding explicit `strict=True` to each of the 5 call sites instead of changing the default. Rejected because it requires modifying 5 files and risks missing a caller; changing the default is a single-line fix.
- Introducing a new environment variable to control strictness. Rejected because ADR-004 INV-01/INV-02 mandates "no environment-based relaxation" for fail-closed startup behavior.

## Implementation

### Target file

`scripts/shared/config_loader.py`

### Procedure

Change the `strict` parameter default in `ConfigLoader.load_all()` from `False` to `True`.

### Method

Edit line 68 of `scripts/shared/config_loader.py`: replace `strict: bool = False` with `strict: bool = True`.

### Details

1. Open `scripts/shared/config_loader.py`
2. Find the `def load_all(self, strict: bool = False)` signature (line 68)
3. Replace `strict: bool = False` with `strict: bool = True`
4. Verify the change is consistent with the existing exception handling logic at lines 83-89: `if strict and name in _REQUIRED_CONFIG_FILES: raise ConfigMissingError(...)`

## Compatibility considerations

- All 5 existing call sites omit the `strict` argument, so they will now inherit the new default. No caller changes needed unless a caller previously relied on silent-continue for a missing `agent.toml`.
- `cmd_config.py`'s CLI command call site is explicitly re-verified in Phase 1 rather than assumed safe.

## Security considerations

This change directly addresses a security-relevant gap: a missing `agent.toml` would not stop the Agent process from starting, contrary to ADR-004 INV-01/INV-02's Fail-Fast requirements. Making the default strict closes this gap across all environments.

## Rollback considerations

Revert the single parameter default change: `strict: bool = True` → `strict: bool = False`. No other code changes to revert.

## Validation plan

Run `uv run pytest tests/shared/test_config_loader.py -v` to confirm all existing tests still pass and the new strict-default behavior is correct.

## Completion criteria

- `strict` parameter default changed from `False` to `True` in `load_all()`
- All existing tests in `tests/shared/test_config_loader.py` pass
- No regressions in any of the 5 call sites

## Out of scope

- Modifying any of the 5 call sites individually (handled by their respective implementation procedure documents)
- Changes to `ProductionConfigValidator` (REQ-002 is a consequence of REQ-001, handled separately)
- Unknown-key rejection (REQ-004, handled separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: scripts/shared/config_loader.py
