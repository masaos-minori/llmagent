# Make security-posture failures fail closed for every server and make ADR-004 the single authority on posture handling

## Priority
High

## Summary
Ensure the Agent never continues startup unless every configured MCP server's security posture is positively confirmed valid (including servers that exit before binding their socket), and reduce the posture-handling rules in ADR-002, ADR-003, ADR-007, and ADR-014 to references to ADR-004.

## Background
- Source: `memo-issue.md` items H-09 and M-01, re-checked against current source on 2026-11-09. The memo's premise is only partly confirmed.
- `Explicit in code`: MCP servers enforce a posture gate before serving (`_enforce_startup_posture_gate` in `scripts/mcp_servers/server.py`, which refuses to start when the gate is missing or fails). The Agent probes each usable HTTP server's published posture (`collect_server_postures()` in `scripts/agent/services/mcp_health.py`), classifies failures as availability versus safety or integrity (`classify_server_failure()`), and `check_readiness()` aborts startup on a safety or integrity failure. `tests/agent/test_mcp_health_posture.py` documents that a safety or integrity posture failure aborts regardless of `required`.
- `Documentation only`: ADR-004 lists a test that "a server posture `FAILED` result aborts startup even when the server is `required = false`" as Confirmed. ADR-003 Decision Detail #16 says a server whose posture is not accepted is excluded from `RuntimeToolRegistry`, and that a posture failure on a `required=true` server aborts startup through `check_readiness()`; it does not state the `required=false` abort. This is the contradiction the memo describes: ADR-003 reads "exclude and continue" for non-required servers, ADR-004 reads "abort".
- `Needs confirmation`: the memo's central claim that a server whose posture fails calls `SystemExit` before binding, so the Agent sees only an unreachable server (an availability failure) and, for a non-required server, logs a WARNING and continues (`docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`). The Agent-side classification of an unreachable server must be checked in `mcp_health.py` and `startup.py` for subprocess-mode servers.
- `Documentation only`: the posture contract is restated in ADR-002, ADR-003, ADR-007, and ADR-014; `config/adr_authority.toml` has no `security.posture-contract` decision target (`Needs confirmation`: grep found no match).
- Related archived issues under `issues/done/`: `mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate`, `agent001_agent-startup-graceful-disable-path-for-non-required-subprocess-mcp-servers`, `start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed`. Re-verify this issue against current source.

## Problem
- If an unreachable non-required server may in fact be a posture failure that exited before binding, the Agent cannot distinguish it from a plain outage and may continue startup (`Needs confirmation`; harmless today only because every server is mandatory).
- ADR-003 and ADR-004 disagree on posture handling for non-required servers, and the contract is restated in four more ADRs, so a change must be applied five times and the authority model has no registered owner for it.

## Reason for Change
- Making any server non-required (an option in the EventBus and Group 7 decision issue) would open the bypass immediately if the `Needs confirmation` item holds.
- Normative ADRs that contradict each other are a blocking Canonical Source Conflict under the documentation policy.

## Implementation Intent
- Positive confirmation: the Agent continues only when it has verified every configured server's posture; a server whose posture cannot be verified is treated as unverifiable and aborts startup regardless of `required`.
- Servers report a posture failure distinctly (a dedicated exit status for subprocess mode and a structured startup log line) so the Agent can tell it from an outage.
- Exactly one ADR (ADR-004) defines posture handling; the others reference it.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (startup posture gate and exit status), `scripts/agent/services/mcp_health.py`, `scripts/agent/services/posture_validator.py`, `scripts/agent/startup.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`
- Tests: `tests/agent/test_mcp_health_posture.py`, `tests/agent/test_failure_handling_policy_cross_cutting.py`, `tests/shared/test_runtime_tool_registry.py`
- `config/adr_authority.toml`
- Docs: ADR-004, ADR-003 (`#16`), ADR-002, ADR-007, ADR-014 under `docs/10_adr/`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

