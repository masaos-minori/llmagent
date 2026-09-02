## Goal

Close the ambiguity gap in `ProductionConfigValidator.security_profile` — when `security_profile` is absent from `agent.toml`, the validator must use `local` as the default rather than allowing an ambiguous None value.

## Scope

Modify `scripts/shared/production_config_validator.py` only. Add explicit default handling for the `security_profile` key.

## Assumptions

- `ProductionConfigValidator.__init__()` reads `security_profile` from config without a default fallback at line 86.
- When `security_profile` is absent, `cfg.get("security_profile")` returns `None`, which is then passed to `SecurityProfile(None)` causing undefined behavior.
- The intended default is `"local"` — confirmed by the existing codebase convention.

## Design decisions

- Add explicit default: `security_profile_val = cfg.get("security_profile", "local")` instead of relying on implicit None handling.
- This is a minimal change that closes the specific gap without affecting other validators.

## Alternatives considered

- Adding a new `validate_security_profile_default()` method. Rejected because it adds unnecessary complexity; a simple default fallback is sufficient.
- Raising an error when `security_profile` is missing. Rejected because the existing design allows graceful degradation with a sensible default.

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

Add explicit default handling for `security_profile` in `ProductionConfigValidator.__init__()`.

### Method

Edit line 86 of `scripts/shared/production_config_validator.py`: replace `security_profile_val = cfg.get("security_profile")` with `security_profile_val = cfg.get("security_profile", "local")`.

### Details

1. Open `scripts/shared/production_config_validator.py`
2. Find the `security_profile_val = cfg.get("security_profile")` assignment (line 86)
3. Replace with `security_profile_val = cfg.get("security_profile", "local")`
4. Verify the change is consistent with the existing `SecurityProfile` enum usage at line 87

## Compatibility considerations

- Existing deployments with explicit `security_profile` values in `agent.toml` are unaffected.
- Deployments without `security_profile` set will now explicitly use `"local"` instead of passing `None` to `SecurityProfile()`.

## Security considerations

- This is a security-relevant change: a missing `security_profile` should not silently fall back to an insecure default. Using `"local"` as the explicit default ensures predictable behavior.

## Rollback considerations

- Revert the default addition: `cfg.get("security_profile", "local")` → `cfg.get("security_profile")`. No other rollback needed.

## Validation plan

Run `uv run pytest tests/shared/test_production_config_validator.py -v` to confirm all existing tests pass and the new default behavior is correct.

## Completion criteria

- Explicit default `"local"` added to `security_profile` getter
- All existing tests in `tests/shared/test_production_config_validator.py` pass
- No regressions in any dependent code

## Out of scope

- Changes to other validators' default handling (handled by their respective documents)
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: scripts/shared/production_config_validator.py
