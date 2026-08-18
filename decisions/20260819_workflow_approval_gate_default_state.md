## Title

Workflow Approval Gate Default State

### Context

Uncertainty about whether the default approval state is approved/denied/pending.

### Decision

**Keep fail-closed default.** Unapproved operations require explicit approval.

### Rationale

`ApprovalConfig` defaults to `"medium"` risk level for tools not explicitly listed. This means unlisted tools default to requiring approval (fail-closed). This is the safe default.

### Evidence

- `scripts/agent/config_dataclasses.py:280`: Comment states "absent tools default to 'medium' (fail-closed)"
- `scripts/agent/config_dataclasses.py:281-299`: `approval_risk_rules` dict lists 18 tools with explicit risk levels
- Tools not in the list (e.g., `github_create_branch`, `github_create_pull_request`) default to `"medium"` which requires approval

### Follow-up Actions

None required. Current design is correct.
