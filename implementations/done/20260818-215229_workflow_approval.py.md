## Goal

Clarify workflow execution and define high-risk operation approval policy by distinguishing between mandatory workflow execution/deployment and policy-based human approval, and formalizing the latter for high-risk tasks.

## Scope

**In-Scope:**
- Explicitly separate "Mandatory WorkflowEngine Execution," "Mandatory Workflow-Definition Deployment," and "Policy-Controlled Human Approval" in all relevant documentation (Overview, Deployment, Agent, workflow, ADRs).
- Formally specify approval requirements for high-risk operations including file writes/deletions, shell command execution, git commits/pushes, GitHub changes, CI/CD execution, database maintenance.
- Associate specific approval requirements with predefined operational risk tiers.
- Define the expected system behavior for approval: rejection, expiration, cancellation, and resumption of pending approvals.
- Specify permitted deviations for local development environments.
- Ensure workflow definitions and configurations can effectively implement the documented approval policies.

**Out-of-Scope:**
- Changes to existing MCP server implementations unless required by the unified policy.
- Changes to deployment infrastructure beyond what's needed for security enforcement.
- Changes to other systems' integration points (only internal security architecture).

## Assumptions

- The project already has some governance documents (e.g., `00_governance_03_evidence-labels.md`, `00_governance_07_needs-confirmation-inventory.md`, `00_governance_04_known-issues-template.md`) but they're inconsistently applied (verify current implementation against each claim).
- Evidence blocks need to be standardized across all documentation (check current evidence block usage).
- Uncertainty markers need to be extracted into a central inventory (check current uncertainty marker usage).
- Known issues need to follow a common template (check current known issues format).

## Design decisions

- Create three distinct categories: Mandatory Execution, Mandatory Deployment, Policy-Controlled Approval — eliminates ambiguity about when human approval is required.
- Use operational risk tiers (Critical, High, Medium, Low) — enables consistent decision-making across areas.
- Require explicit approval state machine — handles rejection, expiration, cancellation, and resumption.
- Allow local dev environment deviations — balances safety with developer productivity.

## Alternatives considered

- Keep approval policy implicit — rejected because it causes inconsistency and makes auditing difficult.
- Use binary approval (yes/no) — rejected because it doesn't capture nuanced risk levels.
- Apply same approval rules everywhere — rejected because local dev needs flexibility.

## Implementation

### Procedure

#### Part A: Separate three categories in documentation

1. Search for existing category descriptions:
   ```bash
   rg -n "WorkflowEngine\|workflow.*execution\|deployment.*policy\|human.*approval" docs/
   ```
2. For each area (Overview, Deployment, Agent, workflow, ADRs), update to clearly distinguish:
   - **Mandatory WorkflowEngine Execution**: Operations that must run automatically without human intervention.
   - **Mandatory Workflow-Definition Deployment**: Operations that deploy workflow definitions to production.
   - **Policy-Controlled Human Approval**: Operations that require explicit human approval before execution.

### Method

Part A — Update documentation section:

```markdown
<!-- BEFORE -->
The agent executes workflows and deploys them to production.

<!-- AFTER -->
The agent distinguishes three categories:

1. **Mandatory WorkflowEngine Execution**: Automatic operations that run without human intervention (e.g., scheduled data sync).
2. **Mandatory Workflow-Definition Deployment**: Deployment of workflow definitions to production (requires CI/CD pipeline).
3. **Policy-Controlled Human Approval**: Operations requiring explicit human approval (see §High-Risk Operation Approval below).
```

### Details

- Three categories clearly separated — eliminates ambiguity.
- Examples provided for each category — helps readers understand scope.

---

#### Part B: Specify approval requirements for high-risk operations

1. Search for existing high-risk operation references:
   ```bash
   rg -n "file.*write\|shell.*exec\|git.*push\|CI/CD\|database.*maintenance" docs/
   ```
