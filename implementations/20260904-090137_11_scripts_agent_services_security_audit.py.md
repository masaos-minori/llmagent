## Goal
Make `audit_security_defaults()` and `_load_audit_config_or_warn()` fully
unconditional: remove `production_mode`'s gating of the audit-log values
(REQ-008), the `auth_token`-violation raise, the four audit-config-load
raise/warn branches, and the `ProductionConfigValidator().validate()`
call's `security_profile=` argument and result handling (REQ-005).

## Scope
- **In-Scope**: `scripts/agent/services/security_audit.py`'s
  `_load_audit_config_or_warn()` and `audit_security_defaults()` functions —
  every `production_mode`-conditional branch within them.
- **Out-of-Scope**: `load_shell_audit_config()`/`load_github_audit_config()`/
  `load_git_audit_config()`/`load_cicd_audit_config()` (imported from
  `agent.security_audit_config`, a different module, not touched by this
  row); the rest of `audit_security_defaults()`'s checks that do not
  reference `production_mode` (e.g. `lockdown`-gated checks, confirmed by
  direct read to be independent).

## Assumptions
- **Corrected 2026-09-04**: this row's scope is larger than this Plan's
  original evidence identified. The originally-cited line 177
  (`security_profile="production" if production_mode else "local"`) is a
  keyword argument to `ProductionConfigValidator().validate()`, not an
  "audit-log field" — REQ-008's actual target (the `profile_label`/
  `auth_required` strings used in a `logger.info(...)` call) is at lines
  69-70. Both are real, but distinct, findings; this document covers both,
  plus two more `production_mode` branches (`:88`, `:182`) discovered during
  this same re-verification.
- Coupled to row 5 (`startup_validation.py`), the sole caller of
  `audit_security_defaults()` — that row's call site must drop the
  `production_mode=production_mode` keyword argument once this row removes
  the parameter.

## Design decisions
- Remove `audit_security_defaults()`'s `production_mode: bool = False`
  parameter entirely, and correspondingly remove it from
  `_load_audit_config_or_warn()`'s signature — every internal branch on it
  becomes the always-fatal path, consistent with this Plan's other REQ-005
  rows.
- For the `security_profile=` argument to `ProductionConfigValidator().validate()`
  (line 177): hardcode to `security_profile="production"` rather than
  removing the keyword argument — `validate()`'s own signature (row 4) still
  accepts this parameter (it no longer affects severity, but a caller must
  still supply a valid value); hardcoding keeps this call site simple without
  requiring `validate()`'s signature to also change in this row.

## Alternatives considered
- Leaving `_load_audit_config_or_warn()`'s `production_mode` parameter in
  place and hardcoding `True` at each of its 4 call sites: rejected — same
  reasoning as row 7 (`retry_helper.py`): leaves a dead parameter that no
  caller may legitimately vary, inviting future regression.

## Implementation
### Target file
`scripts/agent/services/security_audit.py`

### Procedure
1. Remove `_load_audit_config_or_warn()`'s `production_mode: bool` parameter
   (verified 2026-09-04, line 33) and its `if production_mode: ... else: ...`
   branch (lines 39-47), always raising on `RuntimeError` from `loader()`.
2. Update all 4 call sites (lines 111, 165, 192, 218) to drop the
   `production_mode` positional argument.
3. Remove `audit_security_defaults()`'s `production_mode: bool = False`
   parameter (line 53).
4. Remove `profile_label`/`auth_required`'s conditional derivation (lines
   69-70) — hardcode the log message to state the single remaining posture,
   or remove the log line if it no longer conveys distinguishing
   information (implementer's call; re-read the surrounding log statement at
   execution time to decide).
5. Remove `if production_mode and violations:` (line 88) — always
   `raise RuntimeError(...)` when `violations` is non-empty; delete the
   subsequent `for v in violations: logger.warning(...)` fallback path.
6. Change `security_profile="production" if production_mode else "local"`
   (line 177) to `security_profile="production"`.
7. Remove `if production_mode:` (line 182) around the `result.errors`
   handling — always `raise RuntimeError(msg)` for each error; delete the
   `logger.warning`/`warnings.append` fallback path.
8. Update the module/function docstrings (lines 57, and
   `_load_audit_config_or_warn()`'s own docstring) to remove references to a
   non-production mode.

### Method
Direct `Edit` at the 8 sites listed above.

### Details
Repository evidence for every cited line: confirmed by direct read
2026-09-04 (`grep -n "production_mode" scripts/agent/services/security_audit.py`
returns exactly the line numbers cited in Procedure). Re-run this same `grep`
immediately before editing to confirm no further drift since this document's
creation.

## Compatibility considerations
Coupled to row 5 — `audit_security_defaults(ctx)`'s call site there must drop
the `production_mode=production_mode` keyword argument in the same overall
Plan execution.

## Security considerations
None directly — every change in this row removes a relaxed-validation path;
net effect is a broad security hardening across this file's entire audit
surface (auth_token, shell sandbox, cicd allowlist, git allowlist, tool
safety tiers, routing).

## Rollback considerations
Multi-site edit within a single file, under version control; revert via
`git revert` if needed, together with row 5.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/security_audit.py` | Unit | `uv run pytest tests/agent/test_agent_negative_paths.py -v` | Every audit-config load failure and every violation category raises `RuntimeError` unconditionally; no warning-only path remains |

## Completion criteria
No `production_mode` reference remains in this file; every previously-gated
raise/warn branch now always raises.

## Out of scope
`load_shell_audit_config()`/`load_github_audit_config()`/
`load_git_audit_config()`/`load_cicd_audit_config()`'s own implementations
(different module); lockdown-gated checks unrelated to `production_mode`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | mypy caught a self-introduced regression: `is not None` guards on `shell_cfg`/`git_cfg`/`github_cfg`/`cicd_cfg` were initially removed too aggressively — these loaders legitimately return `None` for "not installed" (ImportError), distinct from the removed "malformed config → warn" RuntimeError path; guards restored. Renamed `_load_audit_config_or_warn` to `_load_audit_config_or_raise` (no longer warns). **Additional-target-file ripple found at row 1's mypy check**: `scripts/agent/repl_health.py` (a backward-compat re-export shim, not a row in this Plan's table) re-exports `_load_audit_config_or_warn` by name — updated its import/`__all__` entry to the new name, the minimal mechanical fix required to avoid leaving `mypy scripts/` broken |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 20/21's own edits |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; `tests/agent/test_agent_negative_paths.py` 14 passed, `tests/agent/test_repl_health.py` 57 passed |
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
- **Requirement ID**: REQ-005, REQ-008
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/services/security_audit.py
