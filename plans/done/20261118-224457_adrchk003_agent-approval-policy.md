## Goal
- Establish a verified, evidence-backed picture of which Agent approval-policy mechanisms are actually
  reachable in the current code and configuration, record that picture as the first deliverable, and then
  bring the approval configuration, its documentation, and the ADR decision records into agreement with a
  maintainer-approved policy — removing the unreachable and orphaned approval paths instead of leaving them
  as apparent controls.

## Priority
High

## Scope
- **In-Scope**:
  - Reachability report for `agent/tool_policy.py::classify_risk()` and its four inputs
    (`approval_risk_rules`, `tool_safety_tiers`, `shared/tool_constants.py` defaults, `approval_protected_paths`
    escalation) under the shipped `config/agent.toml`.
  - Documentation of the deterministic evaluation order and of the `approval_protected_paths` ↔
    `allowed_root` interaction.
  - Decision records (option tables, maintainer approval required) for: tier/rule redundancy, protected-path
    semantics, the orphan `approval_decision` event path, argument-validation strictness for schemas without
    `properties`, the Agent/MCP write-enforcement boundary wording, and explicit `tool_concurrency_limits`
    entries.
  - Removal or activation of the orphan `log_approval_decision` / `ApprovalDecisionEvent` / `ApprovalOutcome`
    cluster.
  - Correction of the stale documentation reference in `scripts/agent/tool_approval.py`.
  - ADR Decision/Invariant wording alignment for the approval-boundary ADRs, with the matching invariant
    coverage regeneration.
  - Characterization and provenance tests that pin the verified current behavior before any decision lands.
- **Out-of-Scope**:
  - Any change to approval prompts, risk levels, or blocking behavior before the corresponding decision is
    recorded and approved (issue constraint).
  - Enabling GitHub write access (`approval_github_allowed_repos` is deny-all today and stays deny-all).
  - MCP server-side write enforcement implementation in `scripts/mcp_servers/` (ADR-012 boundary is a
    documentation target here, not a code target).
  - `plan_blocked_tools` removal before DT-03 is approved.
- **Dependencies**: `N/A: none`. The sibling hot-reload validation work item (adrchk004) consumes this Plan's
  tier decisions; this Plan does not wait for it.

## Background
The Agent approval policy is assembled from four independent configuration sources that all feed one
function, `agent/tool_policy.py::classify_risk()`. Because the sources are configured separately
(`[approval_risk_rules]`, `[tool_safety_tiers]`, `approval_protected_paths`, `shared/tool_constants.py`),
entries can exist that the evaluation order can never reach, and controls can appear to exist in
configuration while having no discriminating effect at runtime. Several ADRs make claims about where approval
authority lives (Agent-side approval versus MCP server-side write enforcement), and those claims are the
reference point for future changes. If the reachable subset is not established first, decisions taken against
the ADR text would be taken against behaviour the system does not exhibit.

## Problem
Adversarial verification against the current source produced these findings, several of which contradict the
source issue's claims:

- **Evaluation order is rule-first, not tier-first.** `classify_risk()` (`scripts/agent/tool_policy.py:426-468`)
  resolves in this order: explicit `approval_risk_rules` entry → `tool_safety_tiers` →
  `shared/tool_constants.py` per-tool default → default `MEDIUM`, and then
  `if base == RiskLevel.NONE: return NONE` short-circuits before `_special_case_risk()` and `_escalate_for_path()`.
  The issue's claim that "the tier returns NONE so `approval_risk_rules` never run" is inverted: rules win over
  tiers.
- **What is genuinely unreachable is the tier entry for a ruled tool, and the escalation path for a
  tier-`NONE` tool.** All 19 tools with an `approval_risk_rules` entry also have a `tool_safety_tiers` entry;
  the tier value is then only used by `is_plan_mode_blocked()`. Conversely, the tier-`NONE` tools with no rule
  (`index_paths`, `refresh_index`, `git_add`, `git_commit`, and every `READ_ONLY` tool) return `NONE` before
  special-case and path-escalation checks, so `approval_protected_paths` can never raise their risk.
  Runtime confirmation with the shipped config: `git_add` and `git_commit` classify `none` even with a path
  argument under `allowed_root`.
- **`approval_protected_paths` has no discriminating effect inside the jail.** With
  `allowed_root = "/opt/llm"` and protected paths `/opt/`, `/etc/`, `/boot/`, `/usr/`, `/bin/`, `/sbin/`, every
  ruled tool whose path argument is inside the jail escalates to `HIGH`, so a `medium` rule never produces a
  `[y/N]` prompt for a path-bearing call (measured: `write_file`, `edit_file`, `move_file` → `high`). Outside the
  jail the call is already rejected by the `allowed_root` pre-flight in `check_approval()`.
- **Empty `approval_github_allowed_repos` is already deny-all, and already documented.**
  `check_allowed_repo()` returns `False` for an empty allowlist (`scripts/agent/tool_policy.py:515-530`), the
  behaviour is pinned by `test_allowed_repos_empty_denies_all_github_write`
  (`tests/agent/test_tool_approval_repos.py:230`), and it is documented in
  `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` and the `Known Limitations` of the canonical
  approval document. The issue's "lenient default" claim is false; the GitHub dry-run path is dormant, not
  permissive.
