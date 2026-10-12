## Goal

Confirm / record that `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` states the HALF_OPEN single-trial constraint: HALF_OPEN allows exactly one in-flight trial and concurrent calls while a trial is in flight are rejected with an "unavailable" error result (REQ-004 / ACC-004).

## Scope

`docs/22_mcp/mcp_03_01_dispatch-and-routing.md` only — the circuit-breaker trial-behavior description. No code or other doc is modified here.

## Assumptions

- This doc is the canonical mcp-domain description of dispatch-time health gating.
- Other docs (e.g. `docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md`) are context-only references and are not modified here.

## Design decisions

- The acceptance criterion is satisfied either by documenting the constraint OR by confirming the doc already states it. Verification is the chosen path because the current wording already covers all required points (see Implementation > Details).

## Alternatives considered

- Editing the doc to add the single-trial wording: not needed, because line 48 already states "exactly one in-flight trial dispatch", "further concurrent calls are rejected with an `"unavailable"` error result", and "released on success, failure, or cancellation so the slot never leaks", with code cross-references. Rewriting would duplicate existing content.

## Implementation

### Target file

`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`.

### Procedure

1. Locate the circuit-breaker / HALF_OPEN trial description (grep `HALF_OPEN`, `trial`, `half_open`).
2. Confirm the current wording states all three required points:
   - exactly one in-flight trial dispatch per server;
   - concurrent calls while a trial is in flight rejected with an `"unavailable"` error result;
   - the trial flag released on success, failure, or cancellation.
3. If any point is missing or contradicts the code, add/clarify it (and, if the doc has a decision table, add a "reject concurrent trial" row). Otherwise record that no modification is required.

### Method

Read only the trial-behavior section; do not reformat or touch unrelated sections. Keep prose consistent with the surrounding "Implementation Notes (Current behavior)" list.

### Details

- Current state (verified): the "Implementation Notes (Current behavior)" bullet at line 48 already states the single-trial constraint and cites `scripts/shared/mcp_health.py::McpServerHealthRegistry.acquire_trial` and `scripts/shared/tool_transport_invoker.py::_check_health`. No modification is required to meet ACC-004.
- The doc describes observable behavior, not implementation; leave the code-level details to the source files.

## Compatibility considerations

- Documentation-only; no code/config impact. Ensure no other doc states a contradictory trial count (context-only refs such as `mcp_06_07_mcp-failure-diagnosis.md` are out of scope but should not be silently made inconsistent).

## Security considerations

- N/A.

## Rollback considerations

- Revert the doc edit if any was made; the pre-change wording is preserved in git history.

## Validation plan

- Documentation review: confirm the single-trial + concurrent-rejection behavior is stated and consistent with the code.
- If the doc was edited, run `uv run python tools/check_docs_structure.py` and `uv run python tools/check_docs_quality.py` and confirm clean.

## Completion criteria

- The doc states exactly-one-in-flight trial and concurrent rejection (or is confirmed to already do so); no contradictory wording remains; doc structure/quality checks pass.

## Out of scope

- Other circuit-breaker documentation.
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation review only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy not applicable to a doc edit |
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
- **Requirement ID**: REQ-004 / ACC-004
- **Source issue**: issues/done/20261007-154049_halfopen01_limit-half_open-trial-calls-to-one.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-163326_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-090000
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md
