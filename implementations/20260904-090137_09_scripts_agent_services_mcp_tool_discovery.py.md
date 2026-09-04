## Goal
Remove the `security_profile == PRODUCTION` term from
`McpToolDiscoveryService._is_fatal_severity()`, making duplicate-tool/drift-
finding severity depend only on `strict`.

## Scope
- **In-Scope**: `_is_fatal_severity()`'s method body and docstring only.
- **Out-of-Scope**: `_is_fatal_severity()`'s 3 call sites (`_build_drift_findings()`,
  `_check_tool_definitions_finding()`'s two branches) — they call the method
  unchanged; no edit needed there since the fix is centralized in the method
  itself. The already-resolved `required_in_local`/`required_in_production`
  classification branch elsewhere in this file (per
  `plans/done/20260901-102432_plan.md`'s Out-of-Scope note) — distinct code,
  not touched by this row.

## Assumptions
- None beyond the Plan's own Assumptions section.

## Design decisions
- Edit only `_is_fatal_severity()`'s body, not its 3 call sites — since all
  three already delegate to this one method, fixing the method's return
  value automatically fixes all three call sites' behavior without touching
  them, minimizing the diff.
- Keep the method itself (do not inline `self._is_strict()` at each of the 3
  call sites) — the method already exists as the single point of truth for
  this severity formula; removing it would be an unrequested refactor.

## Alternatives considered
- Inlining `self._is_strict()` at each of the 3 call sites and deleting
  `_is_fatal_severity()`: rejected — unrequested refactor beyond REQ-006's
  ask; the method already correctly centralizes the formula, only the
  formula's content needs to change.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
Change `_is_fatal_severity()` to return `self._is_strict()` directly,
removing the `or (self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION)`
term.

### Method
Direct `Edit`, anchored on the exact method body (verified 2026-09-04, lines
371-380).

### Details
Current:
```python
def _is_fatal_severity(self) -> bool:
    """Return True when findings should be FATAL per the unified severity scheme.

    `is_fatal = strict or (security_profile == PRODUCTION)` — applies to all
    findings emitted by this service (duplicates, drift, tool-definitions,
    malformed-capabilities).
    """
    return self._is_strict() or (
        self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
    )
```
After:
```python
def _is_fatal_severity(self) -> bool:
    """Return True when findings should be FATAL per the unified severity scheme.

    `is_fatal = strict` — applies to all findings emitted by this service
    (duplicates, drift, tool-definitions, malformed-capabilities).
    """
    return self._is_strict()
```
Remove the now-unused `SecurityProfile` import (line 48) if no other
reference to `SecurityProfile` remains in this file (re-check via `rg -n
"SecurityProfile" scripts/agent/services/mcp_tool_discovery.py` at execution
time — this file's module docstring at line 34 also quotes the old formula
and must be updated to match).

## Compatibility considerations
Duplicate-tool, drift, tool-definition, and malformed-capability findings now
depend only on `strict` (`tool_definitions_strict`); a deployment relying on
`security_profile == PRODUCTION` alone (without `tool_definitions_strict`
also set) to get FATAL severity will now get WARNING instead unless
`tool_definitions_strict` is also enabled — flag this in the Plan's
Validation plan manual review, since it is a behavior narrowing, not merely a
refactor (note: `REQ-004`'s edit to `production_config_validator.py` already
makes `tool_definitions_strict=False` an unconditional error at startup, so
in practice `tool_definitions_strict` will always be `True` once this Plan
fully lands — this narrowing is therefore not reachable in the post-Plan
steady state).

## Security considerations
None directly — the practical effect (per Compatibility considerations) is
unchanged once `REQ-004` also lands, since `tool_definitions_strict` becomes
unconditionally required.

## Rollback considerations
Single-method edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | Unit + Integration | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_runtime_tool_routing_integration.py -v` | `_is_fatal_severity()` returns `self._is_strict()`'s value only |

## Completion criteria
`_is_fatal_severity()` no longer references `SecurityProfile`/
`security_profile`; its docstring matches its actual formula.

## Out of scope
The 3 call sites' own code (unchanged); the already-resolved
`required_in_local`/`required_in_production` classification branch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by rows 17-18's own edits |
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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
