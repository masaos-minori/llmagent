## Goal

Add a construction-time regression test proving that `CommandRegistry(...)` raises
`TypeError` when a `CommandDef.is_async` disagrees with its handler's kind, and keep the
existing whole-registry scans so they continue to prove today's 14 entries are consistent.
This locks in the production fix made in row 02 (`registry.py`).

## Scope

Modify `tests/agent/commands/test_command_registry_consistency.py` only. Adds one test
function and keeps the two existing scan-based tests. No other file modified.

## Assumptions

- The module imports `_COMMANDS` from `agent.commands.registry` (`registry.py:39`), so a
  test can monkeypatch `agent.commands.registry._COMMANDS` with one flipped entry.
- The existing `registry` fixture (`test_command_registry_consistency.py:15-23`) already
  builds a real `CommandRegistry` with a `MagicMock` ctx and a `SimpleNamespace`, so a
  mismatched entry can be injected and reconstructed.
- The two existing scans (`test_async_handlers_are_coroutines`,
  `test_sync_handlers_are_not_coroutines`, `:35-49`) stay as the guard that no current
  entry mismatches (AC-2).

## Design decisions

- **One focused test via monkeypatch.** `test_is_async_handler_mismatch_raises_at_construction`
  injects a single flipped entry into `agent.commands.registry._COMMANDS` and asserts
  `pytest.raises(TypeError)`. This isolates the new contract without touching the 14 valid
  entries (AC-1).
- **Keep the scans unchanged.** They assert today's metadata is consistent (AC-2) and are
  preserved, not deleted (A5).
- **Assert the message names all three required pieces** (command, handler, kind) so the
  test also guards the attribution contract in REQ-001.

## Alternatives considered

- **Construct a bare `CommandDef` with a bad `is_async` and register it live.** Rejected:
  the registry reads the module-level `_COMMANDS`; monkeypatching that is the mechanism the
  plan specifies and matches how production enumerates entries.
- **Patch `inspect.iscoroutinefunction`.** Rejected: that tests the wrong seam; the
  contract is about the registry's construction check, exercised by feeding it a real
  mismatched entry.

## Implementation
### Target file
`tests/agent/commands/test_command_registry_consistency.py` (Modify)

### Procedure
1. Open `tests/agent/commands/test_command_registry_consistency.py` and read the existing
   `registry` fixture (`:15-23`) and the two scans (`:35-49`) to match the module's
   conventions (imports, fixture usage, `CommandDef` construction).
2. Add `test_is_async_handler_mismatch_raises_at_construction`:
   - Monkeypatch `agent.commands.registry._COMMANDS` with a list equal to the real one but
     with one entry's `is_async` flipped (e.g. an async handler set to `is_async=False`).
   - Assert `with pytest.raises(TypeError): commands.registry.CommandRegistry(ctx)`.
   - Optionally capture the exception message and assert it contains the command name,
     handler name, and a kind token.
3. Leave `test_async_handlers_are_coroutines` and `test_sync_handlers_are_not_coroutines`
   untouched.
4. Do not modify any production file (row 02 owns `registry.py`).

### Method
- `pytest` + `monkeypatch` fixture. Rebuild/reconstruct the registry inside the
  `pytest.raises` block so the mismatch fails at construction (AC-1).
- Derive the flipped entry from the real `_COMMANDS` (copy one entry and set
  `is_async` to the opposite boolean) so the test stays valid as the list grows.
- Keep the assertion on the exception *type* primary; the message-name check is a
  secondary guard.

### Details
- The flipped entry must reference a handler that actually exists on the registry instance
  (so the `hasattr`/`_get_handler` lookup succeeds and the kind check is reached); reuse a
  real entry and only flip its `is_async` flag rather than inventing a fake handler.
- `CommandDef` is a dataclass (`command_defs.py:65`); construct the flipped entry with the
  same constructor the existing fixture uses — do not introduce a different builder.
- Because the 14 real entries already satisfy the invariant, running the full
  `test_command_registry_consistency.py` suite after this change must be green (AC-2).

## Compatibility considerations

Test-only change. Does not alter `registry.py` behavior; the new construction check is
provided by row 02. Existing scans and other command tests are unaffected.

## Security considerations

No security impact: pure unit test, no network/shell/secrets.

## Rollback considerations

Revert the single added test function in `tests/agent/commands/test_command_registry_consistency.py`.
No other file touched.

## Validation plan

1. `uv run pytest tests/agent/commands/test_command_registry_consistency.py -v` passes with
   the new test plus the unchanged scans.
2. Temporarily drop the production check (row 02) or flip the assertion to expect success
   and confirm the new test fails — restore afterward.
3. Broader suite: `uv run pytest tests/agent/commands/test_command_registry_consistency.py
   tests/agent/commands/test_command_registry_dispatch.py
   tests/agent/commands/test_command_def_sync.py -v` (AC-2).

## Completion criteria

- `test_is_async_handler_mismatch_raises_at_construction` exists and raises `TypeError`
  naming the command, handler, and kind (AC-1).
- Existing scans still pass unchanged (AC-2).
- Full command-test suite green.

## Out of Scope

- The production check itself (row 02, `registry.py`).
- Any other test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-020701_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: tests/agent/commands/test_command_registry_consistency.py
