## Goal

Add `/memory list` numeric-limit cases to `tests/agent/commands/test_memory_data_ops.py`:
`["201"]` and `["0"]` rejected, `["5"]` applied, `["+5"]` accepted after the grammar change, and
`'٣'` accepted (parses to its value) — proving the shared-parser grammar and the unchanged 1..200
bound (REQ-006; AC-5).

## Scope

In scope: `tests/agent/commands/test_memory_data_ops.py`. Out of scope: implementing
`_parse_list_options` (`scripts/agent/commands/memory_data_ops.py`, its own row).

## Assumptions

- No existing test passes a numeric limit today: calls at `:59`, `:73`, `:84`, `:285`, `:299` all
  pass `[]` or `["--pinned"]` (verified by grep). So the new cases are purely additive and cannot
  break an existing assertion.
- The grammar reality (corrected during Step 3a): `int('٣')` == 3, so `'٣'` is accepted and parses
  to its value under the shared `int()`-based parser — not rejected.

## Design decisions

- Add a small set of cases to the characterization harness for `memory_list`, one per token:
  `["201"]` and `["0"]` expected to render a validation error (no listing), `["5"]` expected to
  apply limit 5, `["+5"]` expected to apply limit 5, and `['٣']` expected to apply its parsed value.
  Match the existing call style (`ops.memory_list(mem, [...])`) already used at `:59`/`:73`/`:84`.

## Alternatives considered

- Reusing the existing empty-arg characterization cases: rejected — they never exercise a numeric
  limit, so they cannot prove the bound or the grammar change.

## Implementation

### Target file

`tests/agent/commands/test_memory_data_ops.py`

### Procedure

Add numeric-limit cases to the `memory_list` characterization harness, matching the existing call
style (`ops.memory_list(mem, [...])` at `:59`/`:73`/`:84`):

- `["201"]` → validation error, no listing
- `["0"]` → validation error, no listing
- `["5"]` → limit applied as 5
- `["+5"]` → limit applied as 5 (accepted after the grammar change)
- `['٣']` → limit applied as its parsed value (accepted; `int('٣')` == 3)

### Method

Additive parametrized cases; no existing case passes a numeric limit, so nothing is broken.

### Details

The bound (1..200) and subcommand dispatch (`cmd_memory.py:113`) are unchanged; these cases only
exercise the limit token.

## Compatibility considerations

- Additive only; dispatch via `cmd_memory.py:113` and the subcommand tests (`test_cmd_memory.py`,
  `test_agent_cmd_memory.py`) are unaffected.

## Security considerations

- Locking `0`/`201` as rejected keeps the documented "at most 200" bound enforced.

## Rollback considerations

- Deleting the added cases reverts this row.

## Validation plan

- `uv run pytest tests/agent/commands/test_memory_data_ops.py tests/agent/commands/test_cmd_memory.py
  tests/agent/commands/test_agent_cmd_memory.py -q` — bound preserved; dispatch unchanged
  (AC-5).

## Completion criteria

- Numeric-limit cases cover `["201"]`/`["0"]` (rejected), `["5"]` (applied), `["+5"]` (accepted),
  and `'٣'` (accepted); the 1..200 bound is unchanged (AC-5).

## Out of Scope

Implementing `_parse_list_options` (`memory_data_ops.py`) and the other test rows — each is its
own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add numeric-limit cases to `test_memory_data_ops.py`: `["201"]`/`["0"]` rejected, `["5"]` applied, `["+5"]` accepted, `'٣'` accepted | Pending | — | — | REQ-006, AC-5, AC-6 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |
| 4 | — | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains (UNK-01's bounds are two call-site constants) | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `tests/agent/commands/test_memory_data_ops.py`
