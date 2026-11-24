Generated at: 20261124-093929

# Rewrite Agent memory, CLI, and Session DB documentation for Repository Context and Episodic Memory

## Priority
Medium

## Summary
Rewrite the Agent memory, CLI, reload, diagnostics, context-budget, Session DB backup, and recovery documentation so they consistently describe Repository Context and Episodic Memory, and remove the obsolete Semantic Memory model, Memory JSONL, manual memory operations, and the `/memory` command contract.

## Background
Source: `memo-issue.md`. The Agent documents live under `docs/23_agent/` (`agent_07_01`, `07_03`, `07_06` to `07_10`, `agent_09_01_data-layer-session-db.md`, `agent_11_01` to `agent_11_04` confirmed present). The amended ADR-008 from issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md is the authority this documentation must match. Reference inputs include `registry/manifests/memory_api.yaml` and `registry/manifests/agent_api.yaml`.

## Problem
The Agent documentation still describes the old memory system:
- Semantic and Episodic memories are sibling persistent types; User Semantic and manual memory writes are described.
- Memory JSONL is an archive or rebuild source; pin/unpin, prune, reindex, and rebuild are user-facing; `/memory` is part of the CLI and help model.
- Repository Context is not represented as a non-persistent context source.
- Session DB backup and recovery documentation does not say that Episodic Memory is restored with the complete Session DB while Repository Context is reloaded from source files.
- `/stats`, `/context`, `/debug verbose`, and `/reload` do not own the diagnostic responsibilities previously assigned to `/memory`.

## Reason for Change
Updating only the memory overview would leave the CLI, Session DB, reload, context budgeting, generated references, and operations guidance inconsistent with each other and with ADR-008. Non-critical documentation mismatch, so Medium; it cannot start before the ADR decisions exist.

## Implementation Intent
Present two clearly separated mechanisms.
- Repository Context: loaded directly from explicitly configured repository files, source files authoritative, not stored in SQLite or JSONL, no persistent FTS or Vector index, reloaded atomically at startup or through `/reload`, selected sections injected only for the active turn.
- Episodic Memory: the Agent's only persistent long-term memory, generated internally from reusable work events rather than generic Q&A, stored in `session.sqlite`, FTS and Vector indexes derived, no user-facing add, list, search, pin, delete, prune, or rebuild, managed by internal retention, consistency, backup, and recovery processes.
CLI and recovery behavior must be understandable without exposing individual Episodic entries.

## Target Files or Areas
- `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`, `agent_07_03_cli-and-commands-command-registry.md`, `agent_07_06_cli-and-commands-hot-reload.md`, `agent_07_07_cli-and-commands-slash-commands-session-mcp.md`, `agent_07_08_cli-and-commands-slash-commands-context-plan.md`, `agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`, `agent_07_10_cli-and-commands-slash-commands-memory-other.md`
- `docs/23_agent/agent_11_01_memory-overview-and-modes.md`, `agent_11_02_memory-gate-data-model-search.md`, `agent_11_03_memory-module-reference.md`, `agent_11_04_memory-module-reference-generated.md`
- `docs/23_agent/agent_09_01_data-layer-session-db.md` and the Session DB recovery documentation (exact file under `docs/` to confirm)
- `registry/manifests/memory_api.yaml`, `registry/manifests/agent_api.yaml` (generated-reference inputs)

## Required Changes
A. Memory architecture
- [ ] Remove Semantic Memory, User Semantic, and the `MemoryType` / `SourceType` explanations that imply the dual persistent model; remove Memory JSONL, JSONL import and rebuild, pin/unpin, manual write, and user CRUD documentation.
- [ ] Define Repository Context as read-only context from explicitly configured repository files; state it is not persisted, not backed up in the Session DB, and not persistently indexed. Define authority values such as `canonical` and `observed` only if they remain part of the approved configuration model.
- [ ] Define Episodic Memory as the only persistent Agent memory; document its event categories only after final names are confirmed; state that generic Q&A and Assistant-generated proposals are not persisted as durable rules; state SQLite backup as the only recovery source.