2. Define approval requirements per operation type:
   ```markdown
   ## High-Risk Operation Approval
   
   | Operation | Risk Tier | Approval Required | Expiration |
   |-----------|-----------|-------------------|------------|
   | File write (production) | Critical | Yes | 24h |
   | File delete (production) | Critical | Yes | 24h |
   | Shell exec (production) | Critical | Yes | 24h |
   | Git commit (production) | High | Yes | 48h |
   | Git push (production) | Critical | Yes | 24h |
   | GitHub change (production) | High | Yes | 48h |
   | CI/CD execution (production) | Critical | Yes | 24h |
   | Database maintenance (production) | High | Yes | 48h |
   | File write (local dev) | Low | No | — |
   | Shell exec (local dev) | Low | No | — |
   ```

### Method

Part B — Add approval table to documentation:

```markdown
### Local Development Deviations

Local development environments are exempt from approval requirements for:
- File write operations
- Shell command execution
- Git commit operations

These exemptions apply only to local development environments and do not extend to staging or production.
```

### Details

- Table follows project convention — clear and actionable.
- Expiration times defined — prevents indefinite approval states.
- Local dev deviations specified — balances safety with productivity.

---

#### Part C: Associate approval requirements with operational risk tiers

1. Define risk tier criteria:
   ```markdown
   ## Operational Risk Tiers
   
   | Tier | Criteria | Example |
   |------|----------|---------|
   | Critical | Irreversible, affects production | Git push, CI/CD execution |
   | High | Reversible but significant impact | Git commit, database maintenance |
   | Medium | Minor impact, easily reversible | Config change |
   | Low | No production impact | Local dev operations |
   ```

### Method

Part C — Map operations to risk tiers:

```python
# BEFORE: no risk tier classification
def execute_operation(op_type: str):
    # Execute operation...

# AFTER: risk tier classification added
from enum import Enum

class RiskTier(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

RISK_TIERS = {
    "git_push": RiskTier.CRITICAL,
    "git_commit": RiskTier.HIGH,
    "config_change": RiskTier.MEDIUM,
    "local_dev": RiskTier.LOW,
}

def execute_operation(op_type: str):
    tier = RISK_TIERS.get(op_type, RiskTier.LOW)
    if tier == RiskTier.CRITICAL:
        require_human_approval()
    elif tier == RiskTier.HIGH:
        require_human_approval()
    # ...
```

### Details

- Risk tier classification is explicit — enables consistent decision-making.
- Approval logic tied to risk tier — ensures appropriate controls.
- Default tier is LOW — safe fallback for unknown operations.

---

#### Part D: Define approval state machine

1. Define approval states:
   ```markdown
   ## Approval State Machine
   
   ### States
   - PENDING: Approval requested, awaiting response
   - APPROVED: Approval granted
   - REJECTED: Approval denied
   - EXPIRED: Approval expired without response
   - CANCELLED: Approval cancelled by requester
   
   ### Transitions
   PENDING → APPROVED (by approver)
   PENDING → REJECTED (by approver)
   PENDING → EXPIRED (after timeout)
   PENDING → CANCELLED (by requester)
   APPROVED → EXECUTED (operation executed)
   REJECTED → CLOSED (no further action)
   EXPIRED → CLOSED (no further action)
   CANCELLED → CLOSED (no further action)
   ```

### Method

Part D — Implement approval state machine:

```python
class ApprovalState(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Approval:
    """Approval state machine."""
    
    def __init__(self, request_id: str, timeout_hours: int):
        self.request_id = request_id
        self.state = ApprovalState.PENDING
        self.timeout_hours = timeout_hours
        self.created_at = datetime.now()
    
    def approve(self) -> None:
        """Approve the request."""
        if self.state != ApprovalState.PENDING:
            raise ValueError(f"Cannot approve in state {self.state}")
        self.state = ApprovalState.APPROVED
    
    def reject(self) -> None:
        """Reject the request."""
        if self.state != ApprovalState.PENDING:
            raise ValueError(f"Cannot reject in state {self.state}")
        self.state = ApprovalState.REJECTED
    
    def cancel(self) -> None:
        """Cancel the request."""
        if self.state != ApprovalState.PENDING:
            raise ValueError(f"Cannot cancel in state {self.state}")
        self.state = ApprovalState.CANCELLED
    
    def check_expiration(self) -> None:
        """Check if the approval has expired."""
        if self.state == ApprovalState.PENDING:
            elapsed = (datetime.now() - self.created_at).total_seconds() / 3600
            if elapsed > self.timeout_hours:
                self.state = ApprovalState.EXPIRED
```