## Required Changes
- First reproduce or refute the "exits before bind looks like an outage" path for a non-required subprocess server and record the result; if refuted, narrow this issue to the documentation changes.
- Make servers report a posture failure distinctly (a dedicated exit status in subprocess mode and a structured startup log line), and have the Agent detect it.
- Treat an unreachable server whose posture cannot be verified as unverifiable and abort startup regardless of `required`.
- Add tests: a non-required server with a posture failure aborts startup; a non-required server with a plain network outage follows the outcome of the EventBus and Group 7 decision issue.
- Remove "exclude and continue" from ADR-003 #16 and define "not accepted" as identical to FAILED.
- Replace the restatements in ADR-002, ADR-003, ADR-007, and ADR-014 with references to ADR-004.
- Register the decision target `security.posture-contract` (primary: ADR-004) in `config/adr_authority.toml`.
- Update `mcp_06_09`, `agent_10_01`, and `mcp_02_02`, and close the corresponding Canonical Source Conflict entry in `governance_03` (see the governance-ledger issue in this batch).

## Constraints
- Safety and integrity failures are always Fail-Fast/Fail-Closed (ADR-004 Decision Group 1); no configuration or `required` value may relax this.
- ADR amendments need approval records (governance-ledger issue in this batch); the implementer must not fabricate approvals.
- Child-process exit status and log format are an operational contract: keep them stable and documented by intent, not by value.

## Acceptance Criteria
- A posture failure on any server, required or not, aborts Agent startup with a distinct error message.
- An unverifiable server (posture not confirmable) aborts startup.
- Only ADR-004 contains normative posture-failure rules; `check_adr_authority.py`, `check_adr_structure.py`, and `check_docs_consistency.py --domain mcp` / `--domain agent` pass.
- ADR-003 contains no rule that conflicts with ADR-004.

## Testing Expectations
- Integration tests in `tests/agent/` for the cases above; unit tests for the distinct exit status handling.
- Full validation sequence from `rules/toolchain.md` and the documentation checkers named above.

## Documentation Impact
- ADR-004 is the single authority; ADR-002, 003, 007, 014 become references. Update the MCP and Agent operations documents to describe intent, failure behavior, and the unverifiable case. Do not copy exit-status values or config values into documents.

## Out of Scope
- The decision whether any server becomes non-required (EventBus and Group 7 decision issue).
- Removing non-strict branches (non-strict removal issue in this batch).

## Dependencies
- Depends on: none (its non-required-server test follows the outcome of the EventBus and Group 7 decision issue).
- Related: `issues/20261109-112739_adrrev006_eventbus-future-decision.md` (the decision determines the expected outcome of the plain-outage test).
- Related, recently archived: `mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate` and `agent001_agent-startup-graceful-disable-path-for-non-required-subprocess-mcp-servers` under `issues/done/`.

## Unresolved Questions
- `Needs confirmation`: does a non-required subprocess server that fails its posture gate currently let startup continue? The answer decides the size of the code change.
- `Needs confirmation`: the current text of ADR-002, ADR-007, and ADR-014 posture restatements (not read in this review).
- Maintainer approval is required for the ADR-003 and ADR-004 amendments.

## Adversarial Verification Results

Verified against current source on 2026-11-10 (HEAD `dab0fdf30`). Each claim was checked
once against live files; evidence cites file, line, and behavior.

### Claim 1 — a pre-bind posture exit looks like an outage for a non-required server (Needs confirmation #1)

Status: **REFUTED for subprocess mode; dormant for HTTP/persistent mode.**

- `scripts/mcp_servers/server.py` `_enforce_startup_posture_gate()` (L251-281) raises
  `RuntimeError` when the gate is missing or fails. `run_http()` calls it at L314, before
  uvicorn creates any socket (L316-344). The docstring (L289-292) states the exit is pre-bind
  and fail-fast: the process terminates before binding.
