## Goal
- `REQ-001`: `/memory list` takes the documented arguments, default 20 and at most 200, and prints short IDs.
- `REQ-002`: `/memory delete` asks `[y/N]` before deleting.
- `REQ-003`: `/memory prune [--days <n>]` validates `--days`, confirms with the number of memories it will delete, and keeps pinned memories.

## Scope
- `scripts/agent/commands/memory_data_ops.py` only: the `memory_list`, `memory_delete`, and `memory_prune` handlers and new private helpers. The registry, the delete store query (`updated_at`), the tests, and the docs are other rows' documents.

## Assumptions
- `/memory` stays a synchronous handler; a blocking `input()` is acceptable for the prompt (Plan UNK-04).
- `HybridRetriever.search(MemoryQuery(...), branch=...)` returns hits with an `entry` (already used by the removed search handler) and `store.search_by_type(memory_type, limit)` returns entries (already used by `memory_list`).
- `SQLiteMemoryDeleteStore.collect_prunable_ids(days)` returns the ids `prune` deletes (pinned excluded); the other row switches its condition to `updated_at`.
- The `--dry-run` flag of `delete` and `prune` stays unchanged and undocumented (Plan UNK-02).

## Design decisions
- A module-level `_confirm` (new) takes a prompt, calls `input`, and returns true only for `y` or `yes` (case-insensitive, stripped); `EOFError` and any other answer return false.
- Argument parsing moves into small helpers so `memory_list`, currently rated D (26) by `radon`, does not grow: `_ListOptions` (new) is a small frozen dataclass (`limit`, `memory_type`, `pinned_only`, `query`), and `_parse_list_options` (new) returns it or `None` after writing a validation error; `_parse_prune_days` (new) returns the day count or `None` after writing a validation error.
- `prune` takes its count and ids from `collect_prunable_ids`, not from `count_prunable`, which also counts pinned rows.

## Alternatives considered
- Asynchronous `/memory` with `asyncio.to_thread(input)`: deferred (Plan UNK-04); it changes the handler signature and the dispatch tests.
- A shared confirmation service for all commands: rejected as larger than the Plan's scope (no other slash command prompts today).

## Implementation
### Target file
`scripts/agent/commands/memory_data_ops.py`

### Procedure
- Add `_confirm` (new), `_ListOptions` (new), `_parse_list_options` (new), and `_parse_prune_days` (new) above `MemoryDataOps`.
- `memory_list`: call `_parse_list_options` (new); on `None` return. With `--query`, take entries from `mem.retriever.search(MemoryQuery(query=..., limit=200), branch="")` (hits to entries); otherwise take up to 200 entries from `mem.store.search_by_type` (one call per type, or the single requested `--type`), ordered pinned first then by importance as today. Then apply `--type` and `--pinned`, slice to `limit`, and print the table with the first 8 characters of each memory id (header `ID`).
- `memory_delete`: keep argument handling, id resolution (M-03, M-04), and the `--dry-run` branch. Before `write_delete`, call `_confirm` (new) with `Delete memory <id>? [y/N]: `; when it returns false, write `  [memory] Cancelled: nothing was deleted` and return without deleting.
- `memory_prune`: call `_parse_prune_days` (new) on the arguments with `--dry-run` removed; it accepts `--days <n>` with an integer of at least 1 (default `ctx.cfg.memory.memory_retention_days` when `--days` is absent) and writes the validation error `/memory prune [--days <n>]` for a missing, non-integer, or non-positive value or any other token. Open a read connection and take `collect_prunable_ids(days)` from `SQLiteMemoryDeleteStore`; use its length as the count. With `--dry-run`, report the count as today and return. With a count of zero, report that nothing is prunable and return without a prompt. Otherwise call `_confirm` (new) with `Delete <count> memories not updated for <days> days? [y/N]: `; on false write the cancellation message and return; on true run `prune_old_memories(db, days)` and the existing event and audit emission.
- Remove the `count_prunable` import from `memory_prune`; do not change `count_ops.py`.

### Method
- `_parse_list_options` (new): iterate tokens; a token that is all digits sets `limit` (error unless 1 to 200); `--type` requires the next token to be `semantic` or `episodic`; `--pinned` sets the flag; `--query` consumes following tokens up to the next token that starts with `--` and joins them with a space (error when empty); any other token starting with `--` (including `--source` and `--branch`) is an unknown-option validation error; any other bare token is an error. Default `limit` is 20.
- Write validation errors through `self._out.write_validation_error` with the documented usage text, as the existing handlers do.
- `_confirm` (new) must not raise; wrap `input` in a try for `EOFError` only.
- Open `SQLiteHelper("session")` as the existing code does; read for the id collection, `write_mode=True` for the deletion.

### Details
- Keep `_MIN_SHORT_ID = 8`; the listing prints `memory_id[:8]` and `_resolve_id` already accepts it.
- `--pinned` filtering happens before the slice so pinned entries are not lost to the limit (the old code filtered after the limit).
- `radon` baseline: `memory_list` D (26), `memory_delete` B (9), `memory_prune` B (9); the helpers should leave `memory_list` at or below its baseline.
- The removed `list` forms (`--source`, `--branch`, positional type) are rejected with the unknown-option error; no compatibility shim is added.

## Compatibility considerations
- Behavior change by design: `list` no longer accepts `--source`, `--branch`, or the positional type, the default limit changes from 10 to 20, and `delete` and `prune` need an explicit `y`. `pin`, `unpin`, `status`, `reindex`, and `rebuild` are untouched.

## Security considerations
- Confirmation reduces accidental destructive operations; no new inputs reach SQL (ids and day counts are validated or come from the database). The prompt writes no secrets.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_memory_data_ops.py tests/agent/commands/test_cmd_memory.py -v`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/agent/commands/memory_data_ops.py -c pyproject.toml`, `uv run vulture scripts/agent/commands/memory_data_ops.py --min-confidence 80`, `uv run radon cc scripts/agent/commands/memory_data_ops.py -s`
- `uv run python tools/check_suppression_justification.py`, `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- The three handlers behave as the Plan's REQ-001 to REQ-003 state, and the helpers are the only new code.
- `memory_list` complexity is not above its baseline; lint, type, architecture, and security checks report no new findings.
- The handler tests (other row) and the full suite pass; deployment per `skills/deploy/SKILL.md` is a Plan step after validation.

## Out of scope
- The registry, the delete store query, `count_ops.py`, `cmd_memory.py`, the `--dry-run` flag, asynchronous confirmation, the dead `memory_search` and `memory_show` handlers, and all docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_confirm` (new) and the argument parsers (new) and rework `memory_list` | Pending | — | — | |
| 2 | Add the confirmation to `memory_delete` and rework `memory_prune` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (list), REQ-002 (delete confirmation), REQ-003 (prune forms, confirmation, count)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: scripts/agent/commands/memory_data_ops.py
