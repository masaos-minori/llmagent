# Implementation Procedure: tests/eventbus/test_eventbus_requeue_edge_cases.py

<!-- Generated from plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md row: tests/eventbus/test_eventbus_requeue_edge_cases.py -->
<!-- Preserve this header comment; it links the procedure back to the Plan target file table row. -->

## Goal

Rename the two misspelled `dmq` test methods to `dlq` spellings, leaving no `dmq` substring in
`tests/eventbus/` (`REQ-002`; AC-2).

## Scope

`tests/eventbus/test_eventbus_requeue_edge_cases.py` only: two `def` name changes. No body,
assertion, comment, fixture, or import change; no other file.

## Assumptions

- Source claims re-verified this cycle (2026-10-29, HEAD `a00f4517c`): the only `dmq` occurrences
  in `tests/`, `scripts/`, and `docs/` are the method definitions
  `test_requeue_non_dmq_event` (`:76`) and `test_requeue_valid_dmq_event` (`:88`); neither name is
  referenced anywhere else in `.py` files (grep 2026-10-29), and no doc references either name.
- Sequencing predecessor: `implementations/20261029-102038_05_tests_eventbus_test_eventbus_requeue_edge_cases.py.md`
  (eventbus004, comment/docstring cleanup of the same file) lands first; that document explicitly
  forbids test renames, so this procedure owns them. Its edits change comment lines only, so the
  method-definition anchors shift but not their content.
- Line numbers shift once the predecessor lands; anchor on the two method-name literals, not the
  line numbers.

## Design decisions

- `test_requeue_non_dmq_event` -> `test_requeue_non_dlq_event` (new) and `test_requeue_valid_dmq_event`
  -> `test_requeue_valid_dlq_event` (new): minimal spelling fix preserving each name's existing meaning
  (the docstrings already say "non-DLQ event" and "valid DLQ event", so the new names match the
  documented behavior exactly).
- Method renames only: pytest collects by name, nothing parametrizes or references these names
  (verified above), so a rename is behavior-neutral.

## Alternatives considered

- Rewording to a role-prefixed name per a naming prefix contract: rejected; the Plan deleted the
  fabricated prefix-mapping requirement, and the file's local style is `test_requeue_*` already.

## Implementation
### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

1. Rename `def test_requeue_non_dmq_event(...)` to `def test_requeue_non_dlq_event(...)`.
2. Rename `def test_requeue_valid_dmq_event(...)` to `def test_requeue_valid_dlq_event(...)`.
3. Change nothing else; parameter lists, decorators, and docstrings stay byte-identical.

### Method

Direct edit of two `def` lines.

### Details

- After the edit, `grep -rn "dmq" tests/eventbus/` must return nothing.
- The `client: TestClient` / `tmp_path: Path` parameters stay as they are (fixture injection by
  name).

## Compatibility considerations

Collection count is unchanged (2 before, 2 after); only the reported test ids change. The only
other repo-wide occurrences of the old names are the git-ignored `.pytest_cache` nodeid cache and
archived historical documents under `implementations/done/` and `plans/done/` (grep 2026-10-29);
neither consumes the names at runtime.

## Security considerations

N/A: name-only test change.

## Rollback considerations

Reverting the commit restores the old names; no other change depends on either spelling.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -v` (same pass count; the two
   renamed tests appear under `dlq` names).
2. Grep gate (AC-2): `grep -rn "dmq" tests/eventbus/` -> empty.
3. `uv run pytest tests/eventbus` (baseline 411 passed / 1 skipped before the ebresumetest004
   procedures land).
4. `uv run ruff check tests/eventbus/test_eventbus_requeue_edge_cases.py`; `uv run ruff format
   --check`; `uv run mypy --no-namespace-packages tests/eventbus/test_eventbus_requeue_edge_cases.py`.

## Completion criteria

- The two methods carry the `dlq` spellings; `grep -rn "dmq" tests/eventbus/` is empty.
- The file passes with the same count and unchanged assertions.
- ruff, format check, and mypy are clean on the file.

## Out of Scope

- The `REQ-*` comment/docstring cleanup of this file (eventbus004 procedure `102038_05`).
- Any other test name in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the two `dmq` methods to `dlq` spellings (Implementation > Procedure/Method/Details) | Pending | — | — | After `102038_05` lands |
| 2 | Run the grep gate (Validation plan 2) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-130401
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py
