# Implement capacity policies for the five non-EventBus SQLite stores

## Priority
High

## Summary
Define configuration-managed capacity defaults and implement store-specific metrics, warning and critical behavior, write admission, readiness, diagnostics, and recovery for `session.sqlite`, `workflow.sqlite`, `rag.sqlite`, `mcp_dedup.sqlite`, and `mdq.sqlite`.

## Background
Source: bundle item H-06. Verified against master on 2026-11-27:
- `Explicit in code`: all five store names appear in `scripts/` and `config/`; the listed files `scripts/db/config.py`, `scripts/db/helper.py`, `scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/shared/mcp_dedup_config.py`, `scripts/mcp_servers/mdq/`, `config/mdq_mcp_server.toml`, and `registry/manifests/config_ownership.yaml` exist.
- `Documentation only`: Known Issue `SHARED-006` and ADR-008 require a capacity policy for every store; ADR-008 keeps thresholds out of the ADR.
- `Needs confirmation`: the source states `mcp_dedup.sqlite` already has retry-class-specific fail-open and fail-closed behavior; verify in `scripts/shared/mcp_dedup_config.py` and the dedup server code before changing anything.
- Related archived issue: `issues/done/20261120-115844_mcpdl005_retention-capacity-monitoring.md` (check what it already delivered before planning).

## Problem
Capacity support is incomplete and inconsistent across the five stores, and one universal critical action would be unsafe because the stores have different ownership and failure contracts.

## Reason for Change
ADR-008 requires a policy for every store and `SHARED-006` is open. The work is independent of EventBus retention and the Episodic schema, so it can proceed in parallel.

## Implementation Intent
Keep numeric thresholds outside ADR-008. Put defaults in each owner process's typed configuration, expose one shared metric vocabulary, and enforce behavior suited to each store.

## Target Files or Areas
- `config/agent.toml`, `config/mdq_mcp_server.toml`, RAG owner-process configuration (`Unknown`), MCP dedup configurations (`Unknown`)
- `scripts/db/config.py`, `scripts/db/helper.py`, `scripts/db/maintenance.py`, `scripts/db/rotation.py`
- `scripts/shared/mcp_dedup_config.py`, `scripts/mcp_servers/mdq/`, Agent health and stats code (`Unknown`)
- `registry/manifests/config_ownership.yaml`, `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`

## Required Changes
- Contract and configuration: define metrics for database size, WAL size, free disk, filesystem usage, growth rate, verified backup age, retention lag, and integrity state; add defaults outside ADR-008 (filesystem usage warning 70% and critical 85%; free disk warning below 20% and critical below 10%; WAL-to-DB ratio warning above 25% and critical above 50%; verified backup age warning above 24 hours and critical above 72 hours; retention lag warning above 2 cycles and critical above 5; integrity failure critical); assign each store to its existing owner configuration without a shared `capacity.toml`; define warning, critical, write-admission, readiness, and operator-recovery behavior per store; preserve the established retry-class behavior of `mcp_dedup.sqlite`; update `SHARED-006` with owners, specifications, and evidence.
- Per-store behavior: collect all metrics and read thresholds from the owning process; `session.sqlite` rejects new Session, Message, and Episodic writes at critical while keeping safe diagnostics; `workflow.sqlite` stops accepting new tasks and never reports success when state cannot be persisted; `rag.sqlite` stops ingestion and rebuild but allows safe reads from a consistent index; `mcp_dedup.sqlite` reports capacity state without overriding retryability; `mdq.sqlite` stops index refresh but allows safe reads; expose state in health, stats, logs, and metrics; require revalidation before critical returns to normal; document operator recovery for every store.

## Constraints
- Do not put numeric thresholds in ADR-008 or in design documents.
- Do not apply one universal critical action to all stores; do not bypass ADR-004 or dedup retryability contracts.
- Do not close `SHARED-006` through documentation alone.

## Acceptance Criteria
- Every store has an owning configuration and an operations specification.
- Thresholds can change without editing ADRs or source code.
- No capacity-critical store is reported as normal.
- Store-specific safety behavior is enforced and tested.
- `SHARED-006` can be removed with complete evidence.

## Testing Expectations
Configuration ownership and defaults; warning and critical thresholds for each metric; store-specific write admission; readiness and health classification; dedup retry-class non-regression; recovery and revalidation; integrity-failure and backup-age cases. Run `rules/toolchain.md`.

## Documentation Impact
Per-store capacity policy, readiness classification, and operator recovery in the operations documents and the configuration-ownership manifest; no concrete threshold values in prose. Handled in issues/20261127-085937_amem009_docs-manifests-sync.md.

## Out of Scope
- EventBus capacity and retention (issues/20261127-085932_amem004_eventbus-retention-registry.md) and Episodic retention (issues/20261127-085933_amem005_episodic-retention-policy.md).

## Dependencies
- N/A: none blocking. Blocks issues/20261127-085937_amem009_docs-manifests-sync.md.
- Check issues/done/20261120-115844_mcpdl005_retention-capacity-monitoring.md for overlap before planning.

## Unresolved Questions
- `不明`: the RAG owner-process configuration file and the Agent health and stats modules (not located in this verification).
- `不明`: maintainer confirmation of the default thresholds.
- `不明`: whether the dedup retry-class behavior described by the source matches current code.

## AI Implementation Instruction
Keep each store's behavior within its own contract; do not add a generic capacity gate. Stop and report if a store's owner configuration cannot be identified; never create a shared capacity file.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085934
- **Related target files**: `config/agent.toml`, `config/mdq_mcp_server.toml`, `scripts/db/config.py`, `scripts/db/helper.py`, `scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/shared/mcp_dedup_config.py`, `scripts/mcp_servers/mdq/`, `registry/manifests/config_ownership.yaml`
