# Supersede profile-based design documentation and synchronize configuration/operations references

## Priority
Low

## Summary
Replace the Local/Production profile design with a canonical Production-only and
loopback-only decision, then synchronize all active design, configuration, deployment,
operations, Known Issues, and documentation-quality references.

## Background
ADR-004 (`docs/adr/ADR-004-environment-failure-handling-policy.md`) currently describes
behavior in terms of a two-profile model with required outcome parity (Decision Group 1), not
a Local-mode-removed design. If `localremoval`/`loopbackonly`/`mcpauth` land, ADR-004 and
related documents would become misleading unless the governing decision, configuration
inventory, and operational procedures are updated together. The repository has previously
retained Known Issues and ADR deviations after implementation was completed elsewhere in this
same area, so this migration also needs an explicit documentation-synchronization check.

## Problem
N/A: covered by Background — the problem is prospective (documentation would go stale once the
dependent issues land), not a currently-confirmed mismatch.

## Reason for Change
Once Local mode is removed, ADR-004 and its dependents must describe one final state, not a
partially-migrated mix of profile-based and unconditional wording.

## Implementation Intent
Prefer marking the current profile-based ADR-004 as superseded and creating a new ADR for
Production-only operation (or, if project governance requires in-place revision, record the
change explicitly and preserve decision history). Define in the canonical ADR: one
Production-grade runtime policy, loopback-only Agent-internal HTTP communication, prohibition
of public binding/external publication, retained mandatory MCP Bearer authentication, required
vs. optional MCP behavior, fatal safety/integrity boundaries, configuration-file
deletion/migration policy, restart requirements, verification/rollback approach, and review
triggers. Update the ADR index and all canonical references; remove active documentation
presenting Local mode as supported; preserve unrelated uses of "local" (filesystem, Git
repository, branch, RAG, database, process, localhost); update the configuration inventory,
Known Issues, and ADR deviations to match the implemented state; extend documentation-quality
checks for stale runtime-profile terms and retired configuration keys with an explicit
allowlist for unrelated "local" meanings.

## Target Files or Areas
- `docs/adr/ADR-004-environment-failure-handling-policy.md`
- A new Production-only ADR (if superseding, per Implementation Intent)
- `docs/adr-index.md`
- `docs/00_security_01_architecture-and-trust-boundaries.md`
- `docs/04_mcp_06_02_configuration-file-inventory.md`
- `docs/05_agent_08_01_configuration-loading-agent-config.md`
- MCP and Agent startup/failure-policy documents
- Deployment, operations, troubleshooting, and testing guides
- Known Issues documents
- `.github/ISSUE_TEMPLATE/` (if present)
- `tools/check_docs_quality.py` and `config/doc_quality_rules.json` (rule extension only)
- `docs/00_governance_04_documentation-checks.md`

Confirm exact canonical filenames before editing.

## Required Changes
- Decide whether to supersede ADR-004 with a new ADR or revise it in place; either way, preserve decision history explicitly.
- Define the canonical Production-only/loopback-only decision content listed in Implementation Intent.
- Update the ADR index and all canonical references to point at the final decision.
- Remove active documentation presenting Local mode/profile, Local warning-only behavior, optional Local authentication, or Local-only sandbox relaxation as supported behavior; preserve unrelated "local" usages.
- Update the configuration inventory to list only files that exist after migration; record retired keys and their startup failure behavior.
- Update deployment/operations checklists (loopback checks, MCP credential checks, allowlists/tool safety tiers, workflow/database validation, routing/tool-definition drift checks, audit logs, socket inspection, restart-only settings, recovery steps that do not enable Local mode or public binding).
- Update Known Issues and ADR deviations to reflect the completed implementation.
- Extend documentation-quality checks for stale runtime-profile terms and retired configuration keys, with an allowlist for unrelated "local" meanings.
- Update issue-completion guidance so code, tests, ADRs, Known Issues, configuration references, and operations documents are synchronized in the same change.

## Constraints
- Do not change implementation code in this documentation issue.
- Do not remove unrelated uses of "local".
- Do not claim Event Bus authentication exists if it remains loopback-only without authentication.
- Do not collapse process-specific configuration ownership.
- Do not leave the superseded ADR as an active canonical decision.
- Cite verified implementation functions and tests in Resolution Notes where the repository's documentation standard requires evidence.

## Acceptance Criteria
- No active ADR treats Local mode as supported; a canonical Production-only/loopback-only decision exists.
- The ADR index and related canonical sources reference the new decision.
- Active documentation no longer describes runtime Local-profile behavior; unrelated uses of "local" remain accurate.
- The configuration inventory matches the repository; retired keys are absent from current examples/references.
- Per-process configuration ownership remains documented; operations documentation includes actual listener verification; restart-required settings are clearly identified.
- Known Issues and ADR deviations match the implemented state.
- Documentation-quality checks detect stale profile terms and retired keys without flagging legitimate local-computing terminology.
- Issue-completion guidance requires documentation synchronization.

## Testing Expectations
Run all documentation-quality and link/reference checks
(`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`).
Run repository searches for retired profile keys and runtime-profile wording. Manually review
all remaining uses of "local". Verify every referenced configuration file and test name
exists. Confirm Known Issues statuses and ADR deviations match current implementation
evidence.

## Documentation Impact
This issue is entirely documentation and governance work.

## Out of Scope
- Runtime, configuration, authentication, network, or deployment implementation changes.
- A general rewrite of unrelated design documents.
- Event Bus authentication implementation.

## Dependencies
Depends on `localremoval`, `loopbackonly`, `mcpauth`, and `localcleanup` reaching a stable
implemented state before this issue's documentation can accurately describe it as final —
drafting the canonical ADR content can start earlier, but publishing it as Accepted should wait
for the dependent implementation.

## Unresolved Questions
Whether to supersede ADR-004 with a new ADR or revise it in place is itself a governance
decision (see `localremoval`'s own Unresolved Questions on the same point) — resolve
consistently with that issue's sign-off.

## AI Implementation Instruction
Read the canonical governance and ADR rules before editing. Use repository-wide searches, but
review each "local" match semantically. Update all references to a superseded ADR in one
change. Do not mark an issue resolved based only on another document; verify the implementing
code and tests where evidence is required.
