## Goal

Record this fix's resolution in the `## Known Deviations` section of `docs/adr/ADR-004-environment-failure-handling-policy.md`, following the existing `ADR-004-D1`/`ADR-004-D2` entry pattern, only after REQ-001–REQ-005 pass verification. (REQ-006; Documentation Impact)

## Scope

- Add a new entry to the `## Known Deviations` section documenting this fix's resolution.
- Follow the existing `ADR-004-D1`/`ADR-004-D2` entry pattern.

## Assumptions

- The existing `## Known Deviations` section has established entries covering `ADR-004-D1`/`ADR-004-D2`/`ADR-004-D3`/`CI-016`.
- The entry format follows the existing pattern: `ADR-004-D{N}-{description}` followed by a description of the deviation and its resolution status.

## Design decisions

- Use the same naming convention as existing entries: `ADR-004-D{N}` where `{N}` is the next available number.
- Include the specific requirements addressed (REQ-001–REQ-005) and their acceptance criteria.
- Document the resolution status as "Resolved" since this fix closes the gap.

## Alternatives considered

- Adding a separate ADR — unnecessary since this is a documentation record within the existing ADR-004.
- Updating the main body of ADR-004 — the Known Deviations section is the appropriate place for tracking individual deviations and their resolutions.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents registry publication for disabled servers.
- A disabled server excluded by this change will not appear in the registry's `_tools` dict, which is consistent with treating it as "not configured."

## Security considerations

- Preventing registry publication for disabled servers eliminates the possibility of a disabled server's tools being available for execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `publish_all()` restores the pre-fix behavior where disabled servers get their tools published to the registry.

## Implementation

### Target file

`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. **Phase 1: Documentation update**
   - After REQ-001–REQ-005 pass verification, add a new entry to the `## Known Deviations` section.

### Method

- Edit the `## Known Deviations` section — add a new entry documenting this fix's resolution.

### Details

**Step 1 — Documentation update:**

```markdown
# Before (existing ## Known Deviations section):
## Known Deviations

### ADR-004-D1-profile-config-model-still-present
...

### ADR-004-D2-production-config-validator-severity-downgrade
...

### ADR-004-D3-local-profile-re-addition-risk
...

### CI-016-production-config-validator-ci-gate
...
```

```markdown
# After:
## Known Deviations

### ADR-004-D1-profile-config-model-still-present
...

### ADR-004-D2-production-config-validator-severity-downgrade
...

### ADR-004-D3-local-profile-re-addition-risk
...

### ADR-004-D4-production-tool-safety-validation-fail-open
Status: Resolved

Description: Production tool-safety validation could silently skip checks on
registry failure (bare `except Exception:` returning `None` in
`_resolve_known_tools()`) and accept unknown security-profile values without
rejection. This was addressed by REQ-001–REQ-005: removing the broad exception
fallback, adding explicit `SecurityProfile` coercion/rejection, and injecting
authoritative known-tools from both runtime call sites. All safety-critical
checks remain unconditional across `SecurityProfile.PRODUCTION`.

Requirements addressed: REQ-001 (fail-closed registry resolution), REQ-002
(explicit known-tools injection), REQ-003 (canonical SecurityProfile model),
REQ-004 (unconditional safety-critical checks), REQ-005 (test coverage).

Acceptance criteria satisfied: AC-1 (production validation cannot succeed
without an authoritative tool set), AC-2 (registry failures produce actionable
validation errors), AC-5 (profile consistency), AC-6 (unknown profiles fail
during configuration construction), AC-7 (safety-critical checks remain fail
closed), AC-8 (profile-specific tests prove intended differences).

### CI-016-production-config-validator-ci-gate
...
```

## Validation plan

- Read-only verification: confirm the entry follows the existing `ADR-004-D1`/`ADR-004-D2`/`ADR-004-D3`/`CI-016` pattern.
- No code changes required — documentation-only change.

## Completion criteria

- [ ] Entry follows the existing `ADR-004-D{N}` naming convention.
- [ ] Entry documents all requirements addressed (REQ-001–REQ-005).
- [ ] Entry documents all acceptance criteria satisfied (AC-1, AC-2, AC-5, AC-6, AC-7, AC-8).
- [ ] Status marked as "Resolved".

## Out of scope

- Modifying `scripts/mcp_servers/shell/` (the shell-mcp server's own `command_allowlist` check is a separate defense layer).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
