## Goal
Remove `MCPConfig.security_profile`'s `SecurityProfile.LOCAL` default and the
`__post_init__` coercion's implicit tolerance of a non-`SecurityProfile`
value.

## Scope
- **In-Scope**: `scripts/agent/config_dataclasses.py`'s `MCPConfig` dataclass
  field default and its `__post_init__` coercion only.
- **Out-of-Scope**: `SecurityProfile`'s own enum definition (row 1, must run
  after this row); `config_builders.py`'s fallback (row 3).

## Assumptions
- Must execute before row 1 (`scripts/shared/mcp_config.py`'s `LOCAL` member
  removal) — this file's `security_profile: SecurityProfile = SecurityProfile.LOCAL`
  default must stop referencing `LOCAL` before that member is deleted, or
  this file fails to import.

## Design decisions
- Set the field's default to `SecurityProfile.PRODUCTION` (the sole
  remaining value after row 1 lands) rather than removing the default
  entirely and making the field mandatory in every `MCPConfig(...)`
  construction call — a required-field change would ripple into every
  construction site across `scripts/agent/`, which is a larger, unrequested
  scope expansion beyond REQ-002's own ask (removing the *Local* default,
  not making the field mandatory).

## Alternatives considered
- Making `security_profile` a required constructor argument (no default):
  rejected per Design decisions — out of REQ-002's scope, and would require
  auditing every `MCPConfig(...)` call site across the codebase, which no
  Requirement in this Plan asks for.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Change `security_profile: SecurityProfile = SecurityProfile.LOCAL` to
   default to `SecurityProfile.PRODUCTION`.
2. Confirm `__post_init__`'s coercion (`if not isinstance(self.security_profile, SecurityProfile): self.security_profile = SecurityProfile(self.security_profile)`)
   requires no further change — it already fails via `ValueError` for any
   value that is not a valid `SecurityProfile` member, which becomes
   correctly stricter once `LOCAL` is removed (row 1) since `"local"` will
   then also raise.

### Method
Direct `Edit`, anchored on the exact field declaration (line 278, verified
2026-09-04).

### Details
Current (verified 2026-09-04):
```
security_profile: SecurityProfile = SecurityProfile.LOCAL
```
Change to:
```
security_profile: SecurityProfile = SecurityProfile.PRODUCTION
```
No other line in this dataclass needs modification — the `__post_init__`
coercion at lines 283-285 is generic and requires no edit.

## Compatibility considerations
Any test constructing `MCPConfig()` without an explicit `security_profile`
argument now gets `PRODUCTION` instead of `LOCAL` — this is the intended
behavior change; row 16 (`tests/agent/test_config_dataclasses.py`) updates
any test relying on the old default.

## Security considerations
None directly — removes a relaxed-by-default configuration path; net effect
is a security hardening.

## Rollback considerations
Single-line default-value edit under version control; revert via `git
revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Unit | `uv run pytest tests/agent/test_config_dataclasses.py -v` | Default `security_profile` is `PRODUCTION`; no `SecurityProfile.LOCAL` reference remains |

## Completion criteria
`MCPConfig.security_profile` defaults to `SecurityProfile.PRODUCTION`; no
`SecurityProfile.LOCAL` reference remains in this file.

## Out of scope
`SecurityProfile`'s own enum definition (row 1); `config_builders.py`'s
fallback default (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Must execute before row 1 (`scripts/shared/mcp_config.py`) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 16's own edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation impact owned by `adrprodonly`, sequenced after this Plan lands |

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
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/config_dataclasses.py
