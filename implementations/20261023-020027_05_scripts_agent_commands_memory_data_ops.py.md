## Goal

Make `/memory list [n]` validate its positional limit token through the shared numeric parser
(`parse_int_arg`) so the grammar matches every other command: the 1..200 bound is preserved,
`'+5'` is accepted, and `0`/`201`/non-integers produce a usage error — while `--max-sessions`
semantics and subcommand dispatch stay unchanged (REQ-006; AC-5, AC-6).

## Scope

In scope: `_parse_list_options` in `scripts/agent/commands/memory_data_ops.py` (`:64-125`, the
limit branch at `:85-91`) and the numeric-limit cases in
`tests/agent/commands/test_memory_data_ops.py`. Out of scope: subcommand dispatch in
`scripts/agent/commands/cmd_memory.py` (`:113`), `_parse_prune_days` (`:128-149`), and the other
three command rows.

## Assumptions

- The upper bound `200` is the intended reference bound (A3); UNK-01 records the alternative.
- **Grammar reality (corrected during Step 3a)**: `int()` accepts non-ASCII decimal digits —
  `int('٣')` == 3 and `int('１')` == 1 (verified empirically). So aligning `isdigit()` with
  `int()` does NOT reject `'٣'`/`'１'`; it only widens to accept `'+5'`/`'1_0'`. The Plan's
  original "'٣'/'１' rejected" wording was factually wrong and has been corrected in the Plan
  (REQ-006, A1, AC-5, row 09, Risks). Non-ASCII decimal digits therefore remain accepted, exactly
  as under `isdigit()`.
- The call site `memory_list` (`memory_data_ops.py:188-192`) already does
  `options = _parse_list_options(self, args); if options is None: return`, so the rejection path
  must still return `None` after rendering the usage error.

## Design decisions

- Replace the `tok.isdigit()` branch (`:85-91`) with a bare-positional check plus a
  `parse_int_arg` call:
  ```python
  if not tok.startswith("--"):
      try:
          limit = parse_int_arg(
              tok, usage="/memory list [n]", default=20, minimum=1, maximum=200
          )
      except CommandValidationError:
          self._out.write_validation_error("/memory list [n]")
          return None
      i += 1
      continue
  ```
  The guard MUST change from `tok.isdigit()` to `not tok.startswith("--")`; otherwise `'+5'`
  (which `isdigit()` rejects) never reaches `parse_int_arg` and would fall through to the
  trailing bare-token validation error — contradicting REQ-006. The rest of the option parsing
  (`--query`/`--type`/`--pinned`/trailing error) is unchanged.
- Import `CommandValidationError` into `memory_data_ops.py`. `parse_int_arg` stays free of
  output/rendering (A5); the call site renders.

## Alternatives considered

- Keeping `if tok.isdigit():` and only swapping the body: rejected — `'+5'` would never enter the
  branch, so it could not become accepted (REQ-006).
- Bounds as `ArgSpec` fields: rejected by the Plan (UNK-03); bounds are call-site constants.

## Implementation

### Target file

`scripts/agent/commands/memory_data_ops.py`

### Procedure

In `_parse_list_options` (`:64-125`), change the limit branch guard from `tok.isdigit()` to a
bare-positional check and replace the body with a `parse_int_arg` call:

```python
if not tok.startswith("--"):
    try:
        limit = parse_int_arg(
            tok, usage="/memory list [n]", default=20, minimum=1, maximum=200
        )
    except CommandValidationError:
        self._out.write_validation_error("/memory list [n]")
        return None
    i += 1
    continue
```

Import `CommandValidationError`.

### Method

The guard MUST change from `tok.isdigit()` to `not tok.startswith("--")`; otherwise `'+5'` (which
`isdigit()` rejects) never reaches `parse_int_arg` and would fall through to the trailing bare-token
validation error, contradicting REQ-006. The rest of the option parsing (`:79-119`) is unchanged.

### Details

Grammar is now `int()`-based: `'+5'`/`'1_0'` are accepted, and `'٣'`/`'１'` remain accepted because
`int()` accepts non-ASCII decimal digits (verified). Any other bare token still hits the trailing
validation-error branch. The call site (`memory_list`, `:190-192`) already returns on `None`, so
rendering-then-returning-None preserves it.

## Compatibility considerations

- No existing test passes a numeric limit today (`test_memory_data_ops.py` calls at `:59`, `:73`,
  `:84`, `:285`, `:299` all pass `[]` or `["--pinned"]`), so no existing case breaks. Dispatch
  via `cmd_memory.py:113` is unchanged. `test_cmd_memory.py` and `test_agent_cmd_memory.py`
  regression runs stay green.

## Security considerations

- Rejecting `0`/`201` keeps the documented "at most 200" bound enforced at the command layer
  (`agent_07_10:39`). This is a correctness guard, not an authentication boundary.

## Rollback considerations

- The change is a single-branch swap; revert `memory_data_ops.py` to `HEAD` for this row's commit
  if needed, then re-run the suite.

## Validation plan

- `uv run pytest tests/agent/commands/test_memory_data_ops.py
  tests/agent/commands/test_cmd_memory.py tests/agent/commands/test_agent_cmd_memory.py -q` —
  bound preserved; dispatch unchanged; new numeric-limit cases pass (AC-5).
- `uv run ruff format scripts/agent` + `uv run ruff check scripts/agent`;
  `uv run mypy --no-namespace-packages scripts/agent`.

## Completion criteria

- `_parse_list_options` validates the limit token through
  `parse_int_arg(usage="/memory list [n]", default=20, minimum=1, maximum=200)`; `["201"]` and
  `["0"]` are rejected, `["5"]` is applied, `["+5"]` is accepted, and any other bare token stays a
  validation error (AC-5).
- The 1..200 bound is unchanged; subcommand dispatch is unchanged (REQ-006).

## Out of Scope

Every other command that adopts `parse_int_arg` (`cmd_context.py`, `cmd_session.py`,
`db_session_ops.py`) and their test rows — each is its own row. `_parse_prune_days` and
`cmd_memory.py` dispatch are unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `tok.isdigit()` branch in `_parse_list_options` with a bare-positional check + `parse_int_arg(usage="/memory list [n]", default=20, minimum=1, maximum=200)` wrapped in try/except; render usage error and return None on rejection | Pending | — | — | REQ-006, REQ-007, REQ-009, AC-5, AC-6 |
| 2 | Add numeric-limit cases to `tests/agent/commands/test_memory_data_ops.py`: `["201"]`/`["0"]` rejected, `["5"]` applied, `["+5"]` accepted; keep dispatch unchanged | Pending | — | — | REQ-006, AC-5, AC-6 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `scripts/agent/commands/memory_data_ops.py`