- **Plan mode is already tier-authoritative.** `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
  documents `plan_blocked_tools` as an explicit extension of the tier rule, and every one of the five
  configured entries is a non-`READ_ONLY` tool that the tier check blocks on its own — the list is fully
  redundant under the current config.
- **`role` in `[mcp_servers.*]` is display-only.** `scripts/shared/mcp_config.py:72` labels it a human-readable
  role label; its only consumers are `scripts/agent/commands/cmd_mcp.py` and
  `scripts/agent/services/mcp_status.py`. A wrong value is a cosmetic defect, not an enforcement gap.
- **A missing `tool_concurrency_limits` key is defined behaviour, not a bug.** Unknown keys warn and fall back
  to `DEFAULT_PER_SERVER_CONCURRENCY = 8` (`scripts/shared/tool_transport_invoker.py:33`, `_ensure_semaphores()`
  at `97-125`). `git` and `mdq` have no entry and therefore run at the default; the defect is that the effective
  value is implicit.
- **The `approval_decision` event path is orphaned.** `log_approval_decision()` (`scripts/agent/tool_audit.py:130-149`),
  `ApprovalDecisionEvent` (`scripts/agent/shared/models.py:30`), and `ApprovalOutcome`
  (`scripts/agent/tool_models.py:45`) have no production caller — only tests
  (`tests/agent/test_tool_audit.py:21,90,107,413,425`, `tests/agent/test_tool_approval_preflight.py:20,870,887`,
  `tests/tools/test_check_compat_shims.py:110`) and the generated API artifacts
  (`docs/23_agent/agent_13_reference-api-generated.md:143`, `registry/manifests/agent_api.yaml:548-549`).
  The event the Agent actually emits is `audit_approval()` → `tool_approval` (`scripts/agent/tool_audit.py:97-127`),
  which carries `operation_type` and `resource_scope` but not `escalation_reason`.
- **The lenient argument-validation default is latent, not currently exposed.** Zero shipped MCP tool schemas
  lack `properties` (all are built by `_input_schema(PydanticModel)`), so
  `_check_extra_fields()` (`scripts/agent/tool_arg_validator.py:166-184`) skipping validation when `properties`
  is absent is currently unreachable; `RuntimeTool.allow_extra_fields` is the sanctioned per-tool escape hatch.
- **The ADR boundary is narrower than the issue states, and partly already written down.** ADR-014 has three
  invariants (lines 130-132); INV-03 forbids taking over or duplicating the MCP server's technical safety
  judgments (allowlist, path validation, sandboxing, resource limits, argument validation) in the Orchestrator
  and ToolExecutor layers, and the invariant matrix records it as Manual Review with no automated test
  (`docs/10_adr/adr_01_index.md:209`). ADR-012's Decision already records the split — approval is enforced
  client-side in the Agent process (`agent/tool_policy.py`, `tool_approval.py`) and the git endpoint has no
  dependency on approval state (line 43) — and ADR-012 INV-04 states the two checks are independent
  (`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:133`). The authority registry assigns
  `agent.tool-approval` to ADR-003 with ADR-012 supplemental and limited to server-side write enforcement
  (`config/adr_authority.toml:48-52`). `RepositoryGateway`'s "Single write enforcement boundary" docstring is
  therefore accurate for the git server process. What is actually missing is automated evidence for ADR-014
  INV-03, and docstring wording that makes clear the gateway guards the server-side write path only, not
  Agent-side approval.
- `ProductionConfigValidator._check_approval_risk_floor()` already rejects git write tools that resolve below
  `HIGH`, so the floor is enforced; what is missing is a guard for the redundant tier/rule pairs. DT-01 Option A (approved 2026-11-18) accepts the pairs as documented defense-in-depth for plan-mode blocking and the ADR-003 tier-vs-write classification rather than adding a guard.
- `scripts/agent/tool_approval.py:45` cites `docs/05_agent_06_01_tool-execution-and-approval-execution.md`,
  a path that does not exist; the canonical documents are
  `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` and
  `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`.

## Reason for Change
Three other adrchk work items and the hot-reload validation work item (adrchk004) both take the approval tier
policy as a premise. The config file has 14 commits in the last 30 days and the generated API documentation 21,
so the surface is actively moving. Recording the verified reachable subset now prevents later work from
implementing against controls that do not fire, and it converts several open "is this a bug?" questions into
explicit decisions with owners.

## Implementation Intent
Do not change approval behaviour in the first phase. Measure, pin, and document what the current code actually
does, then present each policy question as an option table for maintainer decision. Only after a decision is
recorded does the configuration, the code, and the ADR text move to the chosen posture, with the generated
API/invariant artifacts regenerated rather than hand-edited. Documentation-only corrections (stale document
path, implicit concurrency default, display-only `role`) proceed without a decision because they change no
behaviour.

## Requirements
- `REQ-001`: Produce a reachability report for `classify_risk()` that states, per configured tool, which of the
  four inputs determines the final risk level, and which inputs are unreachable under the shipped config.
- `REQ-002`: Record the deterministic evaluation order of `classify_risk()` in the canonical approval
  documentation and in the module/function docstrings, including the `RiskLevel.NONE` short-circuit and its
  consequence for `approval_protected_paths` and the special-case checks.
- `REQ-003`: Characterize the current behavior of every tool that has an `approval_risk_rules` entry, a
  tier-`NONE` entry with no rule, and a path-bearing argument, as executable tests that pass against today's
  code before any policy decision lands.
- `REQ-004`: Record a decision task with an option table, and a maintainer approval record, for each policy
  question the verification opens (DT-01 … DT-06); no target file may be edited for a decision task before its
  approval record exists.
- `REQ-005`: Make the effective per-server concurrency for every shipped MCP server key explicit in
  `config/agent.toml`, or state in the concurrency documentation that the default applies to the unlisted keys.
- `REQ-006`: Remove the stale documentation reference in `scripts/agent/tool_approval.py` and replace it with
  the canonical approval document path.
- `REQ-007`: Resolve the orphan `approval_decision` event cluster (DT-04) so that no public approval API exists
  without a production caller; if removal is chosen, remove the function, the event dataclass, the outcome
  dataclass, their imports, and their tests, and regenerate the API artifacts.
- `REQ-008`: Resolve the argument-validation default for schemas without `properties` (DT-02) so the fail-closed
  posture is stated by the validator, and pin the chosen behavior with a test.
- `REQ-009`: Align the ADR Decision/Invariant text with the verified boundary: Agent-side approval authority and
  MCP server-side technical write enforcement, and resolve whether ADR-014 INV-03 needs automated evidence
  as decided by DT-05.
- `REQ-010`: Ensure every claim this Plan makes about approval configuration has one canonical source document,
  registered in `config/documentation_canonical_sources.toml` if a mapping is missing.
- `REQ-011`: Keep generated artifacts generated: regenerate the API reference document and API manifests after
  any docstring or public-signature change instead of editing them.
- `REQ-012`: Run the validation gates for the whole change set and confirm no pre-existing test regressed.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's Implementation Target Files
Validation — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze):
every row exists in the working tree, states a concrete modification, cites file:line or symbol
evidence, and links to a Requirement or Acceptance criterion defined in this Plan).
Amended 2026-11-18 (scope): added tests/agent/test_orchestrator.py — DT-05 Option A adds automated evidence for INV-03 and changes its matrix row from Manual Review to a test gate; the gate test belongs in the suite that already cites ADR-014, which was not in the frozen table

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file
may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | docstring/contract clarification; behavior change only after DT-01/DT-06 approval | `classify_risk()` and `is_plan_mode_blocked()` must state the evaluation order and the `RiskLevel.NONE` short-circuit in their docstrings; DT-01/DT-06 approval can then change tier/rule or protected-path handling | REQ-001, REQ-002, REQ-004 | `scripts/agent/tool_policy.py:426-468` (`classify_risk`), `:413-423` (`is_plan_mode_blocked`), `:471-512` (`check_allowed_root`), `:515-530` (`check_allowed_repo`), `:368-410` (`_special_case_risk`), `:323-349` (`_escalate_for_path`) | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_approval_risk.py` | Verified |
| `scripts/agent/tool_arg_validator.py` | validation default policy (DT-02 gated) | `_check_extra_fields()` returns "valid" when a schema has no `properties`, which is a permissive default that no shipped schema currently exercises; DT-02 decides strict-reject versus documented escape hatch | REQ-004, REQ-008 | `scripts/agent/tool_arg_validator.py:166-184` | `tests/agent/test_tool_arg_validator.py` (`test_properties_absent_allows_extra`) | Verified |
| `scripts/agent/tool_approval.py` | reference fix | Comment at line 45 cites `docs/05_agent_06_01_tool-execution-and-approval-execution.md`, which does not exist (`grep -n 'docs/' scripts/agent/tool_approval.py` returns only that line); point it at the canonical approval document | REQ-006 | `scripts/agent/tool_approval.py:45` | `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_approval_paths.py` | Verified |
| `scripts/agent/tool_audit.py` | orphan-path removal or activation (DT-04 gated) | `log_approval_decision()` has no production caller while `audit_approval()` is the live path; DT-04 decides removal of the orphan function or wiring it into the approval gate | REQ-004, REQ-007 | `scripts/agent/tool_audit.py:97-127` (`audit_approval`, emits `tool_approval`), `:130-149` (`log_approval_decision`, emits `approval_decision`); no production caller found by `tools/scan_change_consumers.py --seed log_approval_decision` | `tests/agent/test_tool_audit.py:21,90,107,413,425`, `tests/agent/test_tool_approval_preflight.py:856-887`, `tests/tools/test_check_compat_shims.py` (`:110`) | Verified |
| `scripts/agent/shared/models.py` | orphan-event removal (DT-04 gated) | `ApprovalDecisionEvent` is constructed only by `log_approval_decision()`; if DT-04 chooses removal the dataclass must be deleted with it | REQ-004, REQ-007 | `scripts/agent/shared/models.py:30` (`ApprovalDecisionEvent`), `:13` (`ToolApprovalEvent`, live path) | `tests/agent/test_tool_audit.py` | Verified |
| `scripts/agent/tool_models.py` | orphan-outcome removal (DT-04 gated) | `ApprovalOutcome` is referenced only by `tool_audit.log_approval_decision()` and tests; removal must delete the dataclass and its imports together | REQ-004, REQ-007 | `scripts/agent/tool_models.py:45`; import at `scripts/agent/tool_audit.py:20` | `tests/agent/test_tool_audit.py:25,84,102,427`, `tests/agent/test_tool_approval_preflight.py:23,864,882` | Verified |
| `scripts/agent/repository_gateway.py` | docstring boundary clarification (DT-05 gated) | Module docstring line 3 and the class docstring assert a "Single write enforcement boundary"; the wording must state the process boundary the ADR-012 Decision describes so it is not read as Agent-side approval authority | REQ-004, REQ-009, REQ-011 | `scripts/agent/repository_gateway.py:3` and class docstring; ADR-012 Decision text at `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:43` | `tests/agent/test_repository_gateway.py` | Verified |
| `config/agent.toml` | configuration posture (DT-01/DT-02/DT-03/DT-06 gated) | Tier entries for the 19 ruled tools are unreachable for risk purposes; the five `plan_blocked_tools` entries are redundant; protected paths have no effect inside `allowed_root`; `git` and `mdq` are missing from `tool_concurrency_limits` | REQ-001, REQ-004, REQ-005 | `config/agent.toml:71` (`tool_concurrency_limits`), `:109-115` (`plan_blocked_tools`), `:116-123` (`approval_protected_paths`), `:229` (`approval_github_allowed_repos = []`), `:252-271` (`[approval_risk_rules]`), `:287-351` (`[tool_safety_tiers]`) | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_approval_repos.py` | Verified |
| `scripts/agent/production_config_validator.py` | posture documentation and existing-guard verification (DT-01 decided Option A) | `_check_approval_risk_floor()` already enforces the git-write risk floor; Option A adds no new guard, so this module documents that rules are authoritative for risk and verifies that every remaining tier entry is required for plan-mode blocking or the ADR-003 tier-vs-write classification | REQ-004, REQ-012 | `scripts/agent/production_config_validator.py` (`_check_approval_risk_floor`) | `tests/agent/test_production_config_validator.py` | Verified |
| `tests/agent/test_production_config_validator.py` | validator test characterization (DT-01 decided Option A) | No new guard exists to test; the existing floor tests must keep passing and a characterization assertion must pin the rule-authoritative posture (a rule overrides its tool's tier) | REQ-004, REQ-012 | `tests/agent/test_production_config_validator.py` (`TestProductionConfigValidatorApprovalRiskFloor`, `tests/agent/test_production_config_validator.py:114-204`, covering the live `_check_approval_risk_floor()` guard at `scripts/agent/production_config_validator.py:88`) | — | Verified |
| `tests/agent/test_tool_policy.py` | characterization + provenance tests | Must pin the current tier/rule/escalation outcomes and add assertions for which branch produced the level, which no existing test asserts | REQ-001, REQ-003 | `tests/agent/test_tool_policy.py:185-192`, `:601-603`, `:374-534` (`_escalate_for_path` imports) | — | Verified |
| `tests/agent/test_tool_policy_comprehensive.py` | characterization tests | Must pin the tier-`NONE` short-circuit for the ruled-but-tiered tools and the `sideeffect001` static-membership contract this Plan depends on | REQ-001, REQ-003 | `tests/agent/test_tool_policy_comprehensive.py:230-275` | — | Verified |
| `tests/agent/test_tool_arg_validator.py` | contract test rewrite | `test_properties_absent_allows_extra` pins today's lenient default; DT-02 must rewrite this assertion rather than add a second test that contradicts it | REQ-008 | `tests/agent/test_tool_arg_validator.py` (`test_properties_absent_allows_extra`) | — | Verified |
| `tests/agent/test_tool_approval_paths.py` | characterization tests | Must pin that a path-bearing ruled tool escalates to `HIGH` under the shipped protected paths, so a DT-06 change is visible as an intentional delta | REQ-003 | `tests/agent/test_tool_approval_paths.py:1-30` (fixture), pre-flight cases | — | Verified |
| `tests/agent/test_tool_approval_risk.py` | characterization tests | Must pin the rule-over-tier precedence and the tier-`NONE` escalation gap measured under the shipped config | REQ-003 | `tests/agent/test_tool_approval_risk.py:97-110` (rule- and tier-derived levels), `:196-210` (`test_custom_risk_rules_override_default`, `test_empty_risk_rules_falls_back_to_tier`) | — | Verified |
| `tests/agent/test_tool_approval_repos.py` | keep deny-all pinned | `test_allowed_repos_empty_denies_all_github_write` is the fail-closed regression guard; any allowlist change must extend this file rather than alter that test | REQ-003, REQ-012 | `tests/agent/test_tool_approval_repos.py:104,119,207-232` | — | Verified |
| `tests/agent/test_tool_approval_preflight.py` | orphan-path test removal (DT-04 gated) | Its `log_approval_decision` section tests the orphan path; removal or activation of DT-04 changes this file | REQ-007 | `tests/agent/test_tool_approval_preflight.py:6,20,856-887` | — | Verified |
| `tests/agent/test_tool_audit.py` | orphan-path test removal (DT-04 gated) | Tests construct `ApprovalOutcome` and call `log_approval_decision()`; it also carries the ADR-001 INV-11 citation that must survive the change | REQ-007, REQ-009 | `tests/agent/test_tool_audit.py:21,25,84-107,413-427`; `registry/manifests/invariant_coverage.yaml:23-29` (INV-11 cites this file) | — | Verified |
| `tests/tools/test_check_compat_shims.py` | compat-shim expectation update | Line 110 asserts `log_approval_decision(ctx, outcome)` is not a shim; DT-04 removal changes the expectation this checker validates | REQ-007 | `tests/tools/test_check_compat_shims.py:110` | — | Verified |
| `tests/agent/_config_test_defaults.py` | shared test fixture alignment | Exports `ALL_APPROVAL_RISK_RULES`, `ALL_TOOL_SAFETY_TIERS`, `PERMISSIVE_ALLOWED_ROOT` that the approval tests build configs from; the approved tier/rule posture changes these constants | REQ-003, REQ-012 | `tests/agent/_config_test_defaults.py` (consumed by `tests/agent/test_tool_approval_paths.py:18-22`) | `tests/agent/test_tool_approval_paths.py` | Verified |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | canonical approval-flow documentation | Must state the verified evaluation order, the `RiskLevel.NONE` short-circuit, the protected-path/allowed-root interaction, and the tier-authoritative plan-mode rule as the canonical description | REQ-002, REQ-010 | `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md:105-112` (plan-mode rule) | — | Verified |
| `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | terminology and behavior documentation | Its Tool-Level Approval Terminology/Behavior sections are the canonical definition of the approval event vocabulary the orphan-cluster decision renames or removes | REQ-007, REQ-010 | `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md:28-45` | — | Verified |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | concurrency documentation | Line 47 already states an unlisted server is capped at the process default; it must name the default value and the currently unlisted keys, or record that the config now lists them | REQ-005 | `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md:47` | — | Verified |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | approval-configuration guide | Must document the tier/rule precedence as implemented, the protected-path scope relative to `allowed_root`, and the display-only nature of `role` | REQ-002, REQ-005, REQ-010 | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md:103,127` (empty allowlist = deny all) | — | Verified |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | tier-to-approval mapping table | The table at lines 73-74 states the tier supplies the default and rules override it; it must also state which tier entries are plan-mode-only and which tools never reach escalation | REQ-001, REQ-002, REQ-010 | `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md:73-74` | — | Verified |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | security policy mapping | Line 119 defers the approval-to-tier mapping to the MCP risk-tier document; it must stay consistent with whatever DT-01/DT-06 approve and state the Agent-side versus server-side control split | REQ-004, REQ-009, REQ-010 | `docs/91_security/security_02_high-risk-tool-common-policy.md:119-124` | — | Verified |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | ADR invariant text (DT-05 gated) | INV-03 at line 132 forbids taking over MCP-server technical safety judgments in the Orchestrator/ToolExecutor layers, and the matrix records it as Manual Review with no automated test; DT-05 Option A (approved 2026-11-18) adds automated evidence for INV-03, changes its matrix row to a test gate, and rewords the `RepositoryGateway` docstrings | REQ-004, REQ-009 | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md:130-132` (the only three invariants), `163` ("INV-01 and INV-03 have no automated tests"); matrix row `docs/10_adr/adr_01_index.md:209` | `tests/agent/test_orchestrator.py` (cites ADR-014) | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | ADR decision/invariant text (DT-05 gated) | Line 43 already records client-side approval with the git endpoint independent of approval state, and INV-04 at line 133 states the two checks are independent; the wording must stay aligned with the verified split and with the `RepositoryGateway` docstrings, and must not be shortened | REQ-004, REQ-009 | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:43` (Decision), `:133` (INV-04); authority entry `config/adr_authority.toml:48-52` (`agent.tool-approval`, primary ADR-003, supplemental ADR-012) | `tests/mcp_servers/git/` (INV-01-INV-04 evidence, matrix row `docs/10_adr/adr_01_index.md:205`) | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | ADR invariant text (DT-04 gated) | INV-11 at line 175 is the invariant the approval-audit tests cite; removing the orphan approval event path must not orphan that invariant's evidence | REQ-007, REQ-009 | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md:175`; `registry/manifests/invariant_coverage.yaml:23-29` | `tests/agent/test_tool_audit.py::TestAuditApprovalInv11` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | ADR invariant text (DT-02/DT-03 gated) | States that approval state and execution eligibility are distinct concepts and that Safety Tier/Write attributes must agree across Routing; the tier-redundancy and validation decisions must be reflected in that text | REQ-004, REQ-009 | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:36,48,55` | `tests/agent/test_tool_policy_comprehensive.py` | Verified |
| `docs/10_adr/adr_01_index.md` | ADR index and invariant verification matrix | The matrix must reflect any invariant added or reworded by DT-05 and re-cite the test evidence changed by DT-04 (it is the source the `invariant_coverage` manifest is generated from) | REQ-009, REQ-011 | `docs/10_adr/adr_01_index.md:180` (ADR-001 INV-11 row), `:205` (ADR-012 row), `:207-209` (ADR-014 rows); `tools/generate_reference_table.py:471` (`invariant_coverage` source) | `tools/check_adr_invariant_matrix.py` | Verified |
| `config/documentation_canonical_sources.toml` | canonical-source registry | No entry currently maps the approval risk-tier claims; the claims this Plan documents must each resolve to one canonical source | REQ-010 | `config/documentation_canonical_sources.toml` (no `approval_risk_rules`/`tool_safety_tiers` entry found by grep) | `tools/check_canonical_source_registry.py` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | generated artifact refresh | Row 143 publishes `log_approval_decision` and every approval-module docstring is published here; docstring edits and DT-04 removal must be regenerated, not hand-edited | REQ-011 | `docs/23_agent/agent_13_reference-api-generated.md:143`; guarded block in the same file | `uv run python tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/agent_api.yaml` | generated manifest refresh | Lines 548-549 publish the orphan `log_approval_decision` signature; regenerated from source after DT-04 and the docstring changes | REQ-011 | `registry/manifests/agent_api.yaml:548-549` | `uv run python tools/generate_reference_table.py --check` (manifest-vs-source direction) | Verified |
| `registry/manifests/invariant_coverage.yaml` | generated manifest refresh | The INV-11 evidence entry (lines 23-29) cites the approval-audit test file this Plan modifies; the manifest must be regenerated after the ADR and test changes | REQ-009, REQ-011 | `registry/manifests/invariant_coverage.yaml:23-29` | `uv run python tools/check_adr_invariant_matrix.py` | Verified |
| `tests/agent/test_orchestrator.py` | ADR-014 INV-03 automated evidence test (DT-05 Option A) | DT-05 Option A adds automated evidence for INV-03 and changes its matrix row from Manual Review to a test gate; the gate test belongs in the suite that already cites ADR-014, which was not in the frozen table | REQ-009 / AC-009 | tests/agent/test_orchestrator.py:3205-3209 (existing ADR-014 INV-02 citation block; no test cites INV-03); matrix row docs/10_adr/adr_01_index.md:209 (Manual Review) | tests/agent/test_orchestrator.py | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_preparation.py` | Establishes that argument validation runs before the approval gate, which fixes the blast radius of the DT-02 decision | REQ-008 |
| `scripts/shared/runtime_tool.py` | `RuntimeTool.allow_extra_fields` is the sanctioned per-tool escape hatch DT-02 must keep working | REQ-008 |
| `scripts/shared/tool_transport_invoker.py` | `DEFAULT_PER_SERVER_CONCURRENCY = 8` and `_ensure_semaphores()` define the fallback REQ-005 documents | REQ-005 |
| `scripts/shared/tool_constants.py` | Supplies the per-tool default risk and `ALL_SIDE_EFFECTING_TOOLS` that `classify_risk()` consults third | REQ-001 |
| `scripts/agent/config_dataclasses.py` | Declares `ApprovalConfig`/`ToolConfig` fields the approved posture must keep constructible | REQ-004 |
| `scripts/agent/config_section_builders.py` | Maps the TOML approval keys to the config dataclasses | REQ-004 |
| `scripts/shared/mcp_config.py` | Line 72 establishes that `role` is a display-only label, the basis for the `role` finding | REQ-010 |
| `scripts/agent/commands/cmd_mcp.py` | Confirms `role` is consumed for display only | REQ-010 |
| `scripts/agent/services/mcp_status.py` | Confirms `role` is consumed for display only | REQ-010 |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Canonical source for the preparation-phase-before-approval-gate ordering | REQ-002, REQ-008 |
| `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` | Line 56 already states `role` is display-only; it is the canonical source for that claim and must not be duplicated | REQ-010 |
| `docs/00_index.md` | Task-scope mapping that names the documentation targets during implementation | REQ-010 |
| `rules/env.md` | Source of the `deploy.sh Impact` values used in `Affected areas` | REQ-012 |
| `rules/toolchain.md` | Ordered validation-gate sequence and the `diff-cover` gate this Plan's steps must satisfy | REQ-012 |
| `tools/generate_reference_table.py` | Regenerates the API reference, the API manifest, and the invariant coverage manifest (`invariant_coverage` type at line 471 and 490) | REQ-011 |
| `tools/scan_change_consumers.py` | Consumer candidate list for the approval symbols; re-run before editing | REQ-001, REQ-007 |
| `tools/check_compat_shims.py` | Validates the expectation `tests/tools/test_check_compat_shims.py:110` encodes | REQ-007 |
| `tests/agent/test_repository_gateway.py` | Characterization baseline for the gateway docstring change | REQ-009 |

