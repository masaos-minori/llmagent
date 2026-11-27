# Synchronize governance, canonical documentation, manifests, and generated references

## Priority
Medium

## Summary
Update ADRs, the Approval Ledger, Known Issues, EventBus and Agent documentation, configuration references, manifests, and generated references so they describe the implemented system.

## Background
Source: bundle item M-02. Verified against master on 2026-11-27:
- `Explicit in code`: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` holds `EVENTBUS-002`, `SHARED-003` to `SHARED-007`, and the ledger (`AAL-042` pending); `docs/23_agent/`, `docs/24_eventbus/`, `docs/10_adr/`, `config/documentation_canonical_sources.toml`, and `tools/generate_reference_table.py` exist.
- Related archived work: `issues/done/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md` to `issues/done/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md` already amended the ADRs and the Agent and EventBus documents toward the target model; this issue covers what the implementation changes afterwards.

## Problem
Runtime implementation alone is incomplete if current specifications still expose removed JSONL, Semantic Memory, pinning, manual writes, or obsolete commands; documentation alone must not close implementation mismatches before evidence exists.

## Reason for Change
The architecture is spread across ADRs, governance inventory, canonical documents, typed configuration, manifests, and generated references; they must agree once implementation lands. Timing: after the implementation issues.

## Implementation Intent
Make every authoritative and generated artifact describe the implemented system, preserve historical records, and keep unresolved gaps active until proven complete.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/`
- `docs/23_agent/`, `docs/24_eventbus/`
- `registry/manifests/`, `config/documentation_canonical_sources.toml`, `tools/generate_reference_table.py`

## Required Changes
- Complete the retention-registry Approval Record and ledger processing from the maintainer's decision; update `EVENTBUS-002` after implementation and verification; update or remove `SHARED-003` to `SHARED-007` only with evidence.
- Update EventBus schema, administration, replay, subscribe, retention, capacity, health, and API documents.
- Add or update the Repository Context design document; rename the active Memory design to Episodic Memory where appropriate; update Agent CLI, reload, stats, context, debug, Session DB, backup, recovery, configuration, and operations documents.
- Remove `/memory`, JSONL, legacy `MemoryEntry`, Semantic Memory, pin, manual-write, and rebuild contracts from current specifications.
- Update configuration-ownership and API manifests; regenerate the Agent Memory and EventBus references with the official generators and never hand-edit guarded generated blocks; run removed-name scans.

## Constraints
- Follow `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content policy — remove (no file trees, signature tables, implementation-location mapping, port numbers, or concrete configuration values).
- Documentation is in English (`skills/DESIGN.md` Output language); preserve historical records; do not close a Known Issue without evidence.

## Acceptance Criteria
- Governance records match the implementation state.
- Current documentation contains only current contracts; generated references contain only current APIs and symbols.
- Configuration references match typed models and validators; historical records stay accurate.
- Generated-reference drift checks pass.

## Testing Expectations
Documentation consistency checkers from `rules/tool-gates.md` "When to run which tool", `tools/generate_reference_table.py --check`, and removed-name scans.

## Documentation Impact
This issue is the documentation change itself: intent, boundaries, constraints, failure behavior, operational notes, Known Issues, and Needs Confirmation items.

## Out of Scope
- Implementation code and ADR invariant evidence updates and the full validation run (issues/20261127-085938_amem010_final-validation-gate.md).

## Dependencies
- Depends on issues/20261127-085932_amem004_eventbus-retention-registry.md, issues/20261127-085933_amem005_episodic-retention-policy.md, issues/20261127-085934_amem006_sqlite-capacity-policies.md, issues/20261127-085935_amem007_context-budget-diagnostics.md, and issues/20261127-085936_amem008_legacy-memory-removal.md.
- Blocks issues/20261127-085938_amem010_final-validation-gate.md.
- Documentation drafting may overlap earlier; completion waits for implementation.

## Unresolved Questions
- `不明`: the maintainer's `AAL-042` approval record (see issues/20261127-085932_amem004_eventbus-retention-registry.md).
- `不明`: which parts of the source's documentation scope were already delivered by `adrdoc001` to `adrdoc004` (to be settled at plan time against current `docs/`).

## AI Implementation Instruction
Edit documents only to match verified implementation. Never write approver or date fields. Use official generators for generated blocks.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085937
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/`, `docs/23_agent/`, `docs/24_eventbus/`, `registry/manifests/`, `config/documentation_canonical_sources.toml`, `tools/generate_reference_table.py`
