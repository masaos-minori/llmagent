# Implementation Procedure: Remove stale `embed_dim` keyword argument from `test_memory_status.py`

## Goal

Make `PYTHONPATH=scripts pytest tests/agent/commands/test_memory_status.py -v` collect and pass
all 17 tests with zero errors/failures, by removing two stale `embed_dim=0,` keyword arguments
from `EmbeddingClientConfig(...)` construction sites. No production source file changes.

## Scope

- In scope: `tests/agent/commands/test_memory_status.py` — delete `embed_dim=0,` at line 30
  (the shared `config` fixture) and at line 77 (the inline `EmbeddingClientConfig(...)` inside
  `test_auto_reset_when_elapsed`).
- Out of scope: `scripts/agent/memory/embedding_client.py` (read-only reference; must not gain an
  `embed_dim` field back); any other test in the file; the stale doc reference at
  `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:67`; unrelated `embed_dim` usages
  tied to `MemoryStore`/`AgentConfig.memory.memory_embed_dim`.

## Assumptions

- `EmbeddingClientConfig` (verified at `scripts/agent/memory/embedding_client.py:31-39`) currently
  defines exactly six fields: `embed_url`, `timeout`, `max_retries`, `circuit_open_after`,
  `circuit_reset_sec`, `local_only`. No `embed_dim` field exists.
- Verified via `grep -n "embed_dim\|EmbeddingClientConfig" tests/agent/commands/test_memory_status.py`:
  the only two `embed_dim=0,` occurrences are at line 30 (fixture `config`, lines 25-31) and line 77
  (inline construction inside `test_auto_reset_when_elapsed`, lines 73-78/lines 72-92 for the full
  test body). No assertion in the file reads `embed_dim`.
- The baseline failure mode (from the source plan) is uniformly
  `TypeError: EmbeddingClientConfig.__init__() got an unexpected keyword argument 'embed_dim'`,
  so removing these two lines is sufficient — no other code path needs a change.

## Design decisions

- Mechanical deletion only: remove the two offending lines verbatim, keep all other constructor
  arguments (`embed_url`, `circuit_open_after`, `circuit_reset_sec`) unchanged and in their current
  order — no reordering, no reformatting.
- No replacement value or new field is introduced; `EmbeddingClientConfig`'s current six-field
  contract is treated as the source of truth and is not modified (test-follows-source, not the
  reverse).

## Alternatives considered

- Re-add `embed_dim` to `EmbeddingClientConfig` to keep the test as-is: rejected — the field was
  intentionally removed from the dataclass in a prior refactor
  (`72939b553 refactor: remove memory_embed_dim config, ...`); reintroducing it would revert that
  change and is explicitly out of scope per the source plan.
- Use `getattr`/defensive construction to tolerate stale kwargs: rejected — unjustified
  indirection (per `skills/python-design` "use abstractions only when justified") for what is a
  two-line, unambiguous deletion.

## Implementation

### Target file

`tests/agent/commands/test_memory_status.py`

### Procedure

1. In the `config` fixture (currently lines 25-31), delete the `embed_dim=0,` line (line 30),
   leaving `embed_url`, `circuit_open_after`, `circuit_reset_sec` as the only constructor
   arguments.
2. In `test_auto_reset_when_elapsed` (currently starting at line 72), delete the `embed_dim=0,`
   line (line 77) from the inline `EmbeddingClientConfig(...)` call, leaving `embed_url`,
   `circuit_open_after`, `circuit_reset_sec` unchanged.
3. Run `rg -n "embed_dim" tests/agent/commands/test_memory_status.py` and confirm zero matches.
4. Run `PYTHONPATH=scripts pytest tests/agent/commands/test_memory_status.py -v` and confirm
   17/17 pass, 0 errors, 0 failures.
5. Run `PYTHONPATH=scripts pytest tests/agent/commands/ --collect-only -q` as a sibling-collection
   sanity check (no new collection errors in `commands/`).
6. Run `ruff check tests/agent/commands/test_memory_status.py` and confirm 0 errors.

### Method

Direct text edit (two single-line deletions) in the identified test file. No new files, no
signature changes, no fixture restructuring.

### Details

- Fixture site (current):
  ```python
  return EmbeddingClientConfig(
      embed_url="http://localhost:8080/embed",
      circuit_open_after=3,
      circuit_reset_sec=60.0,
      embed_dim=0,
  )
  ```
  becomes (after deletion) a 3-argument call with `embed_url`, `circuit_open_after`,
  `circuit_reset_sec` only.
- Inline site (current, inside `test_auto_reset_when_elapsed`):
  ```python
  cfg = EmbeddingClientConfig(
      embed_url="http://localhost:8080/embed",
      circuit_open_after=3,
      circuit_reset_sec=0.001,
      embed_dim=0,
  )
  ```
  becomes the same 3-argument call shape with `circuit_reset_sec=0.001` preserved.
- `EmbeddingClientConfig` itself (`scripts/agent/memory/embedding_client.py:31-39`) is not touched.

## Compatibility considerations

- Test-only change; no public/production API, schema, or wire-format is touched.
- `EmbeddingClientConfig`'s current six-field contract is unaffected — this change makes the test
  conform to the existing contract rather than changing the contract.

## Security considerations

N/A — test-file-only edit, no secrets, network calls, or trust-boundary code involved.

## Rollback considerations

- Trivial `git revert` of the single commit reintroduces the two `embed_dim=0,` lines and the
  original `TypeError` failures; no other file depends on this change.

## Validation plan

- `rg -n "embed_dim" tests/agent/commands/test_memory_status.py` → 0 matches.
- `PYTHONPATH=scripts pytest tests/agent/commands/test_memory_status.py -v` → 17 passed, 0 errors,
  0 failures (baseline: 1 failed / 5 passed / 11 errors).
- `git diff --stat -- scripts/agent/memory/embedding_client.py` → empty (no production change).
- `git diff -- tests/agent/commands/test_memory_status.py` → exactly 2 removed lines, 0 added
  lines, no other lines touched.
- `PYTHONPATH=scripts pytest tests/agent/commands/ --collect-only -q` → no new collection errors.
- `ruff check tests/agent/commands/test_memory_status.py` → 0 errors.

## Out of scope

- Fixing the stale doc reference at
  `docs/05_agent_12_05_memory-module-ref-extraction-and-facade.md:67` (this workflow phase cannot
  edit `docs/*.md`; a separate issue is expected to track it per the source plan).
- Any change to `scripts/agent/memory/embedding_client.py`.
- Any other `embed_dim` usage tied to `MemoryStore` / `AgentConfig.memory.memory_embed_dim`
  (unrelated, still-valid concept).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: /home/sugimoto/llmagent/plans/20260804-110548_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-112956
- Related target files: test_memory_status.py