## Acceptance Criteria
- `AC-001` (REQ-001): A reachability table exists for every tool in `[approval_risk_rules]` and
  `[tool_safety_tiers]` that names the input determining its risk level and marks the unreachable inputs; each
  row is backed by a measured result from the shipped config, not by inference.
- `AC-002` (REQ-002): The canonical approval document and `classify_risk()`'s docstring state the same order,
  and the document states the observable consequence for tier-`NONE` tools with no rule.
- `AC-003` (REQ-003): New characterization tests pass against unmodified approval code, and each asserts which
  branch of `classify_risk()` produced the level.
- `AC-004` (REQ-004): Each of DT-01 … DT-06 has an option table and a recorded maintainer decision before its
  target rows are edited; no decision task is implemented on an assumption.
- `AC-005` (REQ-005): Every MCP server key present in `config/agent.toml` either has an explicit
  `tool_concurrency_limits` entry or is named in the concurrency document as running at the stated default.
- `AC-006` (REQ-006): No source file cites a documentation path that does not exist; `scripts/agent/tool_approval.py`
  cites a path under `docs/23_agent/`.
- `AC-007` (REQ-007): After DT-04 lands, no public approval symbol lacks a production caller or an explicit test-only
  designation, and the API reference document and `agent_api.yaml` are regenerated output, not hand edits.
