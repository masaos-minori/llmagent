## Goal

Apply the approved DT-04 decision (Option A, 2026-11-18): delete the orphan
`log_approval_decision()` path from the audit module (REQ-007); `audit_approval()` remains the only
approval-event emitter (REQ-004).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- `log_approval_decision()` has no production caller (verified via `tools/scan_change_consumers.py --seed log_approval_decision`);
  consumers are tests and generated artifacts only.
- The `tool_approval` event emitted by `audit_approval()` (`:97-127`) is unchanged; the
  `escalation_reason` field is not added to it (rejected Option B).

## Design decisions
- Delete, do not wire: keeping two events for one decision was rejected (Option C conflicts with the
  no-duplication posture of ADR-014).
- The removal spans Plan rows 04/05/06 and companion/tests rows 17/18/19 in one commit, with the
  regenerated API artifacts (rows 33/34) in the same commit (release unit reason).

## Alternatives considered
DT-04 Options B/C in the Plan option table — rejected by the maintainer decision.

## Implementation
### Target file
`scripts/agent/tool_audit.py`
### Procedure
1. Delete `log_approval_decision()` (`:130-149`) and its emission of the `approval_decision` event.
2. Delete the now-unused import of `ApprovalOutcome` (`:20`, companion of Plan row 06) and any
   `ApprovalDecisionEvent` import left dangling by step 1 (`scripts/agent/shared/models.py` row 05).
3. Keep `audit_approval()` byte-for-byte identical.
### Method
Pure deletion; no signature or payload change on the live path.
### Details
- After deletion, `rg "log_approval_decision|ApprovalDecisionEvent" scripts/` must return no hits
  outside the regenerated artifacts (which are fixed by rows 33/34 in the same commit).
- The `escalation_reason` information stays available to `audit_approval()` callers as it is today;
  nothing is added to the event payload.

### Companion test files
- `tests/tools/test_check_compat_shims.py`
  - Procedure: keep the `("log_approval_decision(ctx, outcome)", False)` expectation at `:110` — the
    checker must keep asserting the name is not a compat shim after removal.
  - Validation: `uv run pytest tests/tools/test_check_compat_shims.py -q`.

## Compatibility considerations
- Removes a published public API from `docs/23_agent/agent_13_reference-api-generated.md:143` and
  `registry/manifests/agent_api.yaml:548-549`; both are regenerated (rows 33/34), never hand-edited.
- External consumers: none found (Plan UNK-08 closed by the grep inventory over `scripts/`, `tests/`,
  `docs/`, `registry/`).

## Security considerations
Audit posture is unchanged or stronger: one approval event instead of a second dead emitter.

## Rollback considerations
Revert the whole unit commit (symbols, tests, and regenerated artifacts share one commit); a
partial revert breaks the artifact drift gate.

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py tests/tools/test_check_compat_shims.py -q`
- `uv run python tools/generate_reference_table.py --check` in the same commit (rows 33/34).

## Completion criteria
`log_approval_decision()` no longer exists; `audit_approval()` is byte-identical; the compat-shim
expectation passes; no source reference to the removed symbols remains.

## Out of Scope
ADR-001 INV-11 wording (row 29), the orphan tests' own removal (rows 17/18), artifact regeneration
(rows 33/34).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the orphan path per Procedure/Method/Details | Pending | — | — | DT-04 approved Option A 2026-11-18 |
| 2 | Companion + rows 17/18 test removal in the same commit | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes `generate_reference_table.py --check` |

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
- **Requirement ID**: `REQ-007` (orphan approval-event cluster decision/removal), `REQ-004` (DT-04 decision)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/tool_audit.py`, `tests/tools/test_check_compat_shims.py`
