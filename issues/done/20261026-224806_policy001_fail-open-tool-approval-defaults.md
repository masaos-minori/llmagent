# Close the fail-open defaults in tool approval policy

## Priority
High

## Summary
Tool approval currently auto-approves every tool that is not explicitly tiered in
config, and an unset `allowed_tools` allows all tools. Change the defaults so an
unknown or unconfigured tool does not execute unprompted when approval is required.

## Background
From a python-code-review pass over the REPL turn/command execution path (finding
F-003). Evidence (Explicit in code) in `scripts/agent/tool_policy.py`:
- a tool absent from `mcp_tool_tiers` defaults to tier `"READ_ONLY"`;
- `_TIER_TO_RISK` maps `WRITE_SAFE` to `RiskLevel.NONE`;
- `RiskLevel.NONE` returns approval immediately, before any `approval_mode` check —
  so even `approval_mode="require"` auto-approves these tools;
- empty `allowed_tools` returns allowed for every tool name.

## Problem
A newly added MCP server's write-capable tools execute without any prompt by
default, and there is no allowlist restriction unless the operator explicitly
configures one. Missing validation at a trust boundary: the safe outcome depends
on config the operator is not required to provide.

## Reason for Change
Security-sensitive behavior in the default configuration. Changing the default now
is cheap; once more MCP servers are registered, a silent fail-open default becomes
an operational risk.

## Implementation Intent
Make the deny-safe path explicit: unknown tools get a risk tier that requires
approval (or an explicit configuration error), and the meaning of an empty
`allowed_tools` is decided and documented (deny, or allow-all with an explicit
opt-in flag). Keep the approval flow itself unchanged — this is a defaults-and-
classification change, not a new approval mechanism.

## Target Files or Areas
- `scripts/agent/tool_policy.py` (tier lookup default, risk mapping, allowed_tools check)
- `scripts/agent/services/config_validators.py` (tier validation boundaries)
- agent config docs (approval model section)

## Required Changes
- Choose and implement a safe default for tools missing from `mcp_tool_tiers`
  (require approval, or reject the tool with a clear error).
- Reconsider `WRITE_SAFE -> RiskLevel.NONE`: a write-capable tier mapping to
  no-risk should at least respect `approval_mode="require"`.
- Define empty `allowed_tools` semantics (deny vs. explicit allow-all) and enforce
  it in one place.
- Update config validation and docs to match the chosen semantics.

## Constraints
- Existing configured setups must keep working: tools already tiered in
  `mcp_tool_tiers` must not start prompting differently without a config change.
- Changes must be reflected in the config validator so operators get actionable
  errors, not runtime surprises.

## Acceptance Criteria
- With `approval_mode="require"` and an unregistered tool name, approval is NOT
  auto-granted (test).
- The chosen empty-`allowed_tools` semantics is enforced and covered by tests.
- Docs state the default behavior of both `mcp_tool_tiers` absence and empty
  `allowed_tools`.
- Existing approval tests pass or are updated with explicit justification.

## Testing Expectations
- Unit tests: unregistered tool + `approval_mode="require"` → prompt required.
- Unit tests: empty vs. non-empty `allowed_tools` behavior.
- Regression tests for already-tiered tools (behavior unchanged).

## Documentation Impact
The approval-model docs must state: default tier for untiered tools, the risk of
each tier, and `allowed_tools` semantics (intent, boundaries, failure behavior).
This is a docs/code mismatch fix as well as a behavior change.

## Out of Scope
- Changes to the approval UI/prompt UX.
- MCP server-side permission systems.
- Per-session approval caching.

## Dependencies
- N/A: none

## Unresolved Questions
- 不明: whether auto-approval of `WRITE_SAFE` tools is an intended product decision
  (intentional convenience) or an oversight — confirm with the project owner before
  choosing the new default.
- Whether empty `allowed_tools` should deny-by-default (breaking change for current
  users) or stay allow-all with an explicit opt-in.

## AI Implementation Instruction
Change defaults only in the policy/validator layer; do not restructure the
approval flow or the REPL prompt path. Do not silently break currently working
tiered-tool configurations. If the product intent behind `WRITE_SAFE` auto-approval
cannot be confirmed, implement the safest option that keeps tests green and record
the decision in the docs update.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224806
- **Related target files**: `scripts/agent/tool_policy.py`, `scripts/agent/services/config_validators.py`, agent config docs