B. CLI
- [ ] Remove `/memory` from the CLI reference, help, command registry documentation, examples, and completion documentation; state it is not retained as a compatibility alias.
- [ ] Document Repository Context reload under `/reload` with atomic behavior: load all sources into a candidate snapshot, reject the complete reload on validation failure, keep the active snapshot, apply the new snapshot only to subsequent turns.
- [ ] Add Repository Context source count, loaded count, character total, last load, and load-error summary to `/stats`; add Episodic Memory enabled state, aggregate count, last extraction, last prune, search mode, and consistency summary to `/stats`.
- [ ] Add Repository Context and Episodic Memory token usage to `/context` with system prompt, conversation, tool schemas, and response reserve; add source/section selection, exclusion, fallback, and budget diagnostics to `/debug verbose`.
- [ ] State that diagnostics do not expose individual Episodic contents, IDs, secrets, or personal information.

C. Session DB backup and recovery
- [ ] State that Episodic Memory is inside Session DB backup and full recovery scope and that Repository Context is reloaded from configured files, not restored from backup; remove JSONL-based memory recovery instructions.
- [ ] Document whether schema mismatch permits destructive Session DB recreation or requires migration; if undecided, record a known deviation instead of inventing a policy.
- [ ] Clarify `/session recover` when it restores the complete Session DB, and that `/clear`, `/undo`, session deletion, and session purge give no user-level Episodic deletion semantics unless the approved design says so.

D. Context budget
- [ ] Document final-payload budgeting across system prompt, Repository Context, Episodic Memory, conversation history, tool schemas, current input, and response reserve; the reduction order (low-ranked Episodic Memory, low-ranked Repository Context sections, then older history); that mandatory canonical Repository Context is never silently removed; and the failure behavior when mandatory input exceeds the context limit.

E. Module and generated references
- [ ] Rename the old Memory Layer documentation to Episodic Memory Layer where appropriate; add a separate Repository Context design section or chapter; remove JSONL store, import, pin, manual write, and `/memory` command APIs from module references; update manifests and regenerate generated sections.

## Constraints
- Final Episodic event category names, authority values, configuration keys, and diagnostic fields are documented only after they are confirmed in the approved design or source; otherwise marked Needs Confirmation.
- Generated sections change only through the generator.
- Must match amended ADR-008; documentation follows `skills/DESIGN.md` "Docs content policy" and is written in English.

## Acceptance Criteria
- [ ] No current Agent specification describes the old Semantic/Episodic dual persistent model or Memory JSONL as a backup or recovery source.
- [ ] `/memory`, pin/unpin, manual memory write, and JSONL rebuild are absent from the current CLI contract.
- [ ] Repository Context and Episodic Memory have separate source-of-truth, storage, reload, retrieval, and recovery descriptions.
- [ ] `/stats`, `/context`, `/debug verbose`, `/reload`, and `/session recover` responsibilities are consistent across all documents, and diagnostics expose aggregate state only.
- [ ] Agent documentation matches amended ADR-008.

## Testing Expectations
Documentation-only: `uv run python tools/check_docs_consistency.py --domain agent` (includes slash-command drift against `command_defs_list.py`), `uv run python tools/generate_reference_table.py --check`, Markdown/link checks via `uv run pre-commit run --all-files`, and the checkers in `rules/tool-gates.md` for `docs/` changes.

## Documentation Impact
Yes. All documents above. Record intent, boundaries, constraints, failure behavior, and known deviations (for example an undecided schema-mismatch policy) and Needs Confirmation items.

## Out of Scope
- Implementing Repository Context, Episodic Memory, `/reload` changes, or removing `/memory` in code.
- ADR changes (see issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md) and EventBus documents (see issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md).

## Dependencies
- Depends on issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md (amended ADR-008).
- Blocks issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md.

## Unresolved Questions
- `不明`: final Episodic event category names.
- `不明`: whether `canonical` and `observed` authority values remain in the approved configuration model.
- `不明`: schema-mismatch policy for the Session DB (recreate or migrate).
- `不明`: which document under `docs/` holds Session DB backup and recovery text beyond `agent_09_01_data-layer-session-db.md`, and whether the diagnostic fields are covered by an approved implementation issue.

## AI Implementation Instruction
Edit only the Agent documents and manifest inputs listed. Do not edit generated sections by hand. Do not invent category names, configuration keys, or diagnostic fields; mark them Needs Confirmation. Do not change code. Stop and report if the amended ADR-008 is not yet approved.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-093929
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`, `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/23_agent/agent_11_01_memory-overview-and-modes.md`, `docs/23_agent/agent_11_04_memory-module-reference-generated.md`, `registry/manifests/memory_api.yaml`, `registry/manifests/agent_api.yaml`
