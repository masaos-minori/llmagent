## Goal

Make this module assert the contract values as the generator emits them, so the pinned bounds test the model-derived schema instead of a hand-written block (`REQ-001`, `AC-1`, `AC-2`).

## Scope
**Release unit**: N/A: not part of a release unit

- One helper resolves the validation branch of an optional property.
- The seven bound/enum/items assertions (lines 34-104) read through that helper; the expected values do not change.
- The config cross-check (lines 100-121) keeps comparing the five TOML-backed maxima with `config/mdq_mcp_server.toml`.

## Assumptions

- Verified at current HEAD: a constrained optional field renders as `anyOf` with the constrained branch first and a `{"type": "null"}` branch; a required list field keeps `minItems` directly. So `props["limit"]["maximum"]` no longer resolves and the assertion needs the branch.
- `build_input_schema()` removes generated `title` keys (`scripts/mcp_servers/request_contract.py:44-50`), so no assertion may depend on `title`.
- Expected values are unchanged by row 01: (1,100), (1,100000), (1,10000), (1,500), (1,200), (1,500), `enum: ["bm25"]`, `minItems: 1`, and no maximum for `context_before`/`context_after`.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area (`tools/check_test_taxonomy.py::CLASSIFIED_AREAS`), and the module carries no marker, so no finding arises.

## Design decisions

- Keep the literal expected values. Deriving them from the model would make each assertion tautological; the literals are the advertised contract this module exists to pin.
- Resolve the branch through one helper rather than rewriting each assertion into an `anyOf` traversal.

## Alternatives considered

- `N/A: no representation decision is made here; the generator's output shape is consumed as it is.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_tool_schema.py`

### Procedure
1. Add `_constraint_branch(prop)`: return `prop` when it has no `anyOf`, otherwise the first branch that is not `{"type": "null"}`.
2. Route every `minimum`, `maximum`, `items`, `minItems`, and `enum` read in the assertions through it.
3. Keep the five config cross-checks comparing the resolved maxima with `cfg.get(...)`; the fallback defaults in the `.get()` calls stay as they are.

### Method

- `_tool_schema()` keeps looking up the entry in `TOOL_LIST`; after row 02 that value is the generator output, so the absence of `title` in the returned dict is the evidence the contract has one source.

### Details

- The assertion that `context_before` has no `maximum` applies to the resolved branch, not to the property node.
- The module docstring stays: its config-drift paragraph describes which keys are TOML-backed, which is unchanged.

## Compatibility considerations

- `N/A: test-only change; no other module reads this file.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_schema.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Every bound, enum, and `minItems` assertion passes against the generated schema with the same expected values (`AC-2`).
- The five advertised maxima still equal the TOML config values (`AC-2`).

## Out of Scope

- The guardrail comparing an entry's schema with `build_input_schema()` (row 07).
- The model field constraints themselves (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 (test assertion update) |
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
- **Requirement ID**: REQ-001, AC-1, AC-2
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_tool_schema.py`
