# Implement the /memory command specification (v1.0)

## Priority
Medium

## Summary
Bring the `/memory` command and the JSONL archive in line with specification v1.0 (approved 2026-10-14): subcommands `status`, `list`, `delete`, `pin`/`unpin`, `prune`, `reindex`, `rebuild`; JSONL change events (`delete`, `pin`, `unpin`) that `rebuild` replays; a pin limit; and safer `rebuild` (dry run, `--allow-loss`, backup).

## Background
The specification (MEM-00 to MEM-09, messages M-01 to M-10, acceptance tests 1 to 16) was approved and reflected in docs on 2026-10-14: `agent_07_03`, `agent_07_10`, `agent_11_01`, `agent_11_02`, `agent_11_03`, `agent_09_01`, `agent_08_03`, `agent_10_06`, `agent_04_02`, `deployment_01`. The code does not implement it yet, so the docs describe the target behavior. `agent_11_04` is generated from code and must be regenerated after the code change. The session/memory boundary is covered by the separate responsibility-separation change (`clear_by_session()` was already removed).

## Problem
Verified against the code on 2026-10-14 (specification premises P-1 to P-8 differ from reality in several places):
- `scripts/agent/commands/cmd_memory.py` dispatches `list`, `search`, `show`, `pin`, `unpin`, `delete`, `prune`, `check-consistency`, `rebuild`, `import-jsonl`, `rebuild-fts`, `rebuild-vec`, and `status`; the docstring and `command_defs_list.py` help text list different sets. The spec's P-1 (only status/delete/prune/rebuild) is false.
- `/memory` with no subcommand prints help instead of running `status`; a disabled memory layer prints a different message; an unknown subcommand raises `UnknownSubcommandError`.
- `memory_prune()` accepts `--dry-run` and a positional day count, silently falls back to the default on a non-integer, asks no confirmation, and does not exclude pinned memories (spec: confirmation, `--days`, pinned excluded).
- `memory_rebuild_ops.rebuild()` prints that deletes and pins are NOT replayed and calls `import_from_jsonl()`, which does not replay events, has no `--allow-loss`, and writes no backup.
- `jsonl_store.py` documents that JSONL does not record mutations; no change events are written by delete, pin, or unpin.
- `memory_retention_days` is read and used as the `prune` default (config default 90); `memory_max_pinned` does not exist.
- The FTS fallback count and the `Pinned` line of `/memory status` need checking against MEM-01.

## Reason for Change
Today a rebuild resurrects deleted memories and drops pins, and deletion paths lack confirmation and pin protection. The approved spec makes recovery faithful and destructive operations safe.

## Implementation Intent
- Add change events to the JSONL archive: `{"event", "memory_id", "at"}` lines appended after the SQLite change; memory lines stay unchanged and are told apart by the absent `event` field.
- Teach JSONL reading and `import_from_jsonl()` the replay rules (6.3 of the spec): add/overwrite on memory line, remove on `delete` (re-added by a later memory line), `pinned` update on `pin`/`unpin` when the entry exists, skip and count unparsable lines.
- Rework the subcommands per the spec and remove those the spec does not list, after the open question below is answered. `delete` also removes `memory_links` rows for that memory in one transaction.
- Add `memory_max_pinned` (default 10, at least 1, hot-reloadable) with the config validators, field registry, and `config/agent.toml`.
- Implement `reindex [--fts|--vec]`, the `list` filters, `rebuild` dry-run table 5.8-1, `--allow-loss`, and the pre-run backup of `memories`.
- Emit the specified messages and audit records.

## Target Files or Areas
- `scripts/agent/commands/cmd_memory.py`, `memory_data_ops.py`, `memory_rebuild_ops.py`, `memory_status.py`, `command_defs_list.py`
- `scripts/agent/memory/jsonl_store.py`, `import_ops.py`, `pin_ops.py`, `write_ops.py`, `rebuild_ops.py`, `count_ops.py`
- `scripts/db/maintenance.py`, `scripts/db/store_impl.py` (`prune_old_memories`: pinned exclusion, `memory_links` removal, atomicity)
- `scripts/agent/config_dataclasses.py`, `config_builders.py`, `services/config_validators.py`, `services/config_field_registry.py`, `config/agent.toml`
- `tests/` for each area; `docs/23_agent/agent_11_04_memory-module-reference-generated.md` (regenerate)

