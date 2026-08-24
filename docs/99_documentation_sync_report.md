---
title: "Documentation Sync Report: DB Recovery, Git Write Protection, MCP Tool Availability"
area: governance
tags:
  - governance
  - change-report
  - db
  - mcp
  - security
related:
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
  - 04_mcp_04_05_git.md
  - 00_security_02_high-risk-tool-common-policy.md
  - 04_mcp_03_06_tool-runtime-availability-metadata.md
  - 00_governance_12_documentation-policy.md
---

# Documentation Sync Report: DB Recovery, Git Write Protection, MCP Tool Availability

This report covers a documentation update addressing three issues: database corruption recovery safety (H-3), Git MCP write-operation protection (H-4), and MCP tool availability metadata (M-1). Source code, tests, existing design documents, ADRs, and Known Issues were inspected before editing; no source code was modified.

## Canonical documents updated

- `90_shared_05_04_db_api_and_operations-recovery-and-reference.md` — expanded section 9 Corruption Recovery into a full responsibility/exception/sequence/dry-run/persistence-domain/operational model; corrected a misleading section 10 Error Handling sentence.
- `04_mcp_04_05_git.md` — added a Write protection policy section covering the layered model, per-command policy for `git_checkout`/`git_pull`/`git_push`, protected-branch authority, approval-level gap, rejection codes, postcondition verification, and audit status.
- `00_security_02_high-risk-tool-common-policy.md` — added a Layered protection model section (Agent approval / common guard / command-specific guard / postcondition verification / audit); corrected two factually incorrect claims about Git MCP.
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` — corrected the `WRITE_DANGEROUS` row to reflect that `git_checkout`/`git_pull`/`git_push` actually receive `MEDIUM`-tier (`y/N`) approval, not the full-word `yes` prompt the table previously implied for all listed tools.
- `04_mcp_03_06_tool-runtime-availability-metadata.md` — added a conceptual-distinctions section (Defined/Discoverable/Owned/LLM-visible/Statically available/Dynamically available/Routable/Approved/Executable); corrected the stale claim that `web_search` lacks `enabled`/`disabled_reason`; clarified `include_disabled`/`disabled_code` as implemented-but-unreachable rather than unimplemented; added static-vs-dynamic-health and approval-vs-disabled sections.
- `04_mcp_03_01_dispatch-and-routing.md` — corrected the "Two-stage tool resolution" section, which described a second filtering stage that (on inspection) is a self-referential no-op; replaced it with an accurate description of where filtering actually happens and where the routing-layer gap is.
- `04_mcp_03_02_tool-registry.md` — added a cross-reference to the availability-metadata document.
- `90_shared_90_inconsistencies_and_known_issues.md`, `04_mcp_90_inconsistencies_and_known_issues.md` — Known Issues updated (see below).
- `00_governance_12_documentation-policy.md` — registered the new ADRs and flagged a numbering conflict with ADR-001's aspirational forward references.

## Decisions consolidated

- Git write-operation protection is now defined once, at two levels: the common baseline in `00_security_02_high-risk-tool-common-policy.md`, and Git-specific per-command policy in `04_mcp_04_05_git.md`. The common document no longer restates command-specific detail; it points to the tool document instead.
- MCP tool availability vocabulary (static vs. dynamic, LLM-visible vs. routable vs. approved) is defined once, in `04_mcp_03_06_tool-runtime-availability-metadata.md`, and referenced from `04_mcp_03_01`/`04_mcp_03_02` rather than being redefined in each.

## Contradictions removed

- `00_security_02_high-risk-tool-common-policy.md` previously claimed Git MCP implements `protected_branches` and `force_push_blocked`; `04_mcp_04_05_git.md` already stated the opposite. The false claim has been removed and replaced with a statement consistent with the code-verified reality (no such guards exist).
- The same document's Command allowlists section claimed Git MCP has a "built-in command allowlist" where "write operations require approval" at the MCP layer; corrected to state that approval is an Agent-side, not MCP-side, concern, and that no subcommand allowlist exists.
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` implied all `WRITE_DANGEROUS` tools require full-word `yes` approval; corrected for the three Git write tools, which actually fall back to `MEDIUM`/`y-N`.
- `04_mcp_90_inconsistencies_and_known_issues.md`'s MCP-002 stated `web_search` lacks `enabled`/`disabled_reason`; code shows it is implemented. Corrected and rescoped to the servers that actually lack it.
- `04_mcp_03_01_dispatch-and-routing.md`'s "Stage 2: Runtime Routability" description implied an independent filtering step; the function it names is a self-referential no-op. Corrected to describe actual behavior.

