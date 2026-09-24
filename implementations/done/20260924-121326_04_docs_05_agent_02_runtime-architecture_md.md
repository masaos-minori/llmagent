# Implementation Procedure: Include Preflight Gate Coverage Map in Agent Architecture Documentation

## Goal

Include the preflight gate coverage map in Agent architecture documentation at `docs/05_agent_02_runtime-architecture.md`, per REQ-04.

## Scope

- Modify `docs/05_agent_02_runtime-architecture.md`
- Add a new section documenting the preflight gate coverage map
- Document all 4 `check_preflight()` call sites with their caller chains, gate status, and test coverage

## Assumptions

- The Agent runtime architecture document is `docs/05_agent_02_runtime-architecture.md` (confirmed by UNK-01 resolution)
- The coverage map should follow the existing document structure (sections with headings, bullet points)
- The document uses Markdown format with Japanese headers (consistent with other Agent docs)

## Design decisions

- Add a new top-level section `## Preflight Gate Coverage` after the existing sections
- Use a table format for the coverage map (consistent with the plan's Enumerated Call Sites table)
- Document both enforced paths and exempt paths
- Include ongoing maintenance requirements (REQ-07 / AC-07)

## Alternatives considered

- **Add to existing Known Limitations section**: Would mix enforcement gaps with architectural limitations. Separate section keeps concerns distinct.
- **Create a separate document**: Would fragment the architecture documentation. Keeping it within the runtime architecture doc provides better discoverability.

## Implementation

### Target file

`docs/05_agent_02_runtime-architecture.md`

### Procedure

1. Read the current document to find the appropriate insertion point
2. Add a new `## Preflight Gate Coverage` section
3. Include the coverage map table and exemption documentation
4. Document the ongoing maintenance requirement

### Method

**Step 1: Locate the insertion point**

The document has these sections:
- Related Documents
- Purpose
- Responsibility Boundary
- Key Constraints
- Operational Notes
- Known Limitations

Insert the new section after `Known Limitations` (or before it if that section is empty).

**Step 2: Add the Preflight Gate Coverage section**

```markdown
## Preflight Gate Coverage

`check_preflight()` の呼び出しサイトとそのテストカバレッジを文書化する。
未テストの実行経路はゲートを迂回する可能性があるため、すべての経路にテストまたは正当化が必要。

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
| `repository_gateway.py:execute()` line 85-86 (`if op == OperationType.READ`) | READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools). No separate `read_execute()` method exists. |
| `tool_approval.py:check_approval()` via `ApprovalDecisionType.DRY_RUN` | dry_run execution is preflight-exempt (read-only operation). No separate `build_preview()` method exists; handled via `DryRun` decision type. |
| `tool_runner.py:run_tool_call()` line 116-119 (`else` branch) | Gateway not yet configured; requires separate resolution. This path bypasses both the gateway and the preflight gate. |

### Gateway-Bypass Gap Analysis

Three distinct patterns exist where `tools.execute()` is called directly without going through the gateway:

**Pattern 1: Preflight gate present, gateway bypass** (cmd_mdq.py, cmd_context.py)
- These paths have `check_preflight()` gates but bypass the gateway.
- They are partially covered but inconsistent with the gateway-centric enforcement model.

**Pattern 2: No preflight gate, no gateway** (tool_runner.py)
- Critical gap: neither preflight nor gateway protection.
- Priority 1: Resolve by adding preflight check in the `else` branch.
- Priority 2: Standardize all write/delete/API-write operations through the gateway.

### Ongoing Maintenance

Coverage map accuracy must be maintained over time. Future changes to gate placement must update this map as part of the acceptance criteria (REQ-07 / AC-07). Any new `check_preflight()` addition requires a corresponding test or documented exception.
```

### Details

- **REQ-04**: The coverage map must be included in Agent architecture documentation
- **AC-04**: The coverage map is included in Agent architecture documentation
- **AC-07**: Coverage map accuracy is maintained over time; future changes to gate placement must update the map

## Compatibility considerations

- The section is added as a new top-level heading — does not modify existing content
- Uses mixed English/Japanese consistent with the existing document style
- Table formatting follows the existing Markdown conventions used elsewhere in the document

## Security considerations

- No security impact — this is a documentation update only

## Rollback considerations

- To revert, remove the added section from git history
- Reverting would lose important security boundary documentation

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| Agent architecture doc | Manual: documentation review | Read coverage map section | Coverage map present |

## Completion criteria

- [ ] `docs/05_agent_02_runtime-architecture.md` contains a `## Preflight Gate Coverage` section
- [ ] Coverage map table includes all 4 `check_preflight()` call sites
- [ ] Exempt paths table documents all 3 exemption cases
- [ ] Gateway-bypass gap analysis documents all 3 patterns
- [ ] Ongoing maintenance requirement is documented

## Out of scope

- Modifying the `check_preflight()` function logic itself
- Adding new gate conditions beyond what already exists
- Changes to MCP server preflight behavior
- Changes to Event Bus preflight behavior

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260924-160235 | 20260924-160610 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260924-160610 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260924-160610 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Generated at**: 20260924-121326
- **Related target files**: docs/05_agent_02_runtime-architecture.md