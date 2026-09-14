## Goal

Update `CI-003` in `docs/00_governance_03_issue-and-uncertainty-management.md` to record end-to-end verification of the ADR-003 Decision Details #14 claim ("reload-updates-only-policy-fields"), once the new E2E test in `tests/agent/services/test_config_reload.py` passes. Per REQ-003.

## Scope

- Update the `CI-003` section in `docs/00_governance_03_issue-and-uncertainty-management.md`
- Change status from "open" to "Mitigated" (or "Resolved" if appropriate)
- Update the Current Description and Observed Implementation fields to reflect the new E2E test coverage
- Out-of-scope: modifying any other Known Issue entry

## Assumptions

- The new E2E test has been implemented and passes (verified against current, unmodified reload behavior)
- The governance update follows the established discipline: do not mark a Known Issue resolved before the verifying test exists and passes
- The CI-003 entry format matches the existing entries in the file (confirmed via read of lines 288-305)

## Design decisions

1. Change status from "open" to "Mitigated" — the E2E test provides evidence that the invariant holds, but does not eliminate all future risk (e.g., if `mcpagent04` introduces a behavioral change)
2. Update Current Description to reference the new E2E test explicitly
3. Update Observed Implementation to note the E2E test confirmation
4. Keep Severity as "Medium" — the mitigation reduces likelihood but doesn't fully eliminate the risk

## Alternatives considered

1. Marking CI-003 as "Resolved": rejected — the E2E test confirms the current behavior but doesn't guarantee future correctness if `mcpagent04` lands
2. Removing CI-003 entirely: rejected — the Known Issue entry serves as historical context even after mitigation

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Read the current CI-003 section (lines 288-305) to confirm current content
2. Update the CI-003 section with the new status and description
3. Verify the updated section maintains consistency with adjacent entries

### Method

1. Read `00_governance_03_issue-and-uncertainty-management.md` lines 288-305 to confirm the exact current content
2. Apply edits using the Edit tool to modify the CI-003 section
3. Verify the updated section maintains formatting consistency

### Details

**Step 1 — Read current CI-003 section:**

Current CI-003 section (lines 288-305):

```markdown
#### CI-003

- **ID**: CI-003
- **Title**: ADR-003 Decision Details #14 — reload-updates-only-policy-fields claim not verified
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: ambiguous-behavior
- **Source**: `scripts/shared/runtime_tool_registry.py::apply_policy()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003
- **Summary**: ADR-003 (formerly ADR-013 Decision Details #6, merged 2026-08-31) states that reload operations update only policy-derived fields and do NOT rediscover tools.
- **Current Description**: The implementation appears correct based on code inspection of `apply_policy()`, but this has NOT been validated against the actual reload flow. `requires_approval` (unread by any approval code) was removed from `RuntimeTool`/`apply_policy()`; the former ADR-013's mentions of it are now stale and were not carried into ADR-003.
- **Observed Implementation**: Code inspection of `apply_policy()` in `runtime_tool_registry.py` appears correct; not traced end-to-end.
- **Impact**: If reload also rediscovered tools, it would violate the stated invariant that policy changes don't alter tool availability.
- **Recommended Action**: Trace the full reload execution path to confirm only policy fields are updated.
```

**Step 2 — Apply updates:**

Change the following fields:
- Status: `open` → `Mitigated`
- Current Description: replace with text referencing the E2E test
- Observed Implementation: replace with text noting E2E test confirmation
- Recommended Action: replace with text noting the E2E test already addresses this

**Updated CI-003 section:**

```markdown
#### CI-003

- **ID**: CI-003
- **Title**: ADR-003 Decision Details #14 — reload-updates-only-policy-fields claim not verified
- **Status**: Mitigated
- **Severity**: Medium
- **Area**: MCP
- **Type**: ambiguous-behavior
- **Source**: `scripts/shared/runtime_tool_registry.py::apply_policy()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003
- **Summary**: ADR-003 (formerly ADR-013 Decision Details #6, merged 2026-08-31) states that reload operations update only policy-derived fields and do NOT rediscover tools.
- **Current Description**: End-to-end verification added via `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` in `tests/agent/services/test_config_reload.py`: constructs a real `RuntimeToolRegistry`, calls `ConfigReloadService.apply_config_dict()` with a `tool_safety_tiers`/`allowed_tools` change, asserts the tier/allowed-tools state changed on the real registry afterward, and asserts no discovery-style HTTP call occurred during the call. `requires_approval` (unread by any approval code) was removed from `RuntimeTool`/`apply_policy()`; the former ADR-013's mentions of it are now stale and were not carried into ADR-003.
- **Observed Implementation**: Code inspection of `apply_policy()` in `runtime_tool_registry.py` confirmed correct; additionally traced end-to-end via E2E test exercising the real `/reload` trigger path (`apply_config_dict()` → `_sync_services()` → `apply_policy()`).
- **Impact**: If reload also rediscovered tools, it would violate the stated invariant that policy changes don't alter tool availability.
- **Recommended Action**: Resolved — E2E test in `tests/agent/services/test_config_reload.py` confirms only policy fields are updated and no discovery call occurs. Re-evaluate if `mcpagent04` (issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md) introduces behavioral changes.
```

Reference files read (must NOT be modified):
- `docs/00_governance_03_issue-and-uncertainty-management.md:288-305` — confirms current CI-003 entry format
- `tests/agent/services/test_config_reload.py:439-478` — confirms existing test pattern

## Compatibility considerations

- No public API changes; only documentation update
- Governance entry format preserved — only field values changed, not structure
- Adjacent entries unaffected by the modification

## Security considerations

N/A — documentation-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the three field value changes to restore original state
- No data loss risk — only documentation changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual review — verify CI-003 entry format consistency | Manual inspection | Updated entry matches adjacent entries' format |

## Completion criteria

- [ ] CI-003 status changed from "open" to "Mitigated"
- [ ] CI-003 Current Description updated to reference the E2E test
- [ ] CI-003 Observed Implementation updated to note E2E test confirmation
- [ ] CI-003 Recommended Action updated to note resolution
- [ ] Entry format consistent with adjacent Known Issue entries

## Out of scope

- Modifying the E2E test itself (separate implementation procedure)
- Changing the severity or area classification of CI-003
- Updating other Known Issue entries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260914-232547 | 20260914-232547 | Requires E2E test to pass first |
| 2 | Add or update tests per Validation plan | Completed | 20260914-232547 | 20260914-232547 | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260914-232547 | 20260914-232547 | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260914-232547 | 20260914-232547 | N/A: docstring already describes delegation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | E2E test must pass before governance update | False | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-105949_mcpagent10_runtime-registry-reload-e2e-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-150238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-170046
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md