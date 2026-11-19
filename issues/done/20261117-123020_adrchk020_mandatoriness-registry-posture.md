# Correct the component mandatoriness registry and posture checks

## Priority
Medium

## Summary
`registry/component_mandatoriness.yaml` describes its own derivation backwards, contains no real assessment, and has inaccurate roles and categories; MDQ also has a duplicate posture check.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M08`; merged from ADRCHK-M23, L17, L18 (review finding N38 and round 2 and round 4 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- The derivation is described backwards: the header says the registry is derived from the `agent_08_04` table, but the generator renders that table from the registry, so a maintainer who edits the table would see the edit overwritten.
- No assessment was done: every rationale says Not assessed, so the ADR-004 assessment was never done, and the pending adrauth001 U-1 item is not tracked in governance_03.
- Roles and categories are wrong: the `rag_pipeline` safety_role says document ingestion although its tools are search, delete, and list, and every server is `safety-integrity` although ADR-004 classes an unreachable server as an availability failure.
- MDQ has both `common.auth_token` and `server.auth_token_configured` in its required posture checks, unlike the other servers.

## Implementation Intent
- The registry states that it is the source.
- The missing assessment and adrauth001 are tracked items.
- Each role and category matches the server's tools and ADR-004.
- Each server has one auth posture check.

## Target Files or Areas
- `registry/component_mandatoriness.yaml`
- docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md (regenerated)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `scripts/shared/security/posture_contract.py`
- The MDQ posture builder under `scripts/mcp_servers/mdq/` (file name unknown)

## Required Changes
- Fix the header so it states that the registry is the source.
- Register the ADR-004 assessment and adrauth001 U-1 as tracked items.
- Correct `safety_role` for rag_pipeline, and propose `failure_category` values based on ADR-004.
- Remove the duplicate MDQ auth check.
- Regenerate the table.

## Constraints
- Do not invent rationales; changing a `failure_category` value is a classification decision and needs approval.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- The derivation is stated in one direction only, and the pending items have ledger IDs.
- MDQ has one auth check ID, like the other servers.

## Testing Expectations
Posture contract tests under `tests/` for MDQ (find with `rg auth_token_configured tests`); `tools/generate_reference_table.py --check`; docs checkers; Needs Confirmation inventory check. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The registry header, the regenerated table, and governance_03 entries.

## Out of Scope
- Changing mandatoriness values without a decision.

## Dependencies
- `issues/20261117-123010_adrchk010_canonical-registry-checkers.md` registers this registry in the canonical source registry (soft dependency).

## Unresolved Questions
- The MDQ posture builder file is `不明`; search `scripts/mcp_servers/mdq/` for `auth_token_configured`.

## AI Implementation Instruction
- Do not invent rationales. Changing a `failure_category` value needs approval.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123020
- **Related target files**: `registry/component_mandatoriness.yaml`; `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md (regenerated)`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `scripts/shared/security/posture_contract.py`; The MDQ posture builder under `scripts/mcp_servers/mdq/` (file name unknown)