- Subprocess servers are started by `scripts/agent/startup_mcp_starter.py`. Both
  `start_servers()` (L88-122) and `verify_health()` (L125-180) route every failure through
  `retry_once_with_delay()` (`scripts/agent/shared/retry_helper.py`), which re-raises with a
  `[fatal]` prefix on second failure and aborts startup. Neither path reads `cfg.required`;
  the abort is unconditional. Comment L119: "fail closed (required=true always for subprocess
  servers)".
- Therefore a subprocess that exits before binding is detected as a spawn/health failure and
  aborts startup regardless of `required`. The Agent never reaches the HTTP-probe /
  `classify_server_failure()` Availability path for a subprocess server.
- ADR-004 already encodes this: line 244 and line 305 state a subprocess spawn failure aborts
  startup regardless of `required`, and startup validation rejects a configuration in which a
  subprocess server sets `required = false`.
- The only path where an unreachable server becomes an Availability failure is
  `collect_server_postures()` / `check_readiness()` for probed (persistent/HTTP) servers
  (`scripts/agent/services/mcp_health.py`, classify L160-161, `_is_fatal_gate` L149). A
  `required=false` such server degrades to a warning. However every entry in
  `registry/component_mandatoriness.yaml` is classified `required` (all 10 entries), and
  config validation enforces that classification, so no non-required server exists. The bypass
  is dormant, not exploitable.

Conclusion: the claimed bypass does not reproduce for the mode this issue targets (subprocess).
Per the AI Implementation Instruction, the code change is not warranted; the work narrows to the
documentation and authority-model changes.

### Claim 2 — posture rules are restated in ADR-002, ADR-003, ADR-007, ADR-014 (Needs confirmation #2)

Status: **CONFIRMED that restatements exist; the contradiction is narrower than stated.**

- ADR-002 L239: "a `FAILED` check aborts Agent startup." Consistent with ADR-004.
- ADR-007 L80 / L228: "A posture `FAILED` result aborts startup"; explicitly "not an
  availability failure." More precise than ADR-003.
- ADR-014 L138: "no `RuntimeToolRegistry` entry for a server whose posture is not accepted
  (contract gate only)." Registry-exclusion framing.
- ADR-003 Decision Detail #16 (L86): "A server whose Security Posture is not accepted is
  excluded when `RuntimeToolRegistry` is constructed..." frames it as a static-availability
  decision and does NOT carve out the ADR-004 "posture `FAILED` -> abort even when
  `required = false`" rule. This is the single phrasing that invites the "exclude and continue"
  misread the issue flags.
- Nuance: ADR-003 #16's "not accepted" is broader than ADR-004's "FAILED". Some not-accepted
  cases are Availability failures (a non-required server may continue) while `FAILED` is always
  Safety/Integrity (abort). The two ADRs are not strictly contradictory; the tension is that
  ADR-003 #16 omits the `required = false` abort that ADR-004 mandates. The issue's proposed fix
  (treat "not accepted" as identical to `FAILED` for this rule; drop the "continue" implication)
  is reasonable, but the scope is one ambiguous clause, not five contradictory places.

### Claim 3 — no registered authority target for the posture contract

Status: **CONFIRMED.** `config/adr_authority.toml` contains no `security.posture-contract`
entry (nor any `security.` or `posture` token).

### Overall

- Code change: not warranted. The bypass the issue asks to reproduce does not exist for
  subprocess-mode servers; persistent-mode non-required servers do not currently exist.
- Documentation / authority change: warranted. Consolidate ADR-003 #16 wording, replace the
  restatements in ADR-002/007/014 with references to ADR-004, and register
  `security.posture-contract` (primary: ADR-004) in `config/adr_authority.toml`.
- Unchanged: ADR amendments still require maintainer approval (issue Constraint); do not fabricate
  approval records.

## AI Implementation Instruction
- Reproduce the claimed bypass first; if it does not exist, limit the work to the documentation and authority-model changes and say so in the report.
- Do not relax any existing safety or integrity abort.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112814
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/agent/services/mcp_health.py`, `scripts/agent/services/posture_validator.py`, `scripts/agent/startup.py`, `scripts/agent/startup_validation.py`, `config/adr_authority.toml`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
