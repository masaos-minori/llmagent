## Goal

Compare the two validation paths for the MDQ tools, so a divergence between the advertised schema and the enforced model cannot survive (`REQ-001`, `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

- New module, contract-classified (`pytestmark = pytest.mark.contract`, `REQ-001` citation in the docstring).
- One case table covering unknown fields, empty values, wrong-type inputs, and boundary values for the 7 request models.
- Phase 1 form pins the current divergence; the Phase 2 form asserts decision equality on every case.

## Assumptions

- `validate_tool_arguments()` checks required fields, extra fields (unless `allow_extra_fields=True`), then jsonschema types (`scripts/agent/tool_arg_validator.py:53-66`); the test calls it with the default, so unknown fields are rejected on the Agent side.
- Verified at current HEAD: `SearchDocsRequest.model_validate({"limit": "5"})` coerces the string to `int`, while jsonschema rejects the same argument. The divergence closes only when each MDQ model declares `strict=True` (row 01), so the wrong-type case is the case that pins `AC-1`.
- No `minLength` constraint exists in the current schema blocks (`mdq_tools.py` carries `minimum` and `minItems` only), so an empty `query` is accepted by both paths and stays an equality case, not a rejection case.
- `minItems` on `paths` maps to pydantic `min_length=1` on `list[str]`, so both paths reject an empty list.
- No service, database, or server fixture is needed: the module compares two pure validation calls, so it stays deterministic and outside the integration markers.

## Design decisions

- Assert decision equality per case rather than a fixed outcome, so a divergence on either side fails the test even when one side is "right".
- Keep the two explicit expected outcomes (unknown field rejected, wrong type rejected) as named cases, because `AC-1` names them and an equality-only test would pass on a both-accept drift.

## Alternatives considered

- Assert only the model side: rejected, that cannot detect the Agent-side divergence, which is the requirement.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_validation_parity.py` (new)

### Procedure
1. Build a case table of `(tool_name, args)` for the four case classes and, for each case, call `validate_tool_arguments(tool, args, build_input_schema(model))` and `model.model_validate(args)`.
2. Assert the two decisions agree for every case.
3. Add the two named outcome cases: `use_summary` on `get_chunk` and an undeclared key on `search_docs` are rejected by both paths.
4. Phase 1: commit the module with the current divergence asserted for the wrong-type case; Phase 2 replaces that pin with the equality assertion.

### Method

- Both paths read the same schema object, `build_input_schema(model)`, so the test measures the contract itself rather than two independently authored definitions.

### Details

- Boundary cases use the values the current blocks publish: `limit` 1 and 100 accepted, 0 and 101 rejected; `context_before` 0 accepted with no maximum.
- `pydantic.ValidationError` and `ValidationResult.success` are normalized to one decision value in the helper, so the equality assertion compares decisions, not exception types.

## Compatibility considerations

- The module is new, so no existing test is affected. `tests/mcp_servers/mdq/` is not a classified area; the marker is checked only for citation and registration (`tools/check_test_taxonomy.py`), and `contract` is registered in `pyproject.toml`.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_validation_parity.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the `rules/toolchain.md` threshold.

## Completion criteria

- Both paths accept and reject the same arguments for unknown, empty, wrong-type, and boundary inputs (`AC-1`).

## Out of Scope

- The strict typing declaration (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).
- The handler path that raises `MdqValidationError` (`scripts/mcp_servers/mdq/mdq_server.py`, row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 (pin) and Phase 2 (parity) |
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
- **Requirement ID**: REQ-001, AC-1
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_validation_parity.py`
