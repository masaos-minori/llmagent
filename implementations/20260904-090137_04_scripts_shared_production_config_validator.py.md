## Goal
Remove `is_production`-conditional downgrading in `ProductionConfigValidator`,
making every strict-mode, tool-safety-tier, approval-risk-floor, and
`allowed_tools` violation an unconditional error.

## Scope
- **In-Scope**: `scripts/shared/production_config_validator.py`'s
  `_record()`/`_format_error_or_warning()` severity-routing helpers and
  `validate()`'s `is_production` computation.
- **Out-of-Scope**: `validate_unknown_tool_safety_tiers()` (already
  unconditional — always returns errors, no `is_production` gate, confirmed
  by direct read); callers of `validate()` (row 3 already passes the correct
  `security_profile` argument).

## Assumptions
- `validate()`'s `security_profile` parameter itself is not removed by this
  row — `security_profile: SecurityProfile | str = "local"` remains a valid
  parameter signature (its own default is out of REQ-004's scope; callers
  already pass an explicit value per row 3), but the parameter's *value* no
  longer changes `validate()`'s severity output once this row's edit lands.

## Design decisions
- Remove `_format_error_or_warning()`'s branching entirely and always
  `errors.append(msg)`, rather than keeping the branch but hardcoding
  `is_production=True` at every call site — the latter would leave dead
  parameters (`is_production`) threaded through `_record()`/
  `_format_error_or_warning()`/`validate()` with no remaining caller-visible
  effect, which `skills/DESIGN.md` Pythonic safety constraints implicitly
  discourages (no placeholder/dead logic) and which would need its own
  future cleanup Plan. Removing the parameter now, while every call site is
  already being touched by this Plan, is the smaller total change.
- Keep the `warnings` return list and field on `ConfigValidationResult` —
  other, unrelated warning-producing paths in this module (none currently
  exist, confirmed by direct read) might be added later; removing the field
  entirely is a larger API change than REQ-004 asks for.

## Alternatives considered
- Hardcoding `is_production=True` at every `_record()` call site instead of
  removing the parameter: rejected per Design decisions — leaves dead
  parameter threading that must be cleaned up separately.

## Implementation
### Target file
`scripts/shared/production_config_validator.py`

### Procedure
1. Remove `validate()`'s `is_production = security_profile == "production"`
   computation (line 125, verified 2026-09-04).
2. Change every `self._record(errors, warnings, msg, is_production)` call
   (7 call sites within `validate()`) to `errors.append(msg)` directly, or
   keep `_record()`/`_format_error_or_warning()` as thin wrappers with the
   `is_production` parameter removed (implementer's choice — see Details).
3. Remove `_format_error_or_warning()`'s `if is_production: ... else: ...`
   branch — always route to `errors`.

### Method
Direct `Edit` across the 4 sites within this file: the `is_production`
computation, the 7 `_record(...)` call sites (all pass `is_production` as
the last positional argument), `_record()`'s own signature, and
`_format_error_or_warning()`'s body.

### Details
Current (`_format_error_or_warning`, verified 2026-09-04, lines 212-221):
```
@staticmethod
def _format_error_or_warning(
    msg: str, is_production: bool
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if is_production:
        errors.append(msg)
    else:
        warnings.append(f"[local/development] {msg}")
    return errors, warnings
```
Simplify to always append to `errors` and remove the `is_production`
parameter from this function, `_record()`, and every call site within
`validate()`. Re-verify the exact 7 call sites at execution time (`rg -n
"self\._record\(" scripts/shared/production_config_validator.py`) rather than
assuming this document's count is still exact once earlier rows in this Plan
land.

## Compatibility considerations
Every caller of `validate()` (currently only `config_builders.py`, row 3)
now receives only errors, never `[local/development]`-prefixed warnings, for
what used to be Local-profile-tolerated violations — this is the intended
behavior change (AC-2).

## Security considerations
None directly — this removes the relaxed-validation path entirely; net
effect is a security hardening.

## Rollback considerations
Single-file edit under version control; revert via `git revert` if needed.
No other file depends on `_record()`/`_format_error_or_warning()`'s internal
signature (both are private, `_`-prefixed).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/production_config_validator.py` | Unit | `uv run pytest tests/shared/test_production_config_validator.py -v` | Every strict-mode/tool-tier/approval-risk/allowlist violation is an unconditional error; no warnings are produced |

## Completion criteria
`ProductionConfigValidator.validate()` never returns a warning for any
violation category it checks; `is_production`/`security_profile`-conditional
severity routing no longer exists in this file.

## Out of scope
`validate_unknown_tool_safety_tiers()` (already unconditional); `validate()`
callers (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Found 6 call sites, not 7 as originally estimated (lines 131,137,150,159,179,185); simplified `_format_error_or_warning` to `return [msg], []` |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 13's own edit, executed in the same cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; 33 tests passed. Full-suite diff deferred to end of batch |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: confirmed via `docs/00_index.md`'s Document References by Task table during code-implementation Step 5 — the only `mcp_config.py`-matching row covers `TransportType`/`StartupMode`/`HealthcheckMode`, not `SecurityProfile`; no changed file in this cycle has a matching task-scope row |

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
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/shared/production_config_validator.py
