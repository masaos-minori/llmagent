# Implement Repository Context end to end

## Priority
High

## Summary
Implement the non-persistent Repository Context path: typed configuration, secure atomic loading, in-memory section selection, safe prompt framing, `/reload` integration, and operational diagnostics.

## Background
Source: bundle item H-02. Verified against master on 2026-11-27:
- `Explicit in code`: no Repository Context code exists; `RepositoryContextConfig` has no match and `scripts/agent/repository_context/` is absent.
- `Explicit in code`: the likely integration points exist: `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_reload.py`, `scripts/agent/context.py`, `scripts/agent/commands/` (`cmd_context.py`, `cmd_debug.py`, `cmd_config_stats.py`), and `config/agent.toml`.
- `Documentation only`: the approved architecture (Repository Context replaces the repository-backed part of legacy Memory, source files are authoritative) is stated by the source and ADR-008 text; not re-verified here.

## Problem
Without Repository Context the repository-backed knowledge has no replacement for legacy Memory. A partial implementation would be unsafe: configuration without path security allows repository escape, loading without atomic replacement mixes snapshots, selection without framing elevates repository text into instructions, and reload without diagnostics hides the active state.

## Reason for Change
The legacy Memory removal (issues/20261127-085936_amem008_legacy-memory-removal.md) is gated on this replacement. The security properties (path confinement, secret rejection, atomic snapshot, instruction isolation) are interdependent, so they are one issue (Phase 2 grouping: same files, same reviewable change, tested together).

## Implementation Intent
Load only explicitly configured UTF-8 `.md` and `.txt` files inside the repository root, validate the whole source set, reject an unsafe snapshot as a unit, keep the previous snapshot on failure, and inject only relevant sections as isolated reference data for the current turn. Nothing is persisted to SQLite, JSONL, FTS, or a vector index.

## Target Files or Areas
- `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_reload.py`
- a new `scripts/agent/repository_context/` package
- `scripts/agent/context.py`, `scripts/agent/commands/`
- `tests/agent/config/`, `tests/agent/services/`, and new Repository Context tests

## Required Changes
- Configuration: add immutable `RepositoryContextConfig` and `RepositoryContextSourceConfig` models; support enable flag, sources, file-count and character limits, reload behavior, and per-source path, required flag, authority, and maximum characters; restrict authority to the approved values; accept relative paths only; reject duplicate paths and unknown keys; validate limits before loading; integrate with `AgentConfig` and `config/agent.toml` using the typed-validation convention in `rules/coding.md`.
- Loader: resolve the repository root and each source; reject absolute paths, root escape, root-external symlinks, special files, and unsupported types; enforce per-file and aggregate limits; reject UTF-8 errors; treat a missing required source as fatal and a missing optional source as a warning; detect private keys, known credential formats, authorization headers, and password or token assignments; reject the whole candidate snapshot on any unsafe source; keep the live snapshot after a failed reload; never log secret values; store path, authority, content hash, and immutable content; swap only after all sources pass; keep the old snapshot for an in-progress turn.
- Selection and injection: split Markdown by heading and text by paragraph while keeping path, heading, and authority; build an in-memory selector only, using the approved BM25 approach; prefer canonical over observed sources without treating either as System or Developer instructions; merge adjacent sections of the same file and heading when appropriate; limit by the final token budget; frame as reference data with fixed boundaries; escape role-like headings, control characters, role tags, and Markdown fences; never persist injected content in conversation history.
- Reload and diagnostics: extend `/reload` to detect source and configuration changes and reject the whole reload on any invalid source; report source count and aggregate size; add state to `/stats`, token usage to `/context`, and candidate count, selected count, and exclusion reasons to `/debug verbose`; expose no content, secrets, or unsafe paths.

## Constraints
- Do not persist Repository Context in SQLite or JSONL and do not create a persistent FTS or vector index.
- Do not inject repository text as executable instructions; do not partially activate a failed snapshot.
- Follow `skills/DESIGN.md` No secrets in output for logs and diagnostics.

## Acceptance Criteria
- Unsafe sources never reach the LLM payload.
- Snapshot replacement is atomic and a failed reload keeps the previous snapshot.
- Only relevant sections are injected, and Repository Context does not accumulate in conversation history.
- Operators can inspect safe aggregate state through `/stats`, `/context`, and `/debug verbose` without `/memory`.

## Testing Expectations
Unit tests for configuration parsing and unknown keys; root escape, symlink, special-file, encoding, and size limits; secret detection and no-secret-in-log; atomic reload success and rollback; required and optional sources; BM25 ranking, authority preference, adjacent merge, and budget limits; prompt-boundary and instruction isolation; snapshot stability for an in-progress turn; `/reload`, `/stats`, `/context`, and `/debug verbose`. Run the validation sequence in `rules/toolchain.md`.

## Documentation Impact
Repository Context design intent, security boundaries, reload failure behavior, and configuration ownership must be documented, handled in issues/20261127-085937_amem009_docs-manifests-sync.md. Documentation must follow `skills/DESIGN.md` (no concrete configuration values, no implementation-location mapping).

## Out of Scope
- Episodic Memory (issues/20261127-085931_amem003_episodic-core-recovery.md), final-payload budgeting (issues/20261127-085935_amem007_context-budget-diagnostics.md), and removal of legacy Memory (issues/20261127-085936_amem008_legacy-memory-removal.md).

## Dependencies
- Depends on issues/20261127-085929_amem001_memory-impact-cutover-map.md (inventory of reload, stats, context, and debug owners).
- Blocks issues/20261127-085935_amem007_context-budget-diagnostics.md and issues/20261127-085936_amem008_legacy-memory-removal.md.

## Unresolved Questions
- `不明`: the approved authority values, the approved secret-pattern set, and the reload-behavior options; the source refers to them as approved but does not list them. Confirm against ADR-008 and `docs/23_agent/` at plan time.
- `不明`: the approved BM25 parameters and the section-merge rule.

## AI Implementation Instruction
Implement only the Repository Context path. Do not touch Episodic Memory or remove legacy code. Stop and report if an approved value (authority, secret pattern, BM25 setting) is not defined in the repository; never invent it.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-085930
- **Related target files**: `config/agent.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_reload.py`, `scripts/agent/context.py`, `scripts/agent/commands/`