## Required Changes
- Implement MEM-00 to MEM-09 and messages M-01 to M-10 as written in the specification; the normative text is the specification (`memo3.md`, v1.0) and the docs listed in Background.
- Write JSONL change events for `delete`, `pin`, `unpin`, and for each memory removed by `prune`; keep SQLite-first ordering and the M-07 warning when the append fails.
- Replace the replay-less import with ordered replay; compute the final state before touching SQLite.
- Back up `memories` as JSONL before a confirmed rebuild and abort if that fails; refuse a confirmed rebuild that would lose SQLite-only memories unless `--allow-loss`.
- Exclude pinned memories from `prune`; make `prune` all-or-nothing (`MaintenanceMode.STRICT`).
- Update `command_defs_list.py` help and the registry consistency tests.

## Constraints
- JSONL stays append-only; existing lines are never rewritten.
- SQLite is the source of truth; JSONL write failures never roll back SQLite.
- No compatibility shims; removed subcommands are removed, with `tools/check_compat_shims.py` patterns where the repository convention applies.
- Deletes and pins made before this change are not in the archive and cannot be reproduced; the first rebuild after release must be a dry run.
- Tests must not open production DBs; use the sandbox config and patched DB helpers.

## Acceptance Criteria
All 16 acceptance tests of the specification pass, in particular:
- `/memory` without arguments shows `status`; with the memory layer disabled only `status` runs and others print M-02 without changing data.
- Short IDs from `list` work for `delete`, `pin`, `unpin`; ambiguous and unknown IDs print M-04 and M-03.
- `delete` and `prune` ask for confirmation; `N` changes nothing; `delete` leaves no row in the four tables and appends a `delete` event.
- The pin limit prints M-05; `prune` never deletes pinned memories and a failure deletes nothing.
- `reindex --fts` works in FTS-only mode and leaves `memories` unchanged.
- `rebuild` dry run changes nothing and shows table 5.8-1; SQLite-only memories block `--confirm` without `--allow-loss`; a backup exists before a confirmed run; deleted memories stay deleted and pins are reproduced.
- A failed JSONL append prints M-07 and keeps the SQLite change; data-changing operations are audit logged; `/session delete` leaves memories.

## Testing Expectations
- Unit tests per subcommand and per replay rule; integration test of delete, pin, rebuild round trip using a temporary JSONL and SQLite.
- Tests for config validation of `memory_max_pinned` and hot reload.
- `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`, bandit, full `pytest` with sandbox config, `diff-cover`.
- Docs checkers and `generate_reference_table.py --type memory`.

## Documentation Impact
The docs in Background already describe the target behavior. After implementation: regenerate `agent_11_04`; check that `agent_07_10` matches the final subcommand set and that the `/memory` help text, `agent_07_03`, and `command_defs_list.py` agree; update the slash-command task list so M-1 is complete (the task list file was not found in this repository).

## Out of Scope
- Manual writing or editing of memories; automatic pruning by retention (MEM-09-2).
- Changes to extraction, injection, and retrieval.
- Recovery of deletes and pins made before change events existed.
- Production deployment.

## Dependencies
- Related to the session/memory responsibility-separation change (already applied to docs and code).
- `deployment_01` upgrade note for recreating `session.sqlite` relies on this `rebuild` behavior.

## Unresolved Questions
- The spec lists seven subcommands, but the code also has `search`, `show`, `check-consistency`, `import-jsonl`, `rebuild-fts`, and `rebuild-vec`. Remove them, keep them, or fold them into `list --query` and `reindex`? The docs currently list only the spec's subcommands.
- Whether `memory_links` rows are removed today by `delete()` and `prune_old_memories()` (P-2) was not verified.
- Whether `write_ops.add()`/`upsert()` are called outside automatic extraction (P-4) was not fully verified; `ingestion.py` is a confirmed caller.
- How to count "FTS fallback count" per search (MEM-01-4) given the current counter semantics (P-8), and where the `Embed skip count` of stored memories comes from.
- Whether `memory_retention_days` still needs its current default of 90 (spec: "existing default").

## AI Implementation Instruction
Implement only what this issue states. Resolve each Unresolved Question against the code before coding, and ask when the answer changes behavior. Follow existing patterns in `scripts/agent/commands/` and `scripts/agent/memory/`; no compatibility code; keep JSONL append-only; never touch `/opt/llm`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-155503
- **Related target files**: scripts/agent/commands/cmd_memory.py, scripts/agent/commands/memory_data_ops.py, scripts/agent/commands/memory_rebuild_ops.py, scripts/agent/memory/jsonl_store.py, scripts/agent/memory/import_ops.py, scripts/db/maintenance.py, scripts/agent/config_builders.py
