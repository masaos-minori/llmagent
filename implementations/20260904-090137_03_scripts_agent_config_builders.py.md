## Goal
Remove the `"local"` fallback default in `build_agent_config()` so the
configuration resolves to the single remaining `SecurityProfile` value
unconditionally.

## Scope
- **In-Scope**: `scripts/agent/config_builders.py`'s
  `security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))`
  line only.
- **Out-of-Scope**: `ProductionConfigValidator.validate()` (row 4);
  `MCPConfig`'s own default (row 2).

## Assumptions
- Must execute before row 1 (`SecurityProfile.LOCAL` removal) — this line's
  fallback string `"local"` must stop being a valid `SecurityProfile` member
  reference target before that member disappears, though since this is a
  string literal (not `SecurityProfile.LOCAL` attribute access), it will not
  raise an `ImportError`; it will instead raise `ValueError` at runtime if a
  config ever omits the key and this line is not also fixed — this row must
  still land to avoid that runtime failure once `LOCAL` no longer exists.

## Design decisions
- Change the fallback to `"production"` (matching row 2's dataclass-level
  default) rather than removing the `.get()` fallback and requiring the key
  to always be present — `config/agent.toml`'s `security_profile` key is
  itself being removed by row 12 (REQ-009), so after this Plan lands, the
  config file will *not* set this key at all; the fallback must resolve to
  the correct (sole remaining) value in that case, not raise.

## Alternatives considered
- Requiring `security_profile` to always be present in `cfg` (raise if
  missing): rejected — REQ-009 explicitly removes the key from
  `config/agent.toml`, so requiring its presence would make every normal
  startup fail immediately after this Plan's own `config/agent.toml` edit
  lands, contradicting the Plan's own Implementation intent ("Production-grade
  behavior the sole, unconditional behavior").

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
Change the fallback string from `"local"` to `"production"`.

### Method
Direct `Edit`, anchored on the exact line (447, verified 2026-09-04).

### Details
Current (verified 2026-09-04):
```
security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))
```
Change to:
```
security_profile_val = SecurityProfile(cfg.get("security_profile", "production"))
```
No other line in `build_agent_config()` requires modification for this
Requirement.

## Compatibility considerations
A config file that still sets `security_profile = "local"` (e.g. an
un-migrated deployment) will now raise `ValueError` from
`SecurityProfile("local")` — this is the intended, unconditional-rejection
behavior REQ-009 requires, not a regression to fix here.

## Security considerations
None directly — removes a relaxed-by-default configuration path.

## Rollback considerations
Single-line default-value edit under version control; revert via `git
revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_builders.py` | Unit | `uv run pytest tests/agent/test_repl_health.py -v` | Config with no `security_profile` key resolves to `PRODUCTION`; `"local"` raises `ValueError` |

## Completion criteria
The fallback resolves to `"production"`; a config omitting `security_profile`
no longer silently runs relaxed validation.

## Out of scope
`ProductionConfigValidator.validate()`'s own logic (row 4); `MCPConfig`'s
dataclass-level default (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Verified exact match to cited line 447; no drift |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | No test change needed yet — `SecurityProfile.LOCAL` still exists at this point in the batch, so existing tests pass unmodified; test-file rows (13/20/21) still land later in this batch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; `tests/agent/test_repl_health.py` 62 passed. Full-suite diff deferred to end of batch (see row 22) |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/config_builders.py