### Details

- State machine enforces valid transitions — prevents invalid states.
- Timeout handling implemented — prevents indefinite approval states.
- Error messages follow project convention — clear and actionable.

---

#### Part E: Specify permitted deviations for local development

1. Define local dev deviations:
   ```markdown
   ## Local Development Deviations
   
   ### Permitted Deviations
   - File write operations: No approval required
   - Shell command execution: No approval required
   - Git commit operations: No approval required
   
   ### Restrictions
   - Deviations apply only to local development environments
   - Staging and production environments require full approval
   - Deviations must be documented in configuration
   ```

### Method

Part E — Add local dev deviation config:

```toml
# config/approval.toml

[deviation.local]
enabled = true
operations = ["file_write", "shell_exec", "git_commit"]

[deviation.staging]
enabled = false
operations = []

[deviation.production]
enabled = false
operations = []
```

### Details

- Configuration-driven — allows easy modification without code changes.
- Deviations explicitly scoped to local dev — prevents accidental bypass.
- Staging/production deviations disabled by default — safe defaults.

---

#### Part F: Ensure workflow definitions can implement approval policies

1. Search for existing workflow definition patterns:
   ```bash
   rg -n "workflow.*definition\|workflow.*config\|workflow.*template" docs/ scripts/
   ```
2. For each workflow definition, add approval requirement field:
   ```yaml
   # workflow_definition.yaml
   name: deploy_production
   steps:
     - name: build
       type: mandatory_execution
     - name: test
       type: mandatory_execution
     - name: deploy
       type: policy_controlled_approval
       risk_tier: critical
       timeout_hours: 24
   ```

### Method

Part F — Add approval field to workflow definition:

```yaml
# BEFORE:
name: deploy_production
steps:
  - name: deploy
    type: deployment

# AFTER:
name: deploy_production
steps:
  - name: deploy
    type: policy_controlled_approval
    risk_tier: critical
    timeout_hours: 24
```

### Details

- YAML format follows project convention — human-readable and version-controllable.
- Approval fields added to workflow definition — ensures consistency.
- Risk tier and timeout specified — enables automated enforcement.

## Compatibility considerations

- Adding approval state machine does not affect existing workflow definitions — original behavior preserved.
- Risk tier classification may change existing security outcomes — verify before deploying.
- Local dev deviations are backward compatible — existing local dev configurations continue to work.
- Workflow definition updates do not affect runtime behavior — purely configuration-level.

## Security considerations

- This plan introduces security controls — must be reviewed by security team before deployment.
- Approval state machine enforces valid transitions — prevents invalid states.
- Risk tier classification ensures appropriate controls — prevents unauthorized access.
- Local dev deviations are explicitly scoped — prevents accidental bypass.

## Rollback considerations

- Revert approval state machine: remove `Approval` class and related imports.
- Revert risk tier classification: remove `RiskTier` enum and mappings.
- Revert local dev deviations: restore original configuration.
- Revert workflow definition updates: restore original YAML structure.
- No schema changes — rollback is purely code-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All modified docs | Manual review: verify no broken cross-references | Visual inspection of each changed document | No broken links, no misleading content |
| All modified docs | Automated: verify no duplicate sections remain | `rg -n "Deprecated Items\|Canonical Source Rule" docs/` — check for remaining raw text vs. links | Only links to canonical docs remain |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |
| Generated inventory | Manual verification against active configuration | Visual inspection | Inventory matches config |
| CI pipeline | Stale output detection | Trigger CI build | Warning displayed for stale output |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260818_09_issue.md
- Source requirement: requires/20260818-172200_require.md
- Source plan: plans/20260818-185336_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-215229
- Related target files: docs/**/*.md, scripts/workflow/*.py, config files, ADRs