- `AC-008` (REQ-008): Exactly one behavior is asserted for schemas without `properties`, and the test that pinned the
  previous default now asserts the approved one.
- `AC-009` (REQ-009): The ADR-012 Decision text, the `RepositoryGateway` docstrings, and the approval-flow document
  describe the same split, and either a new invariant covers it or the ADR records explicitly that none is required.
- `AC-010` (REQ-010): Each approval claim resolves to exactly one canonical source document registered in
  `config/documentation_canonical_sources.toml`.
- `AC-011` (REQ-011): `uv run python tools/generate_reference_table.py` reports no drift for the regenerated
  artifacts, and no generated file was edited by hand.
- `AC-012` (REQ-012): `uv run python tools/run_validation_gates.py --full` passes, and the pre-change baseline
  (12810 passed, 7 skipped) shows no new failures.

## Tests
- `REQ-001` / `REQ-003`: Branch-provenance tests in `tests/agent/test_tool_policy.py` and
  `tests/agent/test_tool_policy_comprehensive.py` that assert, for representative tools, whether the level came
  from the rule, the tier, the constants default, or path escalation; existing tests only assert the level.
- `REQ-003`: Gap tests for the tier-`NONE` short-circuit: a tier-`NONE` tool with a path argument under a
  protected path inside `allowed_root` stays `NONE` today (`git_add`, `git_commit`, `index_paths`,
  `refresh_index` measured).
- `REQ-003`: Keep `test_allowed_repos_empty_denies_all_github_write` (`tests/agent/test_tool_approval_repos.py:230`)
  unchanged as the fail-closed regression guard.
- `REQ-008`: Rewrite `test_properties_absent_allows_extra` (`tests/agent/test_tool_arg_validator.py`) to the
  approved posture rather than adding a contradicting test alongside it.
- `REQ-007`: After DT-04, `tests/agent/test_tool_audit.py` and
  `tests/agent/test_tool_approval_preflight.py` must retain their INV-11 evidence and no longer reference a
  removed symbol; `tests/tools/test_check_compat_shims.py` expectation updated in the same commit.
- `REQ-011`: Generated-artifact drift check must pass in the same commit as the docstring and signature changes.
- `REQ-012`: Full-suite run with `--cov` and the `diff-cover` gate per `rules/toolchain.md`.

## Documentation Impact
Yes. `docs/*.md` must be updated for `REQ-002`, `REQ-005`, `REQ-007`, `REQ-009`, and `REQ-010`. Named through
`docs/00_index.md`'s "Document References by Task" mapping and the ADR conventions in the Documentation Policy:
the Agent tool-execution-and-approval document family (flow, canonical terminology, concurrency-safety), the MCP
fail-open/risk-tier document, the high-risk-tool security policy, the approval-configuration guide, and the ADR
index with its invariant verification matrix. The generated API reference document and the generated manifests are
regenerated by the generator, not written as documentation edits.

## Assumptions
- The shipped `config/agent.toml` is the reference configuration for the reachability report; a deployment with a
  different tier or rule set would produce a different reachable subset.
- `RiskLevel` is a `StrEnum` whose `NONE` member is truthy and compares equal to `"none"`, so the
  `if base == RiskLevel.NONE` short-circuit is the only guard on the escalation path.
- The MCP git server's own self-guard and the Agent-side `approval_github_allowed_repos` check are separate
  controls in separate processes; neither is a duplicate of the other in the sense ADR-014 INV-03 prohibits. The
  authority registry splits the claim: `agent.tool-approval` is primary-owned by ADR-003 with ADR-012 supplemental
  and limited to server-side write enforcement (`config/adr_authority.toml:48-52`), so an approval-policy change is
  an ADR-003-scope change and a gateway change is an ADR-012-scope change.
- No persisted schema stores approval events (the approval events are in-memory audit records), so the DT-04
  decision has no DB migration consequence.
