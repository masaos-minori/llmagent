# Map the legacy Memory impact and freeze a replacement-first cutover sequence

## Priority
High

## Summary
Produce a repository-grounded impact map of the legacy Memory implementation and a cutover sequence that builds and validates Repository Context and Episodic Memory before any legacy path is deleted. This issue changes no production behavior.

## Background
Source: the bundle `~/agent_memory_issues/` (item H-01). Verified against master on 2026-11-27:
- `Explicit in code`: legacy symbols are widely referenced. `MemoryType`, `SourceType`, `JsonlMemoryStore`, `import_from_jsonl`, `memory_jsonl_dir`, `rebuild_fts`, `rebuild_vec`, `memory_max_pinned`, `memory_retention_days`, and `prune_old_memories` each appear in `scripts/` and in `tests/`; several also appear in `docs/`.
- `Explicit in code`: the symbols `pin_memory` and `unpin_memory` have no match anywhere in the repository. Pinning lives in `scripts/agent/memory/pin_ops.py` (`pin`, `unpin`) and in the `pinned` column handled by `scripts/agent/memory/write_ops.py` and `retriever.py`. The inventory must search by the real names.
- `Explicit in code`: `write_semantic` and `write_episodic` each match a single file under `scripts/` and a single file under `tests/`.
- `Explicit in code`: the `/memory` command is implemented in `scripts/agent/commands/cmd_memory.py`, `memory_status.py`, `memory_rebuild_ops.py`, `memory_data_ops.py`, and registered in `command_defs_list.py` and `registry.py`.
- `Explicit in code`: `scripts/agent/history/` does not exist; the history code is `scripts/agent/history.py` and `scripts/agent/history_selection_policy.py`. `scripts/agent/repository_context/` does not exist (new work, see issues/20261127-085930_amem002_repository-context-implementation.md).
- `Needs confirmation`: the source states the existing task list deletes JSONL and `/memory` before the replacements exist; that ordering claim is about the source's own task list, not repository code, and is not verified here.

## Problem
Removing legacy modules before every call site, startup and shutdown dependency, and generated reference is known can leave unresolved imports, broken startup or shutdown, stale configuration, invalid generated references, or an unrecoverable Session DB.

## Reason for Change
Every later issue in this bundle depends on a verified inventory and a safe order. The cost of a wrong deletion order is a broken intermediate state; the inventory is cheap by comparison. It is not time-critical beyond unblocking the dependent issues.

## Implementation Intent
Analysis only. Produce one inventory and cutover document from verified repository paths and symbols, classify each reference, and state the replacement-first order. The Session DB policy stays archive-and-recreate from the canonical schema; no in-place migration is introduced.

## Target Files or Areas
- `scripts/agent/memory/`, `scripts/agent/commands/`, `scripts/agent/services/`
- `scripts/agent/history.py`, `scripts/agent/history_selection_policy.py`
- `scripts/agent/factory.py`, `scripts/agent/repl.py`, `scripts/agent/orchestrator.py`, `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`
- `scripts/db/`, `config/agent.toml`, `registry/manifests/`
- `tests/agent/`, `tests/db/`

## Required Changes
- Search the repository for the legacy symbols and settings named in Background, using real names (for example `pin`/`unpin` in `pin_ops.py` instead of the non-existent `pin_memory`), plus the `/memory` command and `MemoryType`/`SourceType` usage.
- Classify each reference as delete, replace with Repository Context, replace with Episodic Memory, move to diagnostics, retain as shared SQLite infrastructure, or preserve as historical documentation.
- Identify Memory service construction, dependency injection, startup, shutdown, configuration reload, and session-end extraction call sites.
- Identify Session DB schema creation, schema fingerprinting, archive-and-recreate, backup, restore, and consistency-check paths.
- Identify the CLI registry, help, completion, `/stats`, `/context`, `/debug verbose`, and `/reload` owners.
- Identify the manifests and generators that produce the Memory API reference.
- Classify every test as remove, rewrite, or retain.
- Write the replacement-first cutover sequence and the list of required files or directories that do not exist yet.

## Constraints
- Do not delete or rename production files in this issue.
- Do not invent paths or symbols; do not treat historical or withdrawn documents as current implementation.
- Do not introduce an in-place Session DB migration.

## Acceptance Criteria
- Every legacy symbol and setting has a verified call-site inventory.
- Every affected test and document is classified.
- The cutover sequence builds and validates replacements before deleting JSONL, Semantic Memory, `/memory`, pin/unpin, or manual writes.
- No later destructive issue depends on an unverified path.
- Missing files and directories required for implementation are listed.

## Testing Expectations
Not required: analysis and documentation only. Verify the inventory by re-running the searches and checking every cited path exists.

## Documentation Impact
The inventory and cutover document is the deliverable; its location is `Needs confirmation` (for example a plan or an `implementations/` procedure). No `docs/*.md` change is required by this issue.

## Out of Scope
- Any production code, configuration, schema, or test change.
- The Episodic and Repository Context implementation (issues/20261127-085930_amem002_repository-context-implementation.md, issues/20261127-085931_amem003_episodic-core-recovery.md).

## Dependencies
- Blocks issues/20261127-085930_amem002_repository-context-implementation.md and issues/20261127-085931_amem003_episodic-core-recovery.md (they build on the inventory).
- Overlaps issues/20261125-103316_adrr010_agent-memory-schema.md (legacy schema removal; it also lists `pinned`, `memory_links`, and the `/memory` paths). Reconcile at plan time so the inventory is produced once.

## Unresolved Questions
- `不明`: where the inventory and cutover document is stored (plan, procedure, or `docs/`).
- `不明`: whether this inventory should be absorbed into `issues/20261125-103316_adrr010_agent-memory-schema.md`, whose Unresolved Questions already say the full list of memory command routes and tests is to be read at plan time.

## AI Implementation Instruction
Do not change production code. Report any symbol or path you cannot verify as `Needs confirmation` instead of guessing. Stop and report if a legacy path is found that is required by a feature outside Memory.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085929
- **Related target files**: `scripts/agent/memory/`, `scripts/agent/commands/`, `scripts/agent/factory.py`, `scripts/db/`, `config/agent.toml`, `registry/manifests/`
