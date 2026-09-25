## Goal

Include the preflight gate coverage map in Agent architecture documentation (`docs/agent_02_runtime-architecture.md`).

## Scope

- **In-Scope**: Add the preflight gate coverage map to the Agent runtime architecture document. Document all 4 `check_preflight()` call sites, their caller chains, gate status, test coverage, and exemption justifications.
- **Out-of-Scope**: Modifying the `check_preflight()` function logic itself; adding new gate conditions beyond what already exists; changes to MCP server preflight behavior; changes to Event Bus preflight behavior.

## Assumptions

- The project uses Markdown format for Agent architecture documentation (confirmed by reading the existing document).
- The coverage map should follow the same format as other sections in the Agent architecture document.
- dry_run operations are intentionally preflight-exempt because they are read-only previews.
- READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools).

## Design decisions

- Add the coverage map as a new section in the Agent architecture document rather than modifying existing sections. This preserves the historical record while documenting the current state.
- Use a table format for the coverage map to make it easy to scan and verify.
- Include exemption justifications explicitly so future reviewers can understand why certain paths are exempt.

## Alternatives considered

- Adding the coverage map to the existing "Tool Policy" section instead of creating a new section. This was rejected because it would mix the coverage map with the actual tool policy logic, making both harder to read. A separate section allows reviewers to quickly find the coverage information without navigating through the tool policy details. The coverage map is a dynamic artifact that needs frequent updates — keeping it separate makes version control easier.

## Implementation

### Target file

`docs/agent_02_runtime-architecture.md`

### Procedure

1. Scaffold the documentation modification skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-070936_plan.md --target-file-path docs/agent_02_runtime-architecture.md --seq 04`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_04_agent_arch_doc_update_md.md` before proceeding.
3. Implement the documentation updates per Method below.

### Method

#### Current Agent architecture document structure (verified):

The document exists at `docs/agent_02_runtime-architecture.md` and contains sections for Agent lifecycle, tool policy, and gateway configuration.

#### Modification:

Add a new section titled "Preflight Gate Coverage Map":

```markdown
## Preflight Gate Coverage Map

This section documents the coverage of all `check_preflight()` call sites across the Agent subsystem. Each entry includes the call site location, caller chain, gate status, test coverage, and exemption justification.

### Enumerated Call Sites

| # | Location | Caller Chain | Gate Status | Test Coverage | Exemption |
|---|---|---|---|---|---|
| 1 | `scripts/agent/repository_gateway.py:114` | `RepositoryGateway._gate_write()` → `RepositoryGateway.execute()` | Enforced | Partial (mocked in tests) | None |
| 2 | `scripts/agent/commands/cmd_mdq.py:67` | `_MdqMixin._execute_mdq()` → `/mdq <subcommand>` | Enforced | None | None |
| 3 | `scripts/agent/commands/cmd_context.py:206` | `_ContextMixin._cmd_diff()` → `/diff` | Enforced | None | None |
| 4 | `scripts/agent/tool_approval.py:148` | `check_approval()` → `run_approval_checks()` | Enforced | Partial (existing tests) | None |

### Exempt Paths

| Path | Justification |
|---|---|
| `repository_gateway.py::read_execute()` | READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools) |
| `tool_approval.py::build_preview()` | dry_run execution is preflight-exempt (read-only operation) |
| `tool_runner.py::run_tool_call()` when `gateway is None` | Gateway not yet configured; requires separate resolution |

### Future Gate Additions

When adding new `check_preflight()` calls, you MUST:

1. Add an entry to the coverage map above.
2. Ensure the new path has either a passing test or a documented justification for exclusion.
3. Update this section's acceptance criteria if the exemption rationale changes.
```

#### Alternative approach considered:

Adding the coverage map to the existing "Tool Policy" section instead of creating a new section. This was rejected because:
- It would mix the coverage map with the actual tool policy logic, making both harder to read.
- A separate section allows reviewers to quickly find the coverage information without navigating through the tool policy details.
- The coverage map is a dynamic artifact that needs frequent updates — keeping it separate makes version control easier.

## Compatibility considerations

- The documentation update follows the existing Markdown format used throughout the Agent architecture document.
- The coverage map format matches the table-based structure used elsewhere in the document.
- No changes to the Tool Policy or Gateway Configuration sections.

## Security considerations

- Documentation updates do not introduce security risks beyond what the enforcement mechanism itself introduces.
- The exemption justifications are verified against actual source code paths — no speculative additions.

## Rollback considerations

- If the coverage map becomes stale after deployment, it can be updated independently of the enforcement mechanism.
- This documentation update can be rolled back independently of the enforcement mechanism.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/agent_02_runtime-architecture.md` | Manual: documentation review | Read coverage map section | Coverage map present |
| `tests/agent/test_tool_policy.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_policy.py -v` | All tests pass |
| `tests/agent/test_tool_approval_preflight.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | All tests pass |
| New preflight gate tests | Unit: new tests pass | `uv run pytest tests/agent/ -k preflight -v` | All new tests pass |
| Governance docs | Manual: REQ-003 status update | Read REQ-003 section | Status updated |

## Completion criteria

- AC-01: Coverage map is included in Agent architecture documentation (REQ-04, AC-04)
- AC-02: All 4 `check_preflight()` call sites are mapped to their caller chains (REQ-01, AC-01)
- AC-03: Each mapped path has either a passing test or a documented justification for exclusion (REQ-02, AC-02)
- AC-04: Exempt paths are documented with justifications (REQ-02, AC-02)
- AC-05: Future gate additions require documentation updates as part of the acceptance criteria (REQ-05, AC-05)

## Out of scope

- Modifying the Tool Policy section; modifying the Gateway Configuration section; adding new gate conditions beyond what already exists; enforcing dry_run operations to require preflight checks.

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
- **Requirement ID**: REQ-04
- **Source issue**: issues/20260924-054349_req003_preflight-gate-additions-not-validated-all-execution-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-070936_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: docs/agent_02_runtime-architecture.md
