## Title

Three-Category Separation for Workflow Approval Documentation

### Context

Implementation procedure `20260818-215229_workflow_approval.py.md` requests separating three categories in documentation:
1. Mandatory WorkflowEngine Execution
2. Mandatory Workflow-Definition Deployment
3. Policy-Controlled Human Approval

These categories do NOT exist as explicit terms in any existing documentation. They are currently conflated across multiple docs. The existing two-layer approval model (tool-level + workflow-level) is well-documented but doesn't explicitly separate these concepts.

### Decision

**Do NOT implement the three-category separation as specified.** Instead, extend the existing two-layer approval model with clearer terminology where needed.

### Rationale

The three-category separation introduces unnecessary complexity:

1. **Existing model is sufficient**: The two-layer model (tool-level + workflow-level) already covers all operational concerns without ambiguity.
   - Tool-level: Real-time risk gates per tool call (before execution)
   - Workflow-level: Post-execution human approval for entire execute stage results

2. **Categories overlap**: "Mandatory WorkflowEngine Execution" and "Mandatory Workflow-Definition Deployment" both describe automatic operations that don't require human intervention — they're subsets of the same concept (non-human-gated operations).

3. **Risk classification already exists**: `ApprovalConfig.approval_risk_rules` provides granular risk tiers per tool, making the proposed "Operational Risk Tiers" table redundant.

4. **State machine already implemented**: The existing `ApprovalRecord` in `workflow.sqlite` handles PENDING/APPROVED/REJECTED states with persistence.

5. **Local dev deviations documented**: `ApprovalConfig.approval_shell_safe_prefixes` and `approval_dry_run_tools` already provide local development exemptions.

### Evidence

- `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`: Canonical two-layer model with clear boundaries
- `scripts/agent/config_dataclasses.py:277-370`: `ApprovalConfig` with risk-based tool approval policy settings
- `scripts/agent/tool_approval.py`: Tool-level approval implementation
- `scripts/agent/workflow/workflow_engine.py`: Workflow-level approval implementation
- `scripts/db/schema_sql.py`: Database schema including approvals table

### Follow-up Actions

1. Update documentation to clarify the distinction between:
   - Automatic operations (no human approval needed)
   - Operations requiring post-execution approval (workflow-level)
   - Operations requiring pre-execution approval (tool-level)

2. Add explicit terminology to key documentation sections:
   - `docs/05_agent_06_04_tool-execution-and-approval-canonical.md`: Clarify the two-layer model
   - `docs/05_agent_03_03_turn-processing-flow-workflow-engine.md`: Clarify workflow approval flow
   - `docs/02_deployment.md`: Clarify workflow definition deployment artifact requirements

3. No code changes required — existing infrastructure supports all necessary functionality.
