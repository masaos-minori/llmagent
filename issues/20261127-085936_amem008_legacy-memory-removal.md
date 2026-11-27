# Cut over to the new information paths and remove legacy Memory features

## Priority
Medium

## Summary
After Repository Context, Episodic Memory, retention, budgeting, reload, and diagnostics pass integration tests, remove JSONL, Semantic Memory, pin and unpin, manual writes, `/memory`, obsolete settings, and dead code in one controlled cutover.

## Background
Source: bundle item M-01. Verified against master on 2026-11-27:
- `Explicit in code`: the legacy surface exists today: `scripts/agent/memory/jsonl_store.py`, `import_ops.py`, `pin_ops.py`, `rebuild_ops.py`, and the `/memory` command files in `scripts/agent/commands/` (`cmd_memory.py`, `memory_status.py`, `memory_rebuild_ops.py`, `memory_data_ops.py`).
- This overlaps the open issue `issues/20261125-103316_adrr010_agent-memory-schema.md` (remove `pinned`, the semantic type, `memory_links`, JSONL assumptions, and `/memory`). Re-verify this issue against current source after that sibling is resolved.

## Problem
Removing legacy paths before replacements are proven creates a broken intermediate state; keeping them afterwards creates dual sources of truth, stale APIs, configuration ambiguity, and generated-reference drift.

## Reason for Change
ADR-008 no longer permits the legacy model. The removal is gated on the replacements, so its timing follows issues/20261127-085930_amem002_repository-context-implementation.md, issues/20261127-085931_amem003_episodic-core-recovery.md, issues/20261127-085933_amem005_episodic-retention-policy.md, and issues/20261127-085935_amem007_context-budget-diagnostics.md.

## Implementation Intent
Perform one controlled cutover after the gate passes, then remove every legacy code, configuration, CLI, manifest, and generated-reference path in the same change set.

## Target Files or Areas
- `scripts/agent/memory/`, `scripts/agent/commands/`, `scripts/agent/factory.py`, `scripts/agent/config_section_builders.py`
- `scripts/db/schema_sql.py`, `scripts/db/store_protocols.py`
- `config/agent.toml`, `registry/manifests/`, `tests/agent/`, `tests/db/`

## Required Changes
- Cutover gate: confirm Repository Context loading, selection, injection, reload, and diagnostics; Episodic extraction, save, retrieval, backup, restore, consistency, and retention; budgeting and diagnostics; Session DB archive-and-recreate; and that no recovery depends on Memory JSONL, each by passing integration tests.
- Removal: remove `JsonlMemoryStore` and JSONL writes, JSONL import and rebuild paths, Semantic and User Semantic paths, pin and unpin and manual-write APIs, the `/memory` definitions, handlers, help category, and completion entries, legacy `MemoryType` and `SourceType` usage when no longer needed, obsolete settings (JSONL, pin, Semantic injection, the legacy single retention setting), obsolete exceptions, shutdown behavior, statistics, package exports, and unused imports; remove or rewrite legacy tests; make `/memory` an unknown command; make long-term write success depend only on the SQLite commit.

## Constraints
- Do not remove anything before the cutover gate passes.
- Preserve historical and withdrawn documentation where required.
- Do not remove shared SQLite, FTS, Vector, backup, or diagnostics utilities still used by current features.
- Follow the deprecation rule in `rules/coding.md` (zero-caller `rg` re-check before deleting).

## Acceptance Criteria
- Repository Context and Episodic Memory are the only active long-term information paths.
- Memory JSONL and `/memory` do not exist in current code or configuration; Semantic Memory, pin and unpin, and manual Memory CRUD do not exist.
- No startup, shutdown, backup, or recovery path depends on removed code.

## Testing Expectations
Startup and shutdown without a JSONL directory; unknown `/memory` command; removed-name repository scan; no import of deleted modules; Session DB and Memory integration tests; no JSONL writes during extraction, deletion, retention, or recovery. Run `rules/toolchain.md`, including import-linter.

## Documentation Impact
Removed contracts must disappear from current specifications and generated references, handled in issues/20261127-085937_amem009_docs-manifests-sync.md; historical records stay accurate.

## Out of Scope
- Building any replacement capability and EventBus `events.jsonl` removal (issues/20261125-103311_adrr005_eventbus-jsonl-removal.md).

## Dependencies
- Depends on issues/20261127-085930_amem002_repository-context-implementation.md, issues/20261127-085931_amem003_episodic-core-recovery.md, issues/20261127-085933_amem005_episodic-retention-policy.md, and issues/20261127-085935_amem007_context-budget-diagnostics.md.
- Overlaps issues/20261125-103316_adrr010_agent-memory-schema.md; decide the owner of the schema and `/memory` removal at plan time.
- Blocks issues/20261127-085937_amem009_docs-manifests-sync.md.

## Unresolved Questions
- `不明`: whether this issue is to be merged with issues/20261125-103316_adrr010_agent-memory-schema.md (a user decision).
- `不明`: which utilities are still used by current features and must be retained (to be settled by the inventory in issues/20261127-085929_amem001_memory-impact-cutover-map.md).

## AI Implementation Instruction
Do not start removal until the cutover gate evidence exists. Stop and report any caller of a symbol you were about to delete.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085936
- **Related target files**: `scripts/agent/memory/`, `scripts/agent/commands/`, `scripts/agent/factory.py`, `scripts/agent/config_section_builders.py`, `scripts/db/schema_sql.py`, `scripts/db/store_protocols.py`, `config/agent.toml`