- This development host is not the production host; the operational findings below describe this host only.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | DT-01: which control should own a tool's approval risk when both a tier entry and a rule entry exist — keep rules authoritative and drop the redundant tier entries, keep tiers and drop the redundant rules, or add a validator that rejects the redundant pair | Maintainer decision; no ADR currently states which is authoritative | Option table DT-01 in `Design`; requires an approval record before `scripts/agent/tool_policy.py`, `config/agent.toml`, `scripts/agent/production_config_validator.py` are editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-02 | DT-02: should a tool schema without `properties` fail closed or keep the lenient default with `RuntimeTool.allow_extra_fields` as the only escape hatch | No shipped schema exercises the branch; cannot measure real-world impact | Option table DT-02 in `Design`; approval record before `scripts/agent/tool_arg_validator.py` and its test are editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-03 | DT-03: keep `plan_blocked_tools` as an explicit extension of the tier rule, or remove the five redundant entries | No ADR states whether an explicit plan-mode block list is required as an operational control independent of tiers | Option table DT-03 in `Design`; approval record before `config/agent.toml` is editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-04 | DT-04: remove the orphan `approval_decision` event cluster, or wire `escalation_reason` into the live `tool_approval` event | No product requirement exists for `escalation_reason` in audit output | Option table DT-04 in `Design`; approval record before the models, audit module, and their tests are editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-05 | DT-05: whether ADR-014 INV-03 should gain an automated gate, and whether the existing ADR-012 Decision and INV-04 text plus the `agent.tool-approval` authority entry are sufficient authority for the split | ADR-014 INV-03 is recorded as Manual Review with no automated test (`docs/10_adr/adr_01_index.md:209`); nothing records what an automated gate for it would assert | Option table DT-05 in `Design`; requires an ADR approval record before the ADR and gateway docstrings are editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-06 | DT-06: whether `approval_protected_paths` should be scoped to paths outside `allowed_root`, widened to paths that `allowed_root` does not jail, or documented as jail-internal escalation only | The intended operational threat model for the protected list is not recorded anywhere | Option table DT-06 in `Design`; approval record before `config/agent.toml` and `scripts/agent/tool_policy.py` are editedResolved 2026-11-18: maintainer approved Option A (see Decision records in `Design`). | False |
| UNK-07 | Whether the production host's listening MCP ports and running services match this host's configuration | This host listens on none of the MCP server ports (8005-8009, 8012-8014 all empty under `ss`); production state was not inspected | Inspect the production host before applying the approved config posture | False |
| UNK-08 | Whether any external consumer depends on the `approval_decision` event type | Grep over `scripts/`, `tests/`, `docs/`, `registry/` found only tests and generated artifacts; no external consumer inventory exists | Confirm with the maintainer before DT-04 removal is executed | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | edit | `agent/tool_approval.py` (3 call sites), all approval test modules, generated API docs | 7 | 4 authors / 32 commits | not applicable (rsynced) |
| `scripts/agent/tool_arg_validator.py` | edit | `agent/tool_preparation.py`, `agent/tool_runner.py`, `shared/runtime_tool.py`, generated API docs | 1 | 2 authors / 5 commits | not applicable (rsynced) |
| `scripts/agent/tool_approval.py` | edit | `agent/tool_runner.py` approval gate, approval test modules | 5 | 2 authors | not applicable (rsynced) |
| `scripts/agent/tool_audit.py` | edit (removal, DT-04 gated) | `tests/agent/test_tool_audit.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/tools/test_check_compat_shims.py`, generated API docs and manifest | 4 | 2 authors / 39 commits | not applicable (rsynced) |
| `scripts/agent/shared/models.py` | edit (removal, DT-04 gated) | `agent/tool_audit.py`, `agent/tool_models.py`, approval tests | 2 | 2 authors | not applicable (rsynced) |
| `scripts/agent/tool_models.py` | edit (removal, DT-04 gated) | `agent/tool_audit.py`, approval tests | 2 | 2 authors | not applicable (rsynced) |
| `scripts/agent/repository_gateway.py` | edit (docstrings) | `mcp_servers/git/write_tools.py`, `commit_tools.py`, `pull_tools.py`, `tool_handlers.py`, generated API docs and manifest | 1 | 3 authors / 8 commits | not applicable (rsynced) |
| `config/agent.toml` | edit | every Agent consumer of approval config, production config validator, all approval tests | 14 | 3 authors / 80 commits | add cp line — no: already copied by `deploy/deploy.sh:152` |
| `scripts/agent/production_config_validator.py` | edit | startup validation path, its test module | 3 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_policy.py` | edit | approval risk characterization suite | 6 | 2 authors / 16 commits | not applicable (rsynced) |
| `tests/agent/test_tool_policy_comprehensive.py` | edit | write-classification and tier suite | 4 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_arg_validator.py` | edit (assertion rewrite) | argument-validation suite | 1 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_approval_paths.py` | edit | allowed-root pre-flight suite | 3 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_approval_risk.py` | edit | approval risk suite | 3 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_approval_repos.py` | edit (additive) | GitHub allowlist suite | 2 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_approval_preflight.py` | edit (removal, DT-04 gated) | approval pre-flight suite | 2 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_tool_audit.py` | edit (removal, DT-04 gated) | audit suite, INV-11 evidence cited by the invariant coverage manifest | 3 | 2 authors | not applicable (rsynced) |
| `tests/tools/test_check_compat_shims.py` | edit | compat-shim audit gate | 1 | 2 authors | not applicable (rsynced) |
| `tests/agent/_config_test_defaults.py` | edit | every approval test module that builds configs from it | 3 | 2 authors | not applicable (rsynced) |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | edit | canonical approval-flow consumers, ADR cross-links | 4 | 2 authors | not applicable (docs are rsynced) |
| `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | edit | approval terminology consumers | 2 | 2 authors | not applicable (docs are rsynced) |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | edit | concurrency-safety consumers | 2 | 2 authors | not applicable (docs are rsynced) |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | edit | approval-configuration guide consumers | 7 | 2 authors / 24 commits | not applicable (docs are rsynced) |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | edit | security policy mapping and MCP tier consumers | 2 | 2 authors | not applicable (docs are rsynced) |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | edit | security policy consumers | 3 | 2 authors | not applicable (docs are rsynced) |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | edit | ADR index matrix, canonical-source registry, ADR-citing tests | 6 | 2 authors / 7 commits | not applicable (docs are rsynced) |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | edit | ADR index matrix, MCP write-enforcement consumers | 2 | 2 authors | not applicable (docs are rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | edit | ADR index matrix, INV-11 evidence chain | 12 | 2 authors / 13 commits | not applicable (docs are rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | edit | ADR index matrix, routing-authority consumers | 8 | 2 authors / 9 commits | not applicable (docs are rsynced) |
| `docs/10_adr/adr_01_index.md` | regenerated | ADR dependency graph and invariant verification matrix | 5 | 2 authors | not applicable (docs are rsynced) |
| `config/documentation_canonical_sources.toml` | edit | canonical-source resolution for approval claims | 4 | 2 authors | add cp line — no: `config/*.toml` already enumerated by `deploy/deploy.sh` |
| `docs/23_agent/agent_13_reference-api-generated.md` | regenerated | every generated API consumer | 21 | 2 authors / 32 commits | not applicable (docs are rsynced) |
| `registry/manifests/agent_api.yaml` | regenerated | API contract consumers and drift checks | 14 | 2 authors / 14 commits | not applicable (rsynced) |
| `registry/manifests/invariant_coverage.yaml` | regenerated | invariant verification matrix and its checkers | 4 | 2 authors | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Not assessed (amendment 2026-11-18) | N/A | N/A | Not assessed (amendment 2026-11-18) |

## Design
Verification-first, decision-gated design. The phases separate three kinds of change that must not be conflated:
documentation of measured fact, behavior-neutral correction, and behavior change gated on an approval record.
No shim, alias, or historical comment is introduced anywhere in this Plan (Current-Specification-Only rule);
removals are removals, and reworded text states the current specification only.

### Architecture findings (Step 5, Path B)
- Approval chain: `agent/tool_runner.py` → `agent/tool_preparation.py::prepare_tool_calls()` (validation, fail
  closed, no `PreparedToolCall` on failure) → `agent/tool_approval.py::run_approval_checks()` →
  `check_approval()` (allowed-root pre-flight, then `classify_risk()`, then repo/preflight checks) →
  `agent/tool_policy.py` → `agent/tool_audit.py::audit_approval()`.
- Boundary: Agent-side approval (intent and human confirmation) and git-MCP-server-side write enforcement
  (`RepositoryGateway`) live in different processes. `lint-imports` keeps all six contracts KEPT across 518
  files and 3102 dependencies, and `mcp_servers must not import from agent` is one of them — so no code path
  can merge the two controls; the duplication question is a documentation/authority question, not an import
  question.
- Generated artifacts are downstream of docstrings and public signatures: the API reference document and
  `registry/manifests/agent_api.yaml` are rebuilt by `tools/generate_reference_table.py`, and
  `registry/manifests/invariant_coverage.yaml` plus `docs/10_adr/adr_01_index.md` are regenerated by the same
  generator (`invariant_coverage` type). Any docstring or signature change in this Plan therefore has a mandatory
  regeneration step, and hand-editing those files is prohibited.
- `ProductionConfigValidator` is the existing place where config-level policy is enforced at startup; a
  tier/rule-redundancy guard would belong there rather than in `classify_risk()` (DT-01 Option A: no guard added).

### Dependency-graph findings (Step 5, Path B)
- `classify_risk`: consumed by `agent/tool_approval.py` at three sites and by five test modules; no consumer in
  `mcp_servers/`, `rag/`, `db/`, or `shared/`.
- `_check_extra_fields`: reached only through `validate_tool_arguments()` → `agent/tool_preparation.py` →
  `agent/tool_runner.py`, plus `shared/runtime_tool.py::RuntimeTool`.
- `log_approval_decision`, `ApprovalDecisionEvent`, `ApprovalOutcome`: production callers none; test callers three
  files; published in the generated API reference and `agent_api.yaml`; `tools/check_compat_shims.py` records an
  expectation about the symbol.
- `RepositoryGateway` public API consumers: `mcp_servers/git/write_tools.py`, `commit_tools.py`, `pull_tools.py`,
  `tool_handlers.py`. Docstring-only edits touch no caller but do change generated output.
- Approval config keys flow `config/agent.toml` → `agent/config_section_builders.py` →
  `agent/config_dataclasses.py` → `agent/production_config_validator.py` → `agent/tool_policy.py`.
- `scan_change_consumers.py` seeds (`classify_risk`, `log_approval_decision`, `check_allowed_repo`,
  `is_plan_mode_blocked`, `_check_extra_fields`) returned 11 ADR-test-citation candidates and 102
  patch-or-import candidates; every candidate that requires modification is a row in the target table, the rest
  are Reference Files rows or unaffected because they are read-only consumers.

### Historical findings (Step 5, Path B)
- High-churn shared surfaces: `docs/23_agent/agent_13_reference-api-generated.md` (21 commits/30d),
  `config/agent.toml` (14), `registry/manifests/agent_api.yaml` (14),
  `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (12). Edits here collide with parallel work, so
  they are sequenced last and regenerated rather than hand-edited.
- Bus factor is low on the approval core: `scripts/agent/tool_policy.py` 32 commits with 16 from the primary
  author, `config/agent.toml` 80 commits with 47, `scripts/agent/tool_audit.py` 39 with 25. Decision records are
  therefore mandatory rather than optional — a single maintainer's inference is the current documentation.
- `tools/check_compat_shims.py` already tracks `log_approval_decision` as a compatibility surface; retiring the
  symbol is consistent with an existing governance mechanism, not a new one.

### Operational dependency findings (Step 5, Path B)
- Listening ports on this host: none of the MCP server ports (8005-8009, 8012-8014) are listening; the Agent and
  MCP services are not running here. Consequence: the DT decisions cannot be validated end-to-end on this host,
  only by unit/characterization tests. Recorded as UNK-07.
- No new MCP server config key is planned, so `scripts/shared/mcp_config.py`,
  `registry/manifests/mcp_endpoints.yaml`, and the MCP configuration table need no change.
- No DDL, `*_db_path` key, or `ATTACH`/`load_vec` usage is affected; `check_db_separation.py` is N/A: no schema
  change in this Plan.
- `deploy/deploy.sh` copies `scripts/` with `rsync -av --delete` and copies `config/agent.toml` with an existing
  `cp` line at `deploy/deploy.sh:152`; no `deploy.sh` edit is required.

### Validation quality findings (baseline)
- `radon cc`: `scripts/agent/tool_policy.py::_special_case_risk` C(13) and `classify_risk` C(13) — the two
  functions with the highest complexity in the approval path are the ones the decisions target, so
  characterization tests are mandatory before any edit. `tool_arg_validator.py` and `repository_gateway.py`
  report no C or worse blocks.
- `vulture scripts/ --min-confidence 80`: no unused code reported in the approval modules (the orphan cluster is
  public and test-referenced, so it is invisible to static dead-code tooling — the reachability report is what
  surfaced it).
- `bandit`: no findings on the three approval target modules.
- `diff-cover`: baseline captured — full suite `12810 passed, 7 skipped` with coverage; no diff lines exist yet,
  so the gate becomes meaningful from Phase 1 onward.
- Assertion-pinning hazard: `test_allowed_repos_empty_denies_all_github_write` pins deny-all, the approval risk
  tests pin `HIGH` for git write tools, and `test_properties_absent_allows_extra` pins the lenient validation
  default. A decision that changes any of these must rewrite the test in the same commit; leaving both assertions
  in place would produce a suite that documents two contradictory policies.
- Observability gap: no test asserts which branch of `classify_risk()` produced a level. Without provenance
  assertions, a tier/rule-redundancy change is invisible to the suite.
- CI: every phase's gates run through `uv run python tools/run_validation_gates.py`; the generated-artifact drift
  check must be part of the same commit as the source change it reflects.

### Decision tasks (approval required before implementation)

DT-01 — Approval-risk authority when a tool has both a tier entry and a rule entry.
**Decision (2026-11-18): Option A approved** — rules remain authoritative; delete the `tool_safety_tiers` entries that can never affect risk, keeping tier entries only for plan-mode blocking.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Keep rules authoritative (current behavior), delete the `tool_safety_tiers` entries that can never affect risk, keep tier entries only for plan-mode blocking | Config-only; tier entries remain required for plan mode and for the tier-vs-write classification check in ADR-003 |
| B | Keep both, add a `ProductionConfigValidator` guard that rejects a tier entry whose effect is unreachable | New startup failure mode for existing configs; makes the redundancy impossible rather than documented |
| C | Keep both, document the redundancy as intended defense-in-depth, no guard | No code or config change; the unreachable entries stay in the file and the reachability report becomes the only record |

DT-02 — Argument validation for schemas without `properties`.
**Decision (2026-11-18): Option A approved** — fail closed: a schema without `properties` rejects unknown fields.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Fail closed: a schema without `properties` rejects unknown fields | Rewrites `test_properties_absent_allows_extra`; affects only future schemas because no shipped schema lacks `properties` |
| B | Keep the lenient default, make `RuntimeTool.allow_extra_fields` the documented escape hatch | No code change; document the contract and the risk |
| C | Require `properties` to be present unless the tool is explicitly registered with `allow_extra_fields` | Adds a registration-time validation step; strongest contract, largest change |

DT-03 — `plan_blocked_tools` (five entries, all already blocked by the tier rule).
**Decision (2026-11-18): Option A approved** — keep as an explicit operational control; document it as redundant-by-design under the current tiers.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Keep as an explicit operational control; document it as redundant-by-design under the current tiers | Config unchanged; documentation only |
| B | Remove the five redundant entries; plan mode blocks purely on tier | Config change; a tier change would silently change plan-mode blocking |
| C | Keep the key but reject entries the tier already blocks at validation time | New startup failure mode; keeps explicit intent visible |

DT-04 — Orphan `approval_decision` event cluster.
**Decision (2026-11-18): Option A approved** — remove `log_approval_decision()`, `ApprovalDecisionEvent`, `ApprovalOutcome`, their imports, and their tests; regenerate API artifacts.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Remove `log_approval_decision()`, `ApprovalDecisionEvent`, `ApprovalOutcome`, their imports, and their tests; regenerate API artifacts | Removes a published public API from the generated reference and manifest; test-only consumers deleted |
| B | Keep `escalation_reason` by adding it to the live `audit_approval()` payload and delete the orphan path | Adds a field to the `tool_approval` event; audit consumers see a new field |
| C | Wire `log_approval_decision()` into the approval gate so both events are emitted | Two events for one decision; conflicts with the no-duplication posture of ADR-014 |

DT-05 — Agent-side approval versus MCP server-side write enforcement boundary. ADR-012's Decision and INV-04 and
ADR-014 INV-03 already describe the split; what is open is whether ADR-014 INV-03 should gain automated evidence,
and how the gateway docstrings should name the process they guard.
**Decision (2026-11-18): Option A approved** — add automated evidence for ADR-014 INV-03, change its matrix row from Manual Review to a test gate, and reword `RepositoryGateway` docstrings to match.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Add automated evidence for ADR-014 INV-03 and change its matrix row from Manual Review to a test gate; reword `RepositoryGateway` docstrings to match | New test plus a matrix row change; `check_adr_invariant_matrix.py` then requires the cited test to keep existing |
| B | Keep ADR-014 INV-03 as Manual Review; reword only the ADR text and the `RepositoryGateway` docstrings to name the guarded process | No new gate; regenerates the API reference and `agent_api.yaml` only; `check_adr_preservation.py` must see the reword as intended |
| C | Add a new invariant that names the Agent-approval versus server-technical-safety split explicitly | New invariant row plus a new evidence requirement; overlaps ADR-012 INV-04 and risks a duplicate authority claim against the `agent.tool-approval` authority entry |

DT-06 — `approval_protected_paths` scope relative to `allowed_root`.
**Decision (2026-11-18): Option A approved** — document the current semantics: inside the jail every ruled path-bearing tool escalates to `HIGH`; the list has no discriminating effect outside it because the jail already denies those paths.

| Option | Description | Compatibility impact |
|---|---|---|
| A | Document the current semantics: inside the jail every ruled path-bearing tool escalates to `HIGH`; the list has no discriminating effect outside it because the jail already denies those paths | Documentation only |
| B | Narrow escalation to paths outside `allowed_root` so a `medium` rule can still produce a `[y/N]` prompt for in-jail writes | Changes prompts for `write_file`, `edit_file`, `move_file`; changes several pinned tests |
| C | Remove the protected-path escalation for tools already jailed by `allowed_root` and keep it for tools the jail does not cover | Behavior change for non-jailed tools only; requires enumerating which tools the jail covers |

## Implementation steps
Each step cites rows of `Implementation Target Files`.

1. **Phase 1: Reachability report and characterization baseline (no behavior change)**
   - [ ] Re-run the verification searches (`tools/scan_change_consumers.py` with the five approval seeds) and
     confirm no finding has already been fixed (REQ-001).
   - [ ] Add branch-provenance and tier-`NONE` gap tests to `tests/agent/test_tool_policy.py`,
     `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_approval_risk.py`, and
     `tests/agent/test_tool_approval_paths.py`; they must pass against unmodified code (REQ-003).
   - [ ] Record the measured reachability table and write it into
     `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` and
     `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` (REQ-001, REQ-002).
   - [ ] State the evaluation order and the `RiskLevel.NONE` short-circuit in the docstrings of `classify_risk()`
     and `is_plan_mode_blocked()` in `scripts/agent/tool_policy.py` (REQ-002).
   - [x] Present DT-01 … DT-06 to the maintainer and record each decision; stop before Phase 3 until a decision
     exists (REQ-004). Done 2026-11-18: all six approved as Option A.
2. **Phase 2: Behavior-neutral corrections**
   - [ ] Fix the stale document path in `scripts/agent/tool_approval.py` (REQ-006).
   - [ ] Add explicit `git` and `mdq` entries to `tool_concurrency_limits` in `config/agent.toml`, or name the
     default explicitly in `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` (REQ-005).
   - [ ] Confirm the display-only `role` claim against `scripts/shared/mcp_config.py` and record it in
     `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` without duplicating the MCP config-field
     document (REQ-010).
3. **Phase 3: Approved policy applied**
   - [ ] Apply the DT-01 decision to `config/agent.toml`, `scripts/agent/tool_policy.py`, and, for Option B,
     `scripts/agent/production_config_validator.py` (REQ-004).
   - [ ] Apply the DT-02 decision to `scripts/agent/tool_arg_validator.py` and rewrite the pinned assertion in
     `tests/agent/test_tool_arg_validator.py` (REQ-008).
   - [ ] Apply the DT-03 decision to `config/agent.toml` and `tests/agent/_config_test_defaults.py` (REQ-004).
   - [ ] Apply the DT-06 decision to `config/agent.toml` and `scripts/agent/tool_policy.py` (REQ-004).
4. **Phase 4: Approval-event path resolution**
   - [ ] Apply the DT-04 decision across `scripts/agent/tool_audit.py`, `scripts/agent/shared/models.py`,
     `scripts/agent/tool_models.py`, `tests/agent/test_tool_audit.py`, `tests/agent/test_tool_approval_preflight.py`,
     and `tests/tools/test_check_compat_shims.py` in one commit (REQ-007).
   - [ ] Update the approval vocabulary in `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` (REQ-007).
5. **Phase 5: Boundary documentation and ADR records**
   - [ ] Apply the DT-05 decision to `scripts/agent/repository_gateway.py`,
     `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`,
     `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, and
     `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` (REQ-009).
   - [ ] Update `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` so INV-11's evidence still points at
     a test that exists after Phase 4 (REQ-007, REQ-009).
   - [ ] Update `docs/91_security/security_02_high-risk-tool-common-policy.md` and
     `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` to the approved posture (REQ-004, REQ-010).
   - [ ] Register the approval-claim canonical sources in `config/documentation_canonical_sources.toml` (REQ-010).
   - [ ] ADR-014 INV-03 automated evidence test (DT-05 Option A) (REQ-009; `tests/agent/test_orchestrator.py`) — amendment 2026-11-18
6. **Phase 6: Regeneration and verification**
   - [ ] Regenerate `registry/manifests/agent_api.yaml` and `registry/manifests/invariant_coverage.yaml` with
     `uv run python tools/generate_reference_table.py --manifests`, which also re-renders the guarded block in
     `docs/23_agent/agent_13_reference-api-generated.md`; regenerate the guarded graph sections of
     `docs/10_adr/adr_01_index.md` with `uv run python tools/generate_adr_authority.py`; never hand-edit them
     (REQ-011).
   - [ ] Run the documentation and manifest checkers: `uv run python tools/generate_reference_table.py --check`,
     `uv run python tools/generate_adr_authority.py --check`, `uv run python tools/check_docs_quality.py`,
     `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`,
     `uv run python tools/check_docs_consistency.py --domain agent`,
     `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_reference.py`,
     `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`,
     `uv run python tools/check_canonical_source_registry.py`,
     `uv run python tools/check_workitem_structure.py`, `uv run python tools/check_plan_target_overlaps.py`
     (REQ-011).
   - [ ] Deployment validation check: confirm `deploy/deploy.sh` still copies every changed config file and that
     no new `config/*.toml` was introduced; `scripts/` needs no `cp` line (REQ-012).
   - [ ] Run `uv run python tools/run_validation_gates.py --full` and compare against the 12810-passed baseline (REQ-012).

### Release units
**Unit**: approval-event-cleanup | **Phases**: 4, 6 | **Reason**: deleting the orphan symbols breaks `tests/agent/test_tool_audit.py`, `tests/agent/test_tool_approval_preflight.py`, and `tests/tools/test_check_compat_shims.py` until the regenerated API reference and manifest land in the same commit, so the phase cannot be validated alone.
**Unit**: boundary-and-adr-record | **Phases**: 5, 6 | **Reason**: the ADR edits change the invariant matrix that `docs/10_adr/adr_01_index.md` and `registry/manifests/invariant_coverage.yaml` publish, and the gateway docstring edit changes the generated API reference, so Phase 5 fails the manifest and docs checkers until Phase 6 regenerates them.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_policy.py` | Unit, branch provenance | `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_risk.py -q` | All pass; provenance assertions identify the rule, tier, constant, or escalation branch |
| `scripts/agent/tool_arg_validator.py` | Unit, contract | `uv run pytest tests/agent/test_tool_arg_validator.py -q` | Exactly one assertion set for schemas without `properties` |
| `scripts/agent/tool_approval.py` | Unit | `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_approval_paths.py -q` | No failure; no citation of a non-existent document |
| `scripts/agent/tool_audit.py`, `scripts/agent/shared/models.py`, `scripts/agent/tool_models.py` | Unit | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py tests/tools/test_check_compat_shims.py -q` | No reference to a symbol that no longer exists; INV-11 evidence still present |
| `scripts/agent/repository_gateway.py` | Unit | `uv run pytest tests/agent/test_repository_gateway.py -q` | Behavior unchanged; only docstrings differ |
| `config/agent.toml` | Config validation | `uv run python tools/check_docs_consistency.py --domain agent` and the `ProductionConfigValidator` startup path | No unknown or redundant approval key survives the approved posture |
| `scripts/agent/production_config_validator.py` | Unit | `uv run pytest tests/agent/test_production_config_validator.py -q` | Existing floor tests pass unchanged; the rule-authoritative characterization assertion passes |
| `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`, `registry/manifests/invariant_coverage.yaml`, `docs/10_adr/adr_01_index.md` | Generated-artifact drift | `uv run python tools/generate_reference_table.py --manifests` then `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_adr_invariant_matrix.py` | Zero drift; no hand edits |
| All `docs/*.md` targets | Structural | `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` | Pass with no unregistered Needs-Confirmation markers |
| Whole change set | Full suite plus coverage gate | `uv run python tools/run_validation_gates.py --full` | Pass; `diff-cover` reports coverage of the changed lines; no new failure against the 12810-passed baseline |

## Risks
- **Risk**: The tier/rule decisions change prompt behavior for tools maintainers use daily (measured: `write_file`,
  `edit_file`, `move_file` currently prompt as `high` because of path escalation) → **Mitigation**: DT-01 and DT-06
  are decision-gated; characterization tests from Phase 1 make the exact delta visible before it is applied.
- **Risk**: Removing `log_approval_decision` deletes a symbol published in the generated API reference and manifest,
  which downstream consumers may already cite → **Mitigation**: UNK-08 must be closed with the maintainer before
  Phase 4; the compat-shim checker already tracks the symbol.
- **Risk**: `config/agent.toml` (14 commits/30d) and the generated API reference (21 commits/30d) are high-churn
  shared surfaces; parallel work can collide with these edits → **Mitigation**: sequence config and generated-artifact
  edits into the last phases, regenerate rather than hand-edit, and re-run
  `uv run python tools/check_plan_target_overlaps.py` before freezing.
- **Risk**: ADR edits change the invariant verification matrix, which is generated and checked → **Mitigation**:
  declare the ADR + regeneration release unit; run the invariant coverage checker in the same commit.
- **Risk**: A decision is implemented before its approval record exists, silently changing approval behavior →
  **Mitigation**: the plan records DT-01 … DT-06 as Blocking Unknowns; no target row for a decision task may be
  edited until the record exists.
- **Risk**: Bus factor 1 on the approval core means the reachability report is the only durable record of intent →
  **Mitigation**: the report lands in canonical documents in Phase 1, not in conversation.
- **Risk**: Verification was performed on a host with no MCP services listening, so end-to-end behavior is not
  observed → **Mitigation**: UNK-07; confirm on the production host before deploying the approved posture.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: reachability report and characterization baseline | In Progress | — | — | Verification findings are recorded in this Plan; the report artifacts are Phase 1 work Procedure documents generated 2026-11-18 (rows 01/11/12/14/15/21/25) |
| 2 | Phase 2: behavior-neutral corrections | In Progress | — | — | Not decision-gated Procedure documents generated 2026-11-18 (rows 03/08/23/24) |
| 3 | Phase 3: approved policy applied | In Progress | — | — | Not started: DT-01, DT-02, DT-03 and DT-06 approval records must exist before this step starts Decision records 2026-11-18: DT-01, DT-02, DT-03, DT-06 approved as Option A; gate satisfied Procedure documents generated 2026-11-18 (rows 01/02/08/09/13-companion-of-02/20) |
| 4 | Phase 4: approval-event path resolution | In Progress | — | — | Not started: DT-04 approval record must exist before this step starts Decision record 2026-11-18: DT-04 approved as Option A; gate satisfied Procedure documents generated 2026-11-18 (rows 04/05/06/17/18/19-companion-of-04/22) |
| 5 | Phase 5: boundary documentation and ADR records | In Progress | — | — | Not started: DT-05 approval record must exist before this step starts Decision record 2026-11-18: DT-05 approved as Option A; gate satisfied Procedure documents generated 2026-11-18 (rows 07/24/26/27/28/29/30/32/36) |
| 6 | Phase 6: regeneration and verification | In Progress | — | — | Must run in the same commits as Phases 4 and 5 Procedure documents generated 2026-11-18 (rows 31/33/34/35) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | DT-01, DT-02, DT-03, DT-06 require maintainer approval records before any approval-behavior change | No | — |
| 4 | DT-04 requires a maintainer decision on the orphan approval-event cluster and confirmation that no external consumer depends on `approval_decision` | No | — |
| 5 | DT-05 requires an ADR decision on whether ADR-014 INV-03 needs an automated gate and how the gateway docstrings should name the guarded process | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261118-233456_01_scripts_agent_tool_policy.py.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261118-233456_02_scripts_agent_tool_arg_validator.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261118-233456_03_scripts_agent_tool_approval.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261118-233456_04_scripts_agent_tool_audit.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_05_scripts_agent_shared_models.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_06_scripts_agent_tool_models.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_07_scripts_agent_repository_gateway.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_08_config_agent.toml.md` | 2, 3 | Procedure | Pending | — | — |
| `implementations/20261118-233456_09_scripts_agent_production_config_validator.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261118-233456_11_tests_agent_test_tool_policy.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_12_tests_agent_test_tool_policy_comprehensive.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_14_tests_agent_test_tool_approval_paths.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_15_tests_agent_test_tool_approval_risk.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_17_tests_agent_test_tool_approval_preflight.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_18_tests_agent_test_tool_audit.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_20_tests_agent__config_test_defaults.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261118-233456_21_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_22_docs_23_agent_agent_06_04_tool-execution-and-approval-canonical.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261118-233456_23_docs_23_agent_agent_06_03_tool-execution-and-approval-concurrency-safety.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261118-233456_24_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md` | 2, 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_25_docs_22_mcp_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261118-233456_26_docs_91_security_security_02_high-risk-tool-common-policy.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_27_docs_10_adr_adr_02_02_014_agent-control-plane-responsibility-boundaries.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_28_docs_10_adr_adr_02_03_012_mcp-git-server-side-write-enforcement.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_29_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_30_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_31_docs_10_adr_adr_01_index.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261118-233456_32_config_documentation_canonical_sources.toml.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261118-233456_33_docs_23_agent_agent_13_reference-api-generated.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261118-233456_34_registry_manifests_agent_api.yaml.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261118-233456_35_registry_manifests_invariant_coverage.yaml.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261118-233456_36_tests_agent_test_orchestrator.py.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-224457
- **Related target files**: `scripts/agent/tool_policy.py`, `scripts/agent/tool_arg_validator.py`, `tests/agent/test_orchestrator.py`
  `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/shared/models.py`,
  `scripts/agent/tool_models.py`, `scripts/agent/repository_gateway.py`, `config/agent.toml`,
  `scripts/agent/production_config_validator.py`, `tests/agent/test_tool_policy.py`,
  `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_arg_validator.py`,
  `tests/agent/test_tool_approval_paths.py`, `tests/agent/test_tool_approval_risk.py`,
  `tests/agent/test_tool_approval_repos.py`, `tests/agent/test_tool_approval_preflight.py`,
  `tests/agent/test_tool_audit.py`, `tests/tools/test_check_compat_shims.py`,
  `tests/agent/_config_test_defaults.py`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`,
  `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`,
  `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`,
  `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`,
  `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`,
  `docs/91_security/security_02_high-risk-tool-common-policy.md`,
  `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`,
  `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`,
  `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`,
  `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`,
  `docs/10_adr/adr_01_index.md`, `config/documentation_canonical_sources.toml`,
  `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`,
  `registry/manifests/invariant_coverage.yaml`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue "Suspected unreachable policy" plus measured `classify_risk()` results | `scripts/agent/tool_policy.py` | 1 | AC-001 | `tests/agent/test_tool_policy.py` provenance tests | Planned |
| REQ-001 | `config/agent.toml:252-271`, `:287-351` | `config/agent.toml` | 1, 3 | AC-001 | `uv run python tools/check_docs_consistency.py --domain agent` | Planned |
| REQ-001 | Tier-to-approval mapping table | `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | 1 | AC-001 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-002 | Issue "Approval-order ambiguity" claim, corrected by `tool_policy.py:426-468` | `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | 1 | AC-002 | `uv run python tools/check_docs_structure.py` | Planned |
| REQ-002 | `scripts/agent/tool_policy.py:426-468` docstrings | `scripts/agent/tool_policy.py` | 1 | AC-002 | `tests/agent/test_tool_policy.py` | Planned |
| REQ-002 | Protected-path scope | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | 2, 5 | AC-002 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-003 | Measured tier-`NONE` gap (`git_add`, `git_commit`, `index_paths`, `refresh_index`) | `tests/agent/test_tool_policy.py` | 1 | AC-003 | `uv run pytest tests/agent/test_tool_policy.py -q` | Planned |
| REQ-003 | Measured rule-over-tier precedence | `tests/agent/test_tool_policy_comprehensive.py` | 1 | AC-003 | `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q` | Planned |
| REQ-003 | `tests/agent/test_tool_approval_risk.py:97-110` (rule- and tier-derived levels), `:196-210` (`test_custom_risk_rules_override_default`, `test_empty_risk_rules_falls_back_to_tier`) | `tests/agent/test_tool_approval_risk.py` | 1 | AC-003 | `uv run pytest tests/agent/test_tool_approval_risk.py -q` | Planned |
| REQ-003 | Measured in-jail escalation to `HIGH` | `tests/agent/test_tool_approval_paths.py` | 1 | AC-003 | `uv run pytest tests/agent/test_tool_approval_paths.py -q` | Planned |
| REQ-003 | `test_allowed_repos_empty_denies_all_github_write` guard | `tests/agent/test_tool_approval_repos.py` | 1 | AC-003 | `uv run pytest tests/agent/test_tool_approval_repos.py -q` | Planned |
| REQ-004 | Issue "Required decisions" plus this Plan's `Design` decision tables | `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | 1, 5 | AC-004 | ADR approval record | Planned |
| REQ-004 | DT-01 Option A: no new guard; existing floor guard verified | `scripts/agent/production_config_validator.py` | 3 | AC-004 | `uv run pytest tests/agent/test_production_config_validator.py -q` | Planned |
| REQ-004 | `config/agent.toml:109-123` | `config/agent.toml` | 3 | AC-004 | config validation at Agent startup | Planned |
| REQ-005 | `scripts/shared/tool_transport_invoker.py:33` default fallback | `config/agent.toml` | 2 | AC-005 | `uv run python tools/check_docs_consistency.py --domain agent` | Planned |
| REQ-005 | `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md:47` | `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | 2 | AC-005 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-006 | `scripts/agent/tool_approval.py:45` non-existent document path | `scripts/agent/tool_approval.py` | 2 | AC-006 | `tests/agent/test_tool_approval_preflight.py` | Planned |
| REQ-007 | `scripts/agent/tool_audit.py:130-149` with no production caller | `scripts/agent/tool_audit.py` | 4 | AC-007 | `uv run pytest tests/agent/test_tool_audit.py -q` | Planned |
| REQ-007 | `scripts/agent/shared/models.py:30` | `scripts/agent/shared/models.py` | 4 | AC-007 | `uv run pytest tests/agent/test_tool_audit.py -q` | Planned |
| REQ-007 | `scripts/agent/tool_models.py:45` | `scripts/agent/tool_models.py` | 4 | AC-007 | `uv run pytest tests/agent/test_tool_approval_preflight.py -q` | Planned |
| REQ-007 | `tests/agent/test_tool_audit.py:84-107` orphan tests | `tests/agent/test_tool_audit.py` | 4 | AC-007 | `uv run pytest tests/agent/test_tool_audit.py -q` | Planned |
| REQ-007 | `tests/agent/test_tool_approval_preflight.py:856-887` | `tests/agent/test_tool_approval_preflight.py` | 4 | AC-007 | `uv run pytest tests/agent/test_tool_approval_preflight.py -q` | Planned |
| REQ-007 | `tests/tools/test_check_compat_shims.py:110` | `tests/tools/test_check_compat_shims.py` | 4 | AC-007 | `uv run pytest tests/tools/test_check_compat_shims.py -q` | Planned |
| REQ-007 | Approval event vocabulary | `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | 4 | AC-007 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-008 | `scripts/agent/tool_arg_validator.py:166-184` | `scripts/agent/tool_arg_validator.py` | 3 | AC-008 | `uv run pytest tests/agent/test_tool_arg_validator.py -q` | Planned |
| REQ-008 | `test_properties_absent_allows_extra` pinned default | `tests/agent/test_tool_arg_validator.py` | 3 | AC-008 | `uv run pytest tests/agent/test_tool_arg_validator.py -q` | Planned |
| REQ-009 | `RepositoryGateway` docstrings vs ADR-012 Decision at `:43` | `scripts/agent/repository_gateway.py` | 5 | AC-009 | `tests/agent/test_repository_gateway.py` | Planned |
| REQ-009 | ADR-012 Decision text | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | 5 | AC-009 | `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` | Planned |
| REQ-009 | INV-11 evidence chain | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | 5 | AC-009 | `registry/manifests/invariant_coverage.yaml` check | Planned |
| REQ-009 | Routing-authority approval-state claim at `:36,48,55` | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 5 | AC-009 | `tests/agent/test_tool_policy_comprehensive.py` | Planned |
| REQ-009 | Security policy control split | `docs/91_security/security_02_high-risk-tool-common-policy.md` | 5 | AC-009 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-009 | Invariant verification matrix | `docs/10_adr/adr_01_index.md` | 5, 6 | AC-009 | `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` | Planned |
| REQ-010 | No existing canonical mapping for the approval tier claims | `config/documentation_canonical_sources.toml` | 5 | AC-010 | `uv run python tools/check_canonical_source_registry.py` | Planned |
| REQ-010 | Empty-allowlist claim | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | 2, 5 | AC-010 | `uv run python tools/check_docs_quality.py` | Planned |
| REQ-011 | `docs/23_agent/agent_13_reference-api-generated.md:143` published orphan symbol | `docs/23_agent/agent_13_reference-api-generated.md` | 6 | AC-011 | `uv run python tools/generate_reference_table.py` drift check | Planned |
| REQ-011 | `registry/manifests/agent_api.yaml:548-549` | `registry/manifests/agent_api.yaml` | 6 | AC-011 | `uv run python tools/generate_reference_table.py` drift check | Planned |
| REQ-011 | `registry/manifests/invariant_coverage.yaml:23-29` | `registry/manifests/invariant_coverage.yaml` | 6 | AC-011 | `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` | Planned |
| REQ-012 | Baseline suite run (12810 passed, 7 skipped) | `tests/agent/_config_test_defaults.py` | 1, 3 | AC-012 | `uv run pytest tests/agent -q` | Planned |
| REQ-012 | `rules/toolchain.md` gate sequence | `config/agent.toml` | 6 | AC-012 | `uv run python tools/run_validation_gates.py --full` | Planned |
| REQ-009 | Amendment 2026-11-18: DT-05 Option A adds automated evidence for INV-03 and changes its matrix row from Manual Review to a test gate; the gate test belongs in the suite that already cites ADR-014, which was not in the frozen table | tests/agent/test_orchestrator.py | 5 | AC-009 | tests/agent/test_orchestrator.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-233456 -->