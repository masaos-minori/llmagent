## Goal

Add table-driven tests for the shared numeric parser `parse_int_arg` itself, proving the absent →
default, absent-without-default → `None`, valid-bounds, and invalid/out-of-range behavior required
by REQ-001 and AC-1. This is a new file: `tests/agent/commands/test_command_arg_parsing.py`.

## Scope

In scope: the new test module `tests/agent/commands/test_command_arg_parsing.py`. Out of scope:
implementing `parse_int_arg` (that is `scripts/agent/commands/utils.py`, its own row) and the
call-site adoption tests.

## Assumptions

- No test module for `scripts/agent/commands/utils.py` exists today: `find tests -name "*utils*"`
  matches only `tests/shared/*`, `tests/rag/*`, `tests/agent/services/test_commands_utils.py`
  (which tests `agent.services.export_formatter`), and `tests/eventbus/*`; and
  `grep -rln "parse_command_args" tests` returns nothing. So this is genuinely a new file.
- `parse_int_arg` raises `CommandValidationError` (a `ValueError` subclass) for invalid input and
  carries the `usage` string on it, so tests assert both the raised value and that `str(exc)`
  contains the usage string.

## Design decisions

- Table-driven: one parametrized case per `(raw, kwargs, expected)` tuple covering absent (`None`),
  absent without default (`None`, `default=None`), valid within bounds, `0`, negative, above
  `maximum`, bare flag (`True`), `'+5'`, `'1_0'`, `' 5 '` (accepted), and `'٣'`/`'１'` (accepted,
  since `int()` accepts non-ASCII decimal digits — verified). Invalid cases assert the raised
  `CommandValidationError` carries the `usage` string.
- The test module lives next to the other command tests under `tests/agent/commands/` so it can
  import `parse_int_arg` from `agent.commands.utils`.

## Alternatives considered

- One assertion per case instead of a table: rejected — a table makes the accepted/rejected token
  set and the `minimum`/`maximum`/`default` combinations explicit and self-documenting (AC-1).

## Implementation

### Target file

`tests/agent/commands/test_command_arg_parsing.py` (new)

### Procedure

Create the module and add a parametrized table over `(raw, kwargs, expected)`:

- absent (`None`) → `default`
- absent without default (`None`, `default=None`) → `None`
- valid within bounds → the value
- `0`, negative, above `maximum` → raises `CommandValidationError`
- bare flag (`True`) → raises
- `'+5'`, `'1_0'`, `' 5 '` → accepted (parsed value)
- `'٣'`/`'１'` → accepted (parse to their values; `int()` accepts non-ASCII decimal digits)
- a `CommandValidationError` asserts `str(exc)` carries the `usage` string

```python
import pytest
from agent.commands.utils import parse_int_arg
from agent.commands.exceptions import CommandValidationError


@pytest.mark.parametrize("raw,kwargs,expected", [
    (None, {"usage": "x", "default": 5}, 5),
    (None, {"usage": "x"}, None),
    ("5", {"usage": "x", "minimum": 1, "maximum": 200}, 5),
    ("+5", {"usage": "x"}, 5),
    ("0", {"usage": "x", "minimum": 1}, pytest.raises(CommandValidationError)),
    ...
])
```

### Method

Table-driven; import `parse_int_arg` from `agent.commands.utils` and `CommandValidationError` from
`agent.commands.exceptions`. The module fails until `utils.py` defines `parse_int_arg`
(Implementation step 2), then passes.

### Details

Place the file under `tests/agent/commands/` next to the other command tests. No existing test
module covers `utils.py`, so this is a genuinely new file.

## Compatibility considerations

- The file is new and additive; it does not touch any existing test. It fails until
  `scripts/agent/commands/utils.py` defines `parse_int_arg` (Implementation step 1 shows the
  failure), then passes once it does.

## Security considerations

- Covering the bare-flag (`True`) and `'+5'`/`'1_0'` cases locks the exact contract the other rows
  depend on, so a later refactor cannot silently reintroduce absent/invalid conflation.

## Rollback considerations

- Deleting the new file reverts this row; it has no effect on other tests.

## Validation plan

- `uv run pytest tests/agent/commands/test_command_arg_parsing.py -v` — all cases pass; `None`
  returned only for an absent argument (AC-1).
- `uv run pytest tests/agent/commands -q` — no collision with existing command tests.

## Completion criteria

- Every accepted/rejected token case and every `minimum`/`maximum`/`default` combination is
  covered, asserting the returned value or the `CommandValidationError` carrying the `usage`
  string (AC-1).

## Out of Scope

Implementing `parse_int_arg` (`scripts/agent/commands/utils.py`) and the four call-site adoption
rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/agent/commands/test_command_arg_parsing.py` and show it fails against the current `scripts/agent/commands/utils.py` (no `parse_int_arg`) | Completed | 2026-10-23 | 2026-10-23 | REQ-001, AC-1 |
| 2 | Fill the table-driven cases over the accepted/rejected token set and `minimum`/`maximum`/`default` combinations; run to green | Completed | 2026-10-23 | 2026-10-23 | REQ-001, AC-1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-23 | 2026-10-23 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `tests/agent/commands/test_command_arg_parsing.py` (new)
