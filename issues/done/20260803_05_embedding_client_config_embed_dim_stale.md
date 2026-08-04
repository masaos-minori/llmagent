# test_memory_status.py constructs EmbeddingClientConfig with a non-existent `embed_dim` argument

## Priority
High

## Summary
`tests/agent/commands/test_memory_status.py` constructs `EmbeddingClientConfig(..., embed_dim=0,
...)` in its shared `config` fixture and in one inline construction. `EmbeddingClientConfig` has
no `embed_dim` field, so every test that depends on the fixture fails at setup with
`TypeError: EmbeddingClientConfig.__init__() got an unexpected keyword argument 'embed_dim'`.
11 of the file's tests error out and 1 more fails, leaving `cmd_memory`'s status-table rendering
and circuit-breaker display logic effectively untested.

## Reason for Change
`scripts/agent/memory/embedding_client.py`'s `EmbeddingClientConfig` dataclass currently has
exactly these fields: `embed_url`, `timeout`, `max_retries`, `circuit_open_after`,
`circuit_reset_sec`, `local_only`. There is no `embed_dim` field and no obvious renamed
equivalent among these — this looks like a field that was removed from the dataclass (e.g. when
embedding dimensionality became inferred or moved elsewhere) without updating this test file.

## Implementation Intent
Confirm whether embedding dimensionality is tracked anywhere else in the current memory config
(`agent/config_dataclasses.py`'s `MemoryConfig`, or a runtime-detected value) — if so, the test
may need to stop asserting on `embed_dim` entirely rather than just deleting the keyword. If
`embed_dim` truly has no current equivalent, remove the argument from both construction sites
and confirm no assertion in the file actually depends on its value (a quick grep for `embed_dim`
usage beyond construction is needed before deleting).

## Target Files or Areas
- `tests/agent/commands/test_memory_status.py` (`config` fixture and one inline construction)
- `scripts/agent/memory/embedding_client.py` (reference only, not expected to change)

## Required Changes
- Remove the `embed_dim=0` keyword argument from both `EmbeddingClientConfig(...)` call sites in
  the file.
- Grep the file for any assertion referencing `embed_dim` on the resulting config/status object
  and remove or replace it if `EmbeddingClientConfig`/`EmbeddingClientStatus` no longer expose
  that concept.

## Acceptance Criteria
- `pytest tests/agent/commands/test_memory_status.py` collects and all tests pass.
- No remaining reference to `embed_dim` in the file unless it maps to a real current field.

## Testing Expectations
Unit tests (the file itself). Run
`PYTHONPATH=scripts pytest tests/agent/commands/test_memory_status.py -v` after the fix.

## Documentation Impact
None expected, unless investigation shows `embed_dim` was a documented config key elsewhere
(check `docs/` for `embed_dim` references) — if so, flag as a separate Documentation Impact note
rather than silently deleting the doc mention.

## Out of Scope
- Do not add an `embed_dim` field back to `EmbeddingClientConfig` unless investigation shows the
  test was right and the field's removal was an unintentional regression in production code.
- Do not touch other `test_memory_status.py` fixtures/tests beyond the `embed_dim` issue.

## AI Implementation Instruction
Read `scripts/agent/memory/embedding_client.py`'s full `EmbeddingClientConfig` and
`EmbeddingClientStatus` definitions before editing the test, to confirm there is truly no
current equivalent for `embed_dim`. Grep `docs/` and `scripts/` for `embed_dim` to rule out a
live reference elsewhere before deleting it from the test. Keep the fix minimal — remove the
stale argument only; do not restructure the fixture.