## Current implementation behavior confirmed

- `_run_integrity_check()` does not catch `sqlite3.DatabaseError`; it propagates uncaught (matches open Known Issue SHARED-001).
- Backup restoration is unvalidated, non-atomic, and unverified post-restore (new gap identified: SHARED-002).
- `workflow.sqlite` and `eventbus.sqlite` have no corruption-recovery path at all (new gap identified: SHARED-003).
- Git MCP enforces only repository-path allowlisting and a global `read_only` flag; no command-specific guard exists for `git_checkout`/`git_pull`/`git_push` (new gap identified and reproduced: MCP-003).
- `branch`/`remote` arguments to Git MCP write tools are unvalidated and were confirmed, in a sandboxed reproduction, to allow forced checkout and forced push via option-injection-shaped values.
- Git write tools' approval tier resolves to `MEDIUM` (`y/N`), not the `HIGH` full-word prompt the risk-tier table implied (MCP-004).
- The Git MCP audit call site likely reads a non-existent argument key for the `target` field (MCP-005; unverified against a live log line, tracked as NC-020).
- `RuntimeToolRegistry.llm_tool_definitions()` is the actual LLM-visibility filter; the documented second-stage filter is inert.
- Static availability (config-derived) and dynamic health (circuit breaker) are separate, unintegrated systems; a `degraded_servers` exclusion tier exists in code but is never populated.
- `RuntimeTool.requires_approval` is written but has no read site anywhere in the codebase; approval is decided by a separate subsystem.
- `/reload` does not rediscover tools; only a full agent restart refreshes discovery-derived availability.

## Target behavior documented

- A structured integrity-result classification, a safe (validate → stage → verify → atomic-replace) restoration sequence, and an explicit persistence-domain recovery policy, per ADR-011.
- Command-specific Git guards (ref/remote validation, protected-branch, Dirty-Worktree, Detached-HEAD, Force-Push rejection) and postcondition verification, per ADR-012.
- A shared availability vocabulary and a documented static/dynamic/approval separation, per ADR-013.

## Implementation gaps retained (not closed by this update)

All gaps above remain open as Known Issues; this update did not modify source code. See SHARED-001/002/003 and MCP-001 through MCP-005.

## ADRs created

- ADR-011: Database Corruption Recovery Safety Boundary
- ADR-012: Git MCP Server-Side Write Enforcement
- ADR-013: MCP Tool Availability Model

All three are `Proposed`. They were originally numbered ADR-002/ADR-003/ADR-004, following the
ADR index's next-available-number rule at the time. A concurrent update assigned those same
numbers to unrelated decisions (config isolation, RuntimeToolRegistry routing authority,
environment-profile fail policy) and reached `origin/master` first, so these three ADRs were
renumbered to ADR-011/ADR-012/ADR-013 to resolve the conflict. Separately, ADR-001's body still
reserves the ADR-002/ADR-003 numbers for unrelated future topics of its own (workflow-definition
schema, workflow monitoring) that were never registered under those numbers either — see the
follow-up task to correct ADR-001's stale forward references.

## Missing evidence

- MCP-005 (Git MCP audit `target` field emptiness) is based on code reading, not a captured live log line — tracked as NC-020 in `00_governance_07_needs-confirmation-inventory.md`.
- The absence of any corruption-recovery path for `eventbus.sqlite` is a confirmed-by-absence finding (no code found), which is inherently a weaker form of evidence than a positive behavioral test; flagged accordingly in the design document and Known Issue.
- Whether the Git MCP guard gaps (protected-branch, Force-Push) are an intentional design choice (local git assumed to be the user's own responsibility) or an oversight remains an open owner decision, carried forward from a pre-existing open question in `04_mcp_04_05_git.md` — tracked as NC-019.
- The DB recovery target design's structured integrity-result classification (section 9.3 of `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`) has not been reviewed by the owner — tracked as NC-021.

## Areas requiring human review

- Whether to close MCP-004 by adding `approval_risk_rules` overrides for the three Git write tools, or by correcting the documented tier — both are legitimate outcomes; the design update did not decide this.
- The eventual recovery policy for `workflow.sqlite`/`eventbus.sqlite` (SHARED-003) requires a decision, not just an implementation.
- ADR-001's stale forward-referenced ADR numbers should be corrected once the workflow-schema/monitoring ADRs are actually written.
