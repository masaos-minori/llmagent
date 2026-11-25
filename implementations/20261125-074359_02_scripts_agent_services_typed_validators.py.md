## Goal

Make `typed_validators` a delegating layer over the shared strict primitives so startup and reload
run one parser instead of two (REQ-001, single shared type rule; REQ-011, field path in the error).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- `scripts/shared/config_field_types.py` (row 1, earlier `seq`) provides the primitives; this module
  imports it and adds nothing that re-implements a type rule.
- `agent` may import `shared`, so the delegation direction is allowed by `shared-is-leaf`.
- `tests/agent/services/test_typed_validators.py` pins the current error text; the message shape is
  preserved by reusing the shared `FieldRule` vocabulary.

## Design decisions
- The `_get_*` functions keep their signatures and return values; only the type check moves behind
  the shared primitive, so existing callers in `config_builders.py` and `config_section_builders.py`
  are untouched.
- The field path is carried as an argument to the primitive and reaches the raised error, which is
  what makes the reload error name the field rather than the value.

## Alternatives considered
- Replacing `typed_validators` with direct calls to the primitives at every call site — rejected:
  the module is the startup-side entry point and its callers are not target rows of this Plan.

## Implementation
### Target file
`scripts/agent/services/typed_validators.py`

### Procedure
Delegate `_get_bool`, `_get_int`, `_get_float`, `_get_str`, `_get_list`, `_get_str_list` (new),
`_get_dict` to the shared primitives and pass the field path through.

### Method
- Each `_get_*` keeps its `required` behavior and raises `ConfigReloadValidationError` with the
  field path and rule name taken from the shared `FieldRule`.
- `_get_list_nonempty`, `_get_str_nonempty`, `_get_dict_nonempty` keep their non-empty behavior by
  passing the `allow_empty=False` flag to the primitive rather than re-checking.

### Details
- `bool` rejection for numeric types must stay: the shared primitive already encodes it, so the
  delegating function must not re-widen the accepted set.
- The `_apply_*` helpers are unchanged; they only call the setter.

## Compatibility considerations
- Blast radius: `typed_validators` is referenced by `config_builders.py` and
  `config_section_builders.py`; behavior changes only for values that were previously coerced, which
  is the intended strictness change.

## Security considerations
- No raw configuration value appears in the raised message.

## Rollback considerations
- Revert the Phase 1 commit; the module holds no state.

## Validation plan
- `uv run pytest tests/agent/services/test_typed_validators.py -q`
- `uv run pytest tests/agent/services/test_config_reload_parity.py -q` (row 27)
- `uv run ruff check scripts tests`, `uv run mypy scripts`, `uv run lint-imports`

## Completion criteria
- No type rule is implemented in this module; every accepted and rejected value matches the shared
  primitive, and the error names the field path.

## Out of Scope
- The `allow_empty` decision per registry entry (row 4).
- Section-builder call-site changes (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 29 |
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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-011 (structured config error); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/typed_validators.py`
