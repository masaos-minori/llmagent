# Implementation Procedure: tests/shared/test_mcp_dedup.py

## Goal

Regression coverage for the new durable dedup store (row 02): state machine, reopen
durability, TTL purge, interrupted classification, and config validation of
`config/mcp_dedup.toml` (REQ-002, REQ-005, REQ-009), test-first for row 02.

## Scope

**In scope:**
- `tests/shared/test_mcp_dedup.py`: new file, full store-contract suite.

**Out of scope:**
- Store implementation (row 02); dispatcher integration (row 19).

## Assumptions

- New file: `tests/shared/test_mcp_dedup.py` does not exist at HEAD (verified `ls
  tests/shared/`); the plan's row 17 "New" designation is confirmed.
- Expected red state: every test here is red until row 02 lands (test-first
  ordering — same pattern as row 15 doc).
- tmp_path-isolated sqlite files only; never touch `/opt/llm/db/mcp_dedup.sqlite` in
  tests.

## Design decisions

- State machine: `pending` → `completed` / `failed` / `interrupted`; assert
  transitions, illegal transitions rejected, and `retry_class` (new) lookup
  (`retryable`/`non_retryable` (new), unknown tool → `non_retryable` (new)) recorded per row 02.
- Reopen durability: write rows, close store, reopen same path — completed rows
  replay identical result (REQ-002 "survives restart").
- Cross-process sharing: two `McpDedupStore` (new) instances on the same file (two
  connections) — second sees first's completed row; concurrent same-key
  check-and-insert yields exactly one `pending` winner.
- TTL purge: `retention_days` expiry boundary tested at exactly N days (row 10 config
  value); expired rows removed, unexpired kept.
- Interrupted classification: a store left holding `pending` past
  `pending_timeout_minutes` (new) is classified interrupted per row 02 semantics (drives
  REQ-007/REQ-008 lifecycle downstream, tested here at store level).
- Config validation cases (plan row 10 "config-validation cases"): missing file →
  shipped defaults; wrong types (string timeout, negative retention) → failure in
  the existing `config_errors.py` class family (`ConfigMissingError`,
  `ConfigParseError`, `ConfigLoadError` — verified at
  `scripts/shared/config_errors.py:5-42`), following the conventions of sibling
  store tests.

## Alternatives considered

- Testing the store through `dispatch_tool` only — rejected: row 19 covers the
  integration surface; store invariants need direct, fast unit coverage including
  reopen and concurrency.

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py` (new)

### Procedure
1. Create the file with fixtures: tmp sqlite path, config dict builder (defaults +
   overrides), store factory.
2. Add test classes: `TestStateMachine` (new), `TestReopenDurability` (new),
   `TestCrossProcessSharing` (new), `TestTtlPurge` (new), `TestInterruptedClassification` (new),
   `TestConfigValidation` (new).

### Method
Test-first: red until row 02 (and row 10 for config cases) land.

### Details
- Key literals are synthetic; do not import agent modules (shared-layer test only,
  import-contract safe).

## Compatibility considerations

- None for existing suites (new file). `tests/shared` mypy config applies.

## Security considerations

- Content-hash collisions are out of scope; no real payloads in fixtures.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py` (red before rows 02/10, green
  after); `uv run mypy --no-namespace-packages tests/shared`;
  `uv run lint-imports` (new test imports only `shared.*`).

## Completion criteria

- All six test classes pass with rows 02/10 landed; store contract (states,
  durability, TTL, interrupted classification, config validation) fully covered.

## Out of Scope

- Dispatcher replay policy (row 19); workflow lifecycle tables (rows 06-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create test file + six test classes | Pending | — | — | Red until rows 02/10 land |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (durable store), `REQ-005` (replay decision inputs),
  `REQ-009` (retention/config)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/shared/test_mcp_dedup.py (new)
