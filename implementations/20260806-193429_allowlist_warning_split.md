## Goal

Split conflated Agent-layer and MCP-server-layer allowlist warning descriptions in MCP documentation to accurately reflect their independent warning mechanisms.

## Scope

- **In-Scope**:
  - Update `docs/04_mcp_05_01_access-control-and-allowlists.md` regarding `cicd-mcp` `workflow_allowlist` warnings.
  - Update `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` regarding `cicd-mcp` `workflow_allowlist` warnings.
  - Update `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` regarding `cicd-mcp` `workflow_allowlist` warnings.
- **Out-of-Scope**:
  - Fixing `shell-mcp` warning conflations (to be handled in a separate issue).
  - Modifying any source code.

## Assumptions

1. The user wants the documentation to be accurate about the dual-layer warning mechanism (Agent vs. Server).
2. The exact wording of existing warnings needs to be read from each file before making replacements.

## Design decisions

- Split the unified warning statement into two distinct items per layer: Agent REPL process and cicd-mcp server process.
- Include trigger conditions, destinations, and exact messages for each layer separately.
- Cross-reference `05_01` from `05_03` and `05_05` rather than duplicating the full description.

## Alternatives considered

- Keep the unified statement but add a note distinguishing layers: rejected because it leaves ambiguity for readers who need precise operational guidance.
- Delete the cicd-mcp section entirely: rejected because readers lose useful information about the server-side warning mechanism.

## Compatibility considerations

- Readers who previously relied on the conflated description will now see two distinct warning paths.
- No API contract changes — this is purely a documentation correction.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the warning messages change in production, the documentation should be updated accordingly.
- If the cross-reference approach causes navigation issues, revert to inline descriptions.

## Implementation

### Target file

`docs/04_mcp_05_01_access-control-and-allowlists.md`

### Procedure

**Phase 2: Update access-control-and-allowlists.md**

1. Read the file to find exact lines for `cicd-mcp` `workflow_allowlist` warnings.
2. Replace the unified warning statement with two distinct items:
   - **Agent REPL process**: trigger condition, destination, exact message.
   - **cicd-mcp server process**: trigger condition, destination, exact message.
3. Ensure consistency with the `github-mcp` `protected_branches` description pattern.
4. Check and update summary table if necessary.

### Method

Verification via grep + direct file edit.

### Details

```bash
# Locate cicd-mcp workflow_allowlist warnings
grep -n "workflow_allowlist\|cicd.*warn\|cicd.*警告" docs/04_mcp_05_01_access-control-and-allowlists.md
```

After reading the exact context:
- Split the unified warning into two bullet points:
  1. Agent REPL: "When `workflow_allowlist` is violated during Agent execution, the Agent REPL emits a warning log."
  2. cicd-mcp server: "When `workflow_allowlist` is violated during cicd-mcp tool invocation, the cicd-mcp server process emits a warning log."
- Update the summary table row for `cicd-mcp` if it currently shows a single warning entry.

### Target file

`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure

**Phase 3: Update fail-open-fail-closed-and-risk-tiers.md**

Update `cicd-mcp` `workflow_allowlist` mention to cross-reference `05_01` for the detailed split description.

### Method

Direct file edit.

### Details

```bash
# Locate cicd-mcp workflow_allowlist mentions
grep -n "workflow_allowlist\|cicd.*warn" docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
```

Replace the cicd-mcp `workflow_allowlist` warning description with prose such as:
> For the detailed split warning mechanism (Agent vs. Server), see [access-control-and-allowlists](04_mcp_05_01_access-control-and-allowlists.md).

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

**Phase 4: Update mdq-enforcement-and-lockdown.md**

Update `cicd-mcp` `workflow_allowlist` mention to cross-reference `05_01` for the detailed split description.

### Method

Direct file edit.

### Details

```bash
# Locate cicd-mcp workflow_allowlist mentions
grep -n "workflow_allowlist\|cicd.*warn" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

Replace the cicd-mcp `workflow_allowlist` warning description with prose such as:
> For the detailed split warning mechanism (Agent vs. Server), see [access-control-and-allowlists](04_mcp_05_01_access-control-and-allowlists.md).

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Documentation files | Manual verification of content accuracy | `cat` / `grep` | Warnings are correctly split into Agent and Server layers. |

## Out of scope

- Source code modifications (`scripts/`).
- Fixes for `shell-mcp` warning conflations.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-145645_require.md
- Source plan: plans/20260804-143146_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-193429
- Related target files: docs/04_mcp_05_01_access-control-and-allowlists.md, docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md, docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
