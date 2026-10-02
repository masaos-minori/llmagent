# Implementation Procedure: Fix stale governance paths in docs/10_adr/ADR-013-eventbus-authentication-authorization.md

## Goal

Replace stale `docs/governance_0N_*` path references in `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` with actual existing paths under `docs/00_governance/governance_0N_*`.

## Scope

- Modify only `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`.
- In-Scope: Replace stale paths on lines 87, 281, 302, and 356.
- Out-of-Scope: Changing any other content in the file.

## Assumptions

- The correct paths are `docs/00_governance/governance_01_documentation-policy.md` and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (confirmed by filesystem inspection).

## Design decisions

- **Approach**: Direct string replacement — replace `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_01_documentation-policy.md` on lines 302 and 356, and `docs/governance_03_issue-and-uncertainty-management.md` with `docs/00_governance/governance_03_issue-and-uncertainty-management.md` on lines 87 and 281.

## Alternatives considered

None — direct replacement is the only sensible approach for stale paths.

## Implementation

### Target file

`docs/10_adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

Replace the stale path strings on lines 87, 281, 302, and 356 with the correct paths.

### Method

Edit `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`:

**Line 87:** Change `docs/governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

**Line 281:** Change `docs/governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

**Line 302:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

**Line 356:** Change `docs/governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`

### Details

Line 87 currently reads:
```
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).
```

Change to:
```
- Correcting the stale `CI-001` status/Recommended-Action text in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (pre-existing documentation inconsistency unrelated to this Issue's stated Target Files).
```

Line 281 currently reads:
```
`docs/governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-008 (No Production Authentication Model for Event Bus HTTP API, High severity, resolved 2026-09-14) and CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, resolved 2026-09-15) are both resolved. Residual gaps from EVENTBUS-008 (token with no configured consumer_id allowlist entry has consumer-identity validation skipped — fail-open) are tracked separately in `issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`.
```

Change to:
```
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-008 (No Production Authentication Model for Event Bus HTTP API, High severity, resolved 2026-09-14) and CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, resolved 2026-09-15) are both resolved. Residual gaps from EVENTBUS-008 (token with no configured consumer_id allowlist entry has consumer-identity validation skipped — fail-open) are tracked separately in `issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`.
```

Line 302 currently reads:
```
- **Approval Reference**: `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Change to:
```
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
```

Line 356 currently reads:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Change to:
```
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
```

Only the path strings change; surrounding text is preserved.

## Compatibility considerations

- The corrected paths resolve to existing files (`docs/00_governance/governance_01_documentation-policy.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).

## Security considerations

N/A — path string correction only.

## Rollback considerations

Revert to the original path strings if the correction introduces unintended side effects.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` | Path resolution | `grep -rnE "docs/governance_0[0-4]_" docs/10_adr/ADR-013-eventbus-authentication-authorization.md` | No matches |
| `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` | File existence | `test -f docs/00_governance/governance_01_documentation-policy.md && test -f docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Files exist |

## Completion criteria

- All `docs/governance_0N_*` paths on lines 87, 281, 302, and 356 of `ADR-013-eventbus-authentication-authorization.md` resolve to existing files.
- No remaining `docs/governance_0N_*` patterns in `ADR-013-eventbus-authentication-authorization.md`.

## Out of scope

- Other stale paths in `ADR-013-eventbus-authentication-authorization.md` (if any).
- Changes to other files.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-003 |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test needed for path string fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-003 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No documentation update needed |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
