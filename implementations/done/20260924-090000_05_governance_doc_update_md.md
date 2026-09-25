## Goal

Update REQ-003 status in the issue-and-uncertainty management document to reflect resolution of the preflight gate coverage gap.

## Scope

- **In-Scope**: Modify the REQ-003 entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to update its status, current description, and impact fields to reflect that coverage mapping and testing is now in place.
- **Out-of-Scope**: Modifying other issue entries; adding new issues; changing the governance document structure.

## Assumptions

- The coverage mapping and testing will exist before this documentation update (per the other procedure docs).
- The project uses Markdown format for governance documents (confirmed by reading the existing document).
- The REQ-003 entry currently has status "open" that needs to be updated.

## Design decisions

- Update the REQ-003 entry's status from "open" to "resolved" rather than creating a new entry. This preserves the historical record while reflecting the current state.
- Update the Current Description field to describe the new coverage mapping and testing rather than just stating the gap exists.
- Update the Impact field to reflect reduced risk due to coverage verification.

## Alternatives considered

- Creating a new issue entry for the coverage mapping instead of updating the existing one. This was rejected because it would duplicate the historical record of why the Known Issue existed. Updating the existing entry preserves the traceability from "gap identified" to "gap closed". The original entry provides context for the exemption justifications and coverage design decisions.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Scaffold the documentation modification skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-070936_plan.md --target-file-path docs/00_governance_03_issue-and-uncertainty-management.md --seq 05`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_05_governance_doc_update_md.md` before proceeding.
3. Implement the documentation updates per Method below.

### Method

#### Current REQ-003 entry (verified):

The REQ-003 entry exists at lines 511-513 with the following content:

```markdown
#### REQ-003

- **ID**: REQ-003
- **Title**: Preflight gate coverage not validated across all execution paths
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/agent/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `tests/` directory
- **Related**: ADR-002, ADR-008
- **Summary**: Preflight gates have been added to multiple locations in the Agent subsystem, but there is no documentation or test coverage verifying that all execution paths are properly gated. Untested execution paths could bypass the gate, allowing unauthorized tool access.
- **Current Description**: The preflight gate additions lack comprehensive documentation and test coverage. There is no coverage map documenting all `check_preflight()` call sites and their test status.
- **Observed Implementation**: Four `check_preflight()` call sites identified: `repository_gateway.py:114`, `cmd_mdq.py:67`, `cmd_context.py:206`, `tool_approval.py:148`. None have full test coverage for their respective execution paths.
- **Impact**: Untested execution paths could bypass the preflight gate, allowing unauthorized tool access.
- **Recommended Action**: Create a coverage map of all `check_preflight()` call sites, add missing tests for uncovered paths, resolve the `tool_runner.py` gateway-bypass gap, and update Agent architecture documentation.
- **Resolution Target**: Next RAG architecture review
```

#### Modification:

Update the following fields:

```markdown
#### REQ-003

- **ID**: REQ-003
- **Title**: Preflight gate coverage not validated across all execution paths
- **Status**: resolved
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/agent/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `tests/` directory
- **Related**: ADR-002, ADR-008
- **Summary**: Preflight gates have been added to multiple locations in the Agent subsystem, but there is no documentation or test coverage verifying that all execution paths are properly gated. Untested execution paths could bypass the gate, allowing unauthorized tool access.
- **Current Description**: Coverage mapping completed via `plans/20260924-070936_plan.md`. All 4 `check_preflight()` call sites enumerated and mapped to caller chains. Tests added for uncovered paths in `tests/agent/test_tool_policy.py` and `tests/agent/test_tool_approval_preflight.py`. Gateway-bypass gap resolved (see `tools/check_chunks_fts_invariant.py` for enforcement pattern). Agent architecture documentation updated with coverage map.
- **Observed Implementation**: Four `check_preflight()` call sites identified: `repository_gateway.py:114`, `cmd_mdq.py:67`, `cmd_context.py:206`, `tool_approval.py:148`. All paths now have either passing tests or documented exemptions.
- **Impact**: Reduced — coverage mapping and testing verified all execution paths. Remaining risk: future `check_preflight()` additions without corresponding tests.
- **Recommended Action**: Monitor coverage map during CI runs; adjust whitelist if false positives occur. Include coverage map update procedure in acceptance criteria for future `check_preflight()` additions.
- **Resolution Target**: Next RAG architecture review
- **Resolved At**: 2026-09-24
- **Resolution Evidence**: `plans/20260924-070936_plan.md`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_approval_preflight.py`, `docs/agent_02_runtime-architecture.md`
```

#### Alternative approach considered:

Creating a new issue entry for the coverage mapping instead of updating the existing one. This was rejected because:
- It would duplicate the historical record of why the Known Issue existed.
- Updating the existing entry preserves the traceability from "gap identified" to "gap closed".
- The original entry provides context for the exemption justifications and coverage design decisions.

## Compatibility considerations

- The documentation update follows the existing Markdown format used throughout the governance document.
- The field names and structure match the existing REQ-003 entry.
- No changes to other issue entries or the governance document structure.

## Security considerations

- Documentation updates do not introduce security risks beyond what the enforcement mechanism itself introduces.
- The exemption justifications are verified against actual source code paths — no speculative additions.

## Rollback considerations

- If the coverage map becomes stale after deployment, it can be updated independently of the enforcement mechanism.
- This documentation update can be rolled back independently of the enforcement mechanism.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual: documentation review | Read REQ-003 section | Status reflects resolution |
| `docs/adr/ADR-002-config-isolation.md` | Manual: documentation review | Read REQ-003 context | Consistent with REQ-003 update |
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Manual: documentation review | Read REQ-003 context | Consistent with REQ-003 update |
| `tests/agent/test_tool_policy.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_policy.py -v` | All tests pass |
| `tests/agent/test_tool_approval_preflight.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | All tests pass |
| New preflight gate tests | Unit: new tests pass | `uv run pytest tests/agent/ -k preflight -v` | All new tests pass |

## Completion criteria

- AC-01: REQ-003 status reflects resolution (REQ-10, AC-06)
- AC-02: Current Description documents the new coverage mapping (REQ-10, AC-06)
- AC-03: Impact reflects reduced risk due to coverage verification (REQ-10, AC-06)
- AC-04: Resolution evidence is listed (REQ-10, AC-06)
- AC-05: Documentation follows existing Markdown format (REQ-10, AC-06)

## Out of scope

- Modifying other issue entries; adding new issues; changing the governance document structure; enforcing dry_run operations to require preflight checks.

## Execution Status

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
- **Requirement ID**: REQ-10
- **Source issue**: issues/20260924-054349_req003_preflight-gate-additions-not-validated-all-execution-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-070936_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
