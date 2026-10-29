# Implementation Procedure: tests/eventbus/test_eventbus_replay_subscribe.py

<!-- Generated from plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md row: tests/eventbus/test_eventbus_replay_subscribe.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Rename `test_subscribe_yields_matching_event` to a query/row-conversion name so the test name
matches what it actually executes — a direct SQL query plus `_row_to_dict()` — with no
assertion or behavior change (`REQ-004`; AC-3).

## Scope

`tests/eventbus/test_eventbus_replay_subscribe.py` only: one test function rename. Fixtures,
`_event()`, the other two tests, imports, and every assertion stay unchanged.

## Assumptions

- Source claims re-verified this cycle: `client` fixture (`:13-34`), `_event` (`:37`),
  `test_replay_returns_events_since_seq` (`:47`), `test_replay_since_seq_filters` (`:64`),
  `test_subscribe_yields_matching_event` (`@pytest.mark.anyio` `:81`, def `:82`, docstring
  `:83-88` states `/replay` already validates SSE framing and the same `_row_to_dict` is
  reused; direct SQL at `:94-99`; `_row_to_dict` imported at `:100`).
- No test references `test_subscribe_yields_matching_event` by name outside its own def
  (verified with `grep -rn` over `tests/`, only the def site and `.pyc` caches match).
- The Plan's row 03 leaves the new name as "a query/row-conversion name"; this procedure
  fixes it to `test_subscribe_query_row_conversion_yields_matching_event` (new) because it
  names both executed parts (SQL query, `_row_to_dict` conversion) without claiming live
  subscribe/SSE behavior.

## Design decisions

- Rename-only change (Plan row 03 Test column: "Same assertions, names changed only"); the
  docstring and `@pytest.mark.anyio` marker stay as-is even though the body is synchronous —
  removing the marker would change test execution, which is out of this row's scope.

## Alternatives considered

- Also dropping the stale `@pytest.mark.anyio`: rejected, out of scope for a rename-only row.

## Implementation

### Target file

`tests/eventbus/test_eventbus_replay_subscribe.py`

### Procedure

1. Open `tests/eventbus/test_eventbus_replay_subscribe.py` and locate
   `async def test_subscribe_yields_matching_event` (`:82`).
2. Rename the function to `test_subscribe_query_row_conversion_yields_matching_event` (new);
   keep the decorator, docstring, body, and assertions byte-identical.
3. Run `rg -n "test_subscribe_yields_matching_event" tests/` and confirm zero source matches
   remain (`.pyc` caches are ignored).

### Method

Single-line def-line edit; no other occurrence of the old name exists in the repository.

### Details

- The new name is a rename target, not a new test; the stale detector treats it via the
  `(new)` template marker.

## Compatibility considerations

- `pytest --collect-only` test-id diff is the only externally visible change.

## Security considerations

- None.

## Rollback considerations

- Rename back; no other file references the name.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py -q` (3 tests pass).
- `uv run pytest --collect-only tests/eventbus/test_eventbus_replay_subscribe.py` diff shows
  exactly one renamed test id (`REQ-004`; AC-3).
- `uv run ruff check tests/eventbus/test_eventbus_replay_subscribe.py`.

## Completion criteria

- Old name has zero source occurrences; the renamed test passes with identical assertions.

## Out of Scope

- Marker/docstring changes and any behavior edits in this file.
- Fixture and scenario tests (procedures `20261029-111247_01/02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Renamed test function |
| 2 | Add or update tests per Validation plan | Done | — | — | All 3 tests green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261028-122337_ebresumetest004_subscribe-restart-integration-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-111247
- **Related target files**: tests/eventbus/eventbus_helpers.py, tests/eventbus/test_eventbus_restart_resume.py
