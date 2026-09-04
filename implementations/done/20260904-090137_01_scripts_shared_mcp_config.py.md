## Goal
Remove `SecurityProfile.LOCAL` from the `SecurityProfile` enum, per the
architecture-owner sign-off (full removal, not single-member retention).

## Scope
- **In-Scope**: `scripts/shared/mcp_config.py`'s `SecurityProfile(StrEnum)`
  definition only.
- **Out-of-Scope**: every consumer of `SecurityProfile` (rows 2-11 of this
  Plan own their own edits); `FailurePolicy` (already resolved, REQ-010).

## Assumptions
- This row must execute **last** among the source-file edits (Phase 3 of the
  Plan's Implementation steps) — every consumer (`config_dataclasses.py`,
  `config_builders.py`, `production_config_validator.py`,
  `startup_validation.py`, `mcp_health.py`, `retry_helper.py`,
  `startup_mcp_starter.py`, `mcp_tool_discovery.py`, `config_reload.py`,
  `security_audit.py`) must stop referencing `SecurityProfile.LOCAL` before
  the enum member is deleted, or those files fail to import.

## Design decisions
- Delete the `LOCAL` member entirely rather than deprecating it with a
  `# noqa` alias — the architecture-owner sign-off explicitly confirmed full
  removal (`UNK-01` resolved), and the source Issue's Constraints prohibit a
  silent compatibility alias (REQ-009's own wording).
- Leave `SecurityProfile` itself as a `StrEnum` with a single `PRODUCTION`
  member, rather than deleting the enum/field entirely — multiple consumers
  (`config_dataclasses.py`'s `MCPConfig.security_profile`,
  `production_config_validator.py`'s `validate()` parameter) still type-check
  against `SecurityProfile`, and collapsing it to a bare boolean would be a
  larger, unrequested API change across all 11 consumer files. Re-verify this
  choice against each consumer row as they execute — if every consumer row
  turns out not to need the type marker, a future Plan can remove the enum
  entirely.

## Alternatives considered
- Deleting the whole `SecurityProfile` enum/type now: rejected per Design
  decisions — out of this row's own scope to decide unilaterally when 10
  other rows still consume the type; the Plan's own Implementation intent
  defers this exact judgment call to "the implementer verifies during
  plan-to-implementation-procedure."

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
Remove the `LOCAL = "local"` line from the `SecurityProfile(StrEnum)`
definition, leaving only `PRODUCTION = "production"`.

### Method
Direct `Edit`, anchored on the exact enum body.

### Details
Current (verified 2026-09-04, lines 62-67):
```
class SecurityProfile(StrEnum):
    """Deployment security profile for MCP auth enforcement."""

    LOCAL = "local"
    PRODUCTION = "production"
```
Remove the `LOCAL = "local"` line. Update the class docstring if it still
implies two profiles exist (re-read at execution time).

## Compatibility considerations
Breaking for any caller still referencing `SecurityProfile.LOCAL` after this
edit — this is why this row runs last (see Assumptions), once rows 2-11 have
already removed their own references.

## Security considerations
None directly — this removes a code path that permitted relaxed validation;
net effect is a security hardening, not a new risk.

## Rollback considerations
Single-enum-member removal under version control; revert via `git revert` if
a still-undiscovered consumer breaks. Re-run `rg -rn "SecurityProfile.LOCAL"
scripts/ tests/` before finalizing to catch any consumer this Plan's 22-row
inventory missed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Unit | `uv run pytest tests/shared/test_mcp_config.py -v` | No `SecurityProfile.LOCAL` reference remains; import succeeds |
| Repository-wide | Static | `rg -rn "SecurityProfile.LOCAL" scripts/ tests/` | Zero matches |

## Completion criteria
`SecurityProfile` has exactly one member, `PRODUCTION`; no file under
`scripts/`/`tests/` references `SecurityProfile.LOCAL`.

## Out of scope
Any consumer file's own edit (rows 2-11); `FailurePolicy`; deciding whether
`SecurityProfile` itself should eventually be removed entirely.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Executed last as designed, after all consumer rows landed. `mypy scripts/` surfaced one additional-target-file ripple: `scripts/agent/repl_health.py` (backward-compat re-export shim, not a row in this table) re-exported row 11's renamed `_load_audit_config_or_warn` by name — fixed as part of row 11's cycle (see that doc's Notes), not a `SecurityProfile.LOCAL` issue itself |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 15's own edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; `mypy scripts/` clean (399 files); `tests/shared/test_mcp_config.py` 32 passed. Repository-wide `rg -rn "SecurityProfile.LOCAL" scripts/ tests/` returns zero matches in `scripts/`; one known, out-of-scope match remains in `tests/integration/test_production_security_regression.py` — a forward-looking regression suite written ahead of this Plan (and `loopbackonly`/`mcpauth`) landing, using `xfail(strict=False)` markers that safely tolerate the resulting `AttributeError` without breaking the suite (confirmed: 6 passed, 1 skipped, 2 xfailed, 1 xpassed). That file's own docstring documents that its markers should be removed and re-verified once each named dependency Plan lands — flagged as a recommended follow-up, not fixed in this cycle (not a row in this Plan's frozen table) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation impact owned by `adrprodonly` (`plans/20260903-093353_plan.md`), sequenced after this Plan lands |

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
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/shared/mcp_config.py
