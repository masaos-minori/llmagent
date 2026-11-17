# Define the Agent tool approval policy and validation boundary

## Priority
High

## Summary
The Agent approval and validation path has unreachable rules, overlapping definitions, undefined values, and a conflict with ADR-014 INV-03. One decision covers the policy.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H03`; merged from ADRCHK-H03, H17, M29, M31, M32, M33, L19 (review findings N5, N30, N31, N47, N55, N56, N57)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- Approval rules are bypassed: `classify_risk` returns NONE as soon as a tool's tier is `READ_ONLY` or `WRITE_SAFE`, and `config/agent.toml` marks the file-write, git-write, index, and github-write tools `WRITE_SAFE`. Their `[approval_risk_rules]` entries, the protected-path escalation, and the recursive or force escalation never run. `approval_protected_paths` covers `allowed_root`, so every allowed write is under a protected path and the list has no effect.
- The validation boundary contradicts ADR-014: INV-03 forbids the Agent from duplicating path, allowlist, and argument validation, yet the Agent runs `check_allowed_root`, `check_allowed_repo`, and `validate_tool_arguments`, and `RepositoryGateway` calls itself the single write enforcement boundary although ADR-012 assigns enforcement to the server.
- Lenient parsing is applied to a main contract: when a tool schema has no `properties`, `tool_arg_validator.py` skips the extra-field check, but governance_02 allows lenient parsing only for inputs that are not the main contract.
- Plan mode has two sources: `plan_blocked_tools` omits some write tools while plan mode also checks tiers.
- An empty `approval_github_allowed_repos` has no defined meaning (deny all or no restriction), so it can fail open.
- Server roles are wrong: github has a search role but exposes write tools, cicd has a query role but exposes `trigger_workflow`, and `tool_concurrency_limits` has no entries for git and mdq.
- Two approval events exist (`approval_decision` and `tool_approval`), and ADR-001 INV-11 defines only `tool_approval`.

## Implementation Intent
- One documented evaluation order combines the tier, the explicit risk rules, and the escalation checks, and no configured rule is unreachable.
- ADR-014 INV-03 states which validations the servers own and which pre-flight checks the Agent keeps as non-authoritative defense in depth.
- Plan mode, the empty allowlist, server roles, and approval events each have one definition, and tests pin them.

## Target Files or Areas
- `scripts/agent/tool_policy.py`
- `scripts/agent/tool_arg_validator.py`
- scripts/agent/repository_gateway.py (docstring)
- `config/agent.toml`
- `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
- `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
- docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md (INV-11)
- `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
- `tests/agent/`

## Required Changes
- (no decision needed) Write a reachability report: for each tool in `tool_safety_tiers`, list which rules in `config/agent.toml` can apply.
- (no decision needed) Fix the `RepositoryGateway` docstring so it does not claim to be the single boundary.
- (no decision needed) Correct the server `role` values, and add the missing concurrency limits or document the default.
- (decision) Approval order: evaluate risk rules and escalations before the tier shortcut (recommended), or remove the rules that cannot apply. Narrow `approval_protected_paths` so it does not contain `allowed_root`, or state that this is intended.
- (decision) ADR-014 INV-03: narrow the invariant (recommended), or remove the Agent-side checks under a separate plan.
- (decision) Plan mode source: the tier or `plan_blocked_tools`.
- (decision) The meaning of an empty `approval_github_allowed_repos` (deny all recommended).
- (decision) Approval events: keep one, or define both in ADR-001.
- Reject unknown arguments when a schema has no `properties`, or reject such schemas at load.

## Constraints
- Do not change approval behavior before a decision is recorded; the reachability report is the first deliverable.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- Unit tests pin the result for a file write under `allowed_root` and for `delete_directory` with `recursive=true`.
- No rule in `config/agent.toml` is unreachable under the chosen order.
- Plan mode blocks every non-READ_ONLY tool from one configuration source (test).
- Tests pin the behavior of an empty repo allowlist and of a schema without `properties`.
- ADR-012, ADR-014, and the code docstrings agree on where enforcement happens.

## Testing Expectations
Unit tests under `tests/agent/` pinning each behavior above; run the full validation sequence and the ADR checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-001 (INV-11), ADR-003, ADR-014 (INV-03), and the approval configuration guide: state the evaluation order, the validation ownership, and the empty-allowlist meaning.

## Out of Scope
- Server-side validation changes in the MCP servers.
- Changing any tool's safety tier without a recorded decision.

## Dependencies
- `issues/20261117-123004_adrchk004_hot-reload-validation.md` depends on this issue's tier decisions (a bad hot reload can disable approval).

## Unresolved Questions
- The full approval call order is unknown. Needs `scripts/agent/tool_approval.py` and `scripts/agent/tool_runner.py` (paths assumed).
- How `role` is used at runtime is unknown. Needs `scripts/agent/config_dataclasses.py`.
- The module that emits `approval_decision` was not found.

## AI Implementation Instruction
- Produce the reachability report first and stop before any behavior change.
- For each decision task, write an option table and stop.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123003
- **Related target files**: `scripts/agent/tool_policy.py`; `scripts/agent/tool_arg_validator.py`; `scripts/agent/repository_gateway.py (docstring)`; `config/agent.toml`; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md (INV-11)`; `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`; `tests/agent/`
