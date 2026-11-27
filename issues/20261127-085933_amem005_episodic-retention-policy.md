# Implement state-aware Episodic Memory retention

## Priority
High

## Summary
Define configuration-managed Episodic Memory retention defaults and implement state-aware retention using event type, resolution state, recurrence, importance, relations, legal hold, backup state, and database consistency.

## Background
Source: bundle item H-05. Verified against master on 2026-11-27:
- `Explicit in code`: `memory_retention_days` and `prune_old_memories` exist in `scripts/` and `tests/`; legacy retention is a single age-based setting.
- `Explicit in code`: `scripts/db/maintenance.py`, `scripts/db/store_impl.py`, `scripts/db/schema_sql.py`, `scripts/agent/config_dataclasses.py`, and `scripts/agent/services/config_validators.py` exist.
- `Documentation only`: Known Issues `SHARED-004` and `SHARED-005` in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` track the undecided event categories and per-event-type periods; ADR-008 holds the stable principles.
- `Needs confirmation`: the numeric defaults below come from the source bundle; they are configuration defaults, not ADR decisions, and must be confirmed by the maintainer before they are fixed in `config/agent.toml`.

## Problem
Age-only retention cannot protect unresolved failures, recurring failures, open review findings, legal holds, unknown event types, or events required by active relations, and it does not guarantee consistent deletion of canonical events and derived FTS or Vector state.

## Reason for Change
Retention must exist before the legacy removal (issues/20261127-085936_amem008_legacy-memory-removal.md) retires the single legacy setting. It depends on the canonical schema, taxonomy, and relations of issues/20261127-085931_amem003_episodic-core-recovery.md, and not on EventBus retention or other stores' capacity.

## Implementation Intent
Keep stable principles in ADR-008; keep changeable day counts, intervals, batch limits, and thresholds as typed defaults in Agent configuration. Delete an event only when eligibility is proven and canonical and derived state can be updated consistently.

## Target Files or Areas
- `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`
- `scripts/agent/memory/`, `scripts/db/maintenance.py`, `scripts/db/store_impl.py`, `scripts/db/schema_sql.py`
- `tests/agent/memory/`, `tests/agent/config/`, `tests/db/`
- `docs/23_agent/agent_11_01_memory-overview-and-modes.md`, `docs/23_agent/agent_11_02_memory-gate-data-model-search.md`

## Required Changes
- Configuration: replace the single `memory_retention_days` setting with event-type-specific settings; add defaults of 90 days for `investigation_result` and `work_result`, 180 days for `resolution` and resolved `review_finding`, 365 days for `decision_history`, and 180 days for a resolved `failure` (from `resolved_at`) and a recurring `failure` (from `last_recurred_at`); add maintenance defaults (interval 24 hours, batch size 500, maximum 1,000 rows per cycle, high-importance threshold 0.8); define unresolved failures, unresolved review findings, and legal hold as non-expiring by age; preserve unknown event types; add typed fields and validators, including `batch_size <= max_rows_per_cycle`.
- Retention: implement state-aware eligibility queries over event type, resolution state, recurrence, importance, active relations, legal hold, backup state, and database consistency; use `resolved_at` and `last_recurred_at` per the canonical contract; delete canonical events and derived FTS and Vector state as one consistent operation; add a dedicated bounded retention task integrated with the lifecycle; record last run, result, deleted count, blocked count, and failure reason; separate or retire the age-only `prune_old_memories()` path; remove the legacy single field from the active configuration contract; update `SHARED-004` and `SHARED-005` only after evidence exists.

## Constraints
- Do not place numeric retention values in ADR-008 or copy them into design documents (`skills/DESIGN.md` No concrete configuration values).
- Do not reuse age-only pruning; do not delete an event when eligibility cannot be proven.
- Do not close `SHARED-004` or `SHARED-005` through documentation alone.

## Acceptance Criteria
- Configuration, typed models, validators, and canonical documentation agree.
- No Episodic event is deleted solely because of age, and unknown types are preserved.
- Canonical events and derived indexes remain consistent after a purge.
- Retention is bounded by the batch and per-cycle limits.
- `SHARED-004` and `SHARED-005` can be removed with implementation and test evidence.

## Testing Expectations
Defaults and validation; cross-field validation; event-type and state eligibility; unresolved failure and review-finding preservation; recurring failures; legal hold and relations; unknown-type fail-closed; FTS and optional Vector consistency; batch and per-cycle limits; task lifecycle and failure diagnostics. Run `rules/toolchain.md`.

## Documentation Impact
Retention principles and failure behavior in the Agent memory documents; defaults are described by policy and point to `config/agent.toml`. Handled in issues/20261127-085937_amem009_docs-manifests-sync.md.

## Out of Scope
- EventBus retention (issues/20261127-085932_amem004_eventbus-retention-registry.md) and capacity for the five other stores (issues/20261127-085934_amem006_sqlite-capacity-policies.md).

## Dependencies
- Depends on issues/20261127-085931_amem003_episodic-core-recovery.md.
- Blocks issues/20261127-085936_amem008_legacy-memory-removal.md and issues/20261127-085937_amem009_docs-manifests-sync.md.

## Unresolved Questions
- `不明`: maintainer confirmation of the numeric defaults and of the `last_recurred_at` and `resolved_at` field contract.
- `不明`: the approved definition of legal hold and backup-state eligibility.

## AI Implementation Instruction
Implement retention only for Episodic events. Do not add speculative defaults beyond those listed. Stop and report if the canonical event contract from issues/20261127-085931_amem003_episodic-core-recovery.md does not yet define `resolved_at` and `last_recurred_at`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085933
- **Related target files**: `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/memory/`, `scripts/db/maintenance.py`, `scripts/db/store_impl.py`, `scripts/db/schema_sql.py`
