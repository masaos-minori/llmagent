## Goal

Make the MDQ request models the single source of the published input contract (`REQ-001`, purpose: one source for advertised schema and enforced validation), give every read metadata shape a machine-readable consistency state (`REQ-003`), define the `get_chunk` metadata shape (`REQ-004`), and drop `with_neighbors` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- The 7 tool request models change base class and gain field constraints; no behavior is added to this module.
- Read metadata shapes gain `refresh_in_progress` (new) and `index_generation` (new); `GetChunkMetadata` (new) is added.
- `with_neighbors` is removed from `GetChunkRequest` (line 203).

## Assumptions

- The advertised values stay identical to the current hand-written blocks (`AC-2`): maxima 100, 100000, 10000, 500, 200, 6, `enum: ["bm25"]`, `minItems: 1`; the config cross-check in `tests/mcp_servers/mdq/test_mdq_tool_schema.py` (lines 100-121) continues to pass against the generated schema.
- Optional fields render as `anyOf` in the generated schema; the representation changes, the values do not. `tests/mcp_servers/mdq/test_mdq_tool_schema.py` is updated by its own row.
- Strict typing is required for wrong-type parity: verified at current HEAD that `SearchDocsRequest.model_validate({"limit": "5"})` coerces the string to `int`, while `validate_tool_arguments()`'s jsonschema type check rejects the same argument (`scripts/agent/tool_arg_validator.py:62-66`). `StrictRequestModel` sets `extra="forbid"` only, so `strict=True` has to be declared on each MDQ model; the Plan's Risks carry this as the mitigation.
- `index_generation` (new) is a service-level value that does not survive a restart (Plan UNK-05), so the field is nullable and reports the unknown-after-restart case rather than a persisted generation.
- The truncation fields named by `GetChunkMetadata` (new) come from the mdqmcp003 and mdqmcp004 plans' vocabularies; this document consumes them and does not extend them.
- `outline` and `stats` have no metadata shape today, so `OutlineMetadata` (new) and `StatsMetadata` (new) are declared here; the service rows return them.

## Design decisions

- Inherit `StrictRequestModel` (`scripts/mcp_servers/request_contract.py:34`) rather than defining an MDQ-specific strict base: one posture, `extra="forbid"`, the same as the wire models.
- Declare `strict=True` per MDQ model rather than changing `StrictRequestModel`'s config: the shared base is out of this Plan's scope, and the parity requirement (`AC-1`) needs coercion off only for the MDQ models.
- Bounds, the mode enum, and `minItems` are declared as `Field` constraints so `build_input_schema()` (`scripts/mcp_servers/request_contract.py:44`) passes them through unchanged; a hand-written schema block would recreate the drift `REQ-001` closes.
- Consistency state is added to the existing metadata `TypedDict` shapes, not to a new parallel record, because the audit detail builder already consumes metadata as a mapping.

## Alternatives considered

- Keep plain `BaseModel` and add an explicit extra-field check in the handler: rejected, the Agent path already rejects extra fields (`scripts/agent/tool_arg_validator.py`, checks 1-3) and `RuntimeTool.allow_extra_fields` defaults to `False` (`scripts/shared/runtime_tool.py:102`), so the model must carry the posture.
- Add a new `ResourceKeyKind` value or a store-identity contract field for the metadata: rejected, both need the contract owner (Plan UNK-03) and are outside this row.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
1. Change the base of `SearchDocsRequest` (186), `GetChunkRequest` (199), `OutlineRequest` (207), `IndexPathsRequest` (215), `RefreshIndexRequest` (221), `StatsRequest` (228), `GrepDocsRequest` (234) to `StrictRequestModel`, and declare `model_config = ConfigDict(extra="forbid", strict=True)` on each of them so the model makes the same accept/reject decision as the Agent-side jsonschema check.
2. Express each advertised bound as a `Field` constraint on the model field it belongs to.
3. Delete `with_neighbors` from `GetChunkRequest` (line 203).
4. Add `refresh_in_progress: bool` and `index_generation: int | None` to `SearchDocsMetadata` (482), `IndexPathsMetadata` (498), `GrepDocsMetadata` (512), `OutlineMetadata` (new), `StatsMetadata` (new).
5. Add `GetChunkMetadata` (new).

### Method

- This module holds declarations only; the enforcement stays in `scripts/mcp_servers/mdq/mdq_server.py` (whole-mapping validation) and the consistency values are filled by `scripts/mcp_servers/mdq/mdq_service.py`.
- Constraint mapping, so the generated schema publishes the same values the current blocks publish (the current blocks carry `minimum` and `minItems`, verified at `mdq_tools.py:28,56,62,96,126,132,162,191,247,253,259,264`): maxima — `limit` and `max_results_limit` le 100, `max_total_result_chars` le 100000, `max_chars_per_chunk` le 10000, `max_outline_items` le 500, `max_depth` le 6, `max_grep_matches` le 200, `max_chars_per_match` le 500; minima — ge 1 on every bounded numeric field, ge 0 on `context_before` and `context_after`; `min_length=1` on the `list[str]` fields; `Literal["bm25"]` for the search mode.
- `StrictRequestModel` makes unknown fields a validation error, which is what the flipped characterization test asserts (`tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py:81`).

### Details

- `GetChunkMetadata` (new) fields: `chunk_id`, `truncated`, `truncation_char_count` (new), `char_count`, `refresh_in_progress` (new), `index_generation` (new) — the persisted truncation fields come from the mdqmcp004 plan, the read-time cap that was applied is the effective value of `max_chars_per_chunk` after `MdqConfig` bounds.
- `OutlineMetadata` (new) and `StatsMetadata` (new) carry only the consistency fields; existing outline and stats output shapes are unchanged.
- `stale_warning` (line 292) keeps its field and meaning as display text; the state it describes is now also carried by `refresh_in_progress` (new).

## Compatibility considerations

- `tests/mcp_servers/mdq/test_mdq_metadata_consistency.py` reads existing metadata keys and does not assert an exact key set, so the added keys do not break it.
- `tests/mcp_servers/mdq/test_mdq_routing.py:209` compares tool names, not schema content, and is unaffected.
- Handlers that construct models field-by-field must switch to whole-mapping validation (row 03); any caller that passes an undeclared argument starts failing, which is the intended contract change.

## Security considerations

- Rejecting unknown arguments closes the divergence between the Agent path and the direct path; no secret or path fields are added.
- `refresh_in_progress` (new) and `index_generation` (new) expose only internal state counters, already visible through the health endpoint.

## Rollback considerations

- Revert the commit; no persisted state or migration depends on these declarations.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_schema.py tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`
- `uv run ruff check scripts/mcp_servers/mdq/mdq_models.py && uv run mypy scripts/mcp_servers/mdq/mdq_models.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Unknown fields raise a validation error on a model built from the whole argument mapping (`AC-1`).
- A string-encoded number is rejected by the model, so the model and the Agent-side check make the same decision on a wrong-type input (`AC-1`).
- The generated schema publishes the same bounds, enum, and `minItems` values the current blocks publish (`AC-2`).
- `with_neighbors` is absent from the model, the generated schema, and the tool description (`REQ-005`).

## Out of Scope

- The schema generator and the strict base themselves (`scripts/mcp_servers/request_contract.py`): consumed, not redefined.
- The handler validation path (`scripts/mcp_servers/mdq/mdq_server.py`) and the values that fill the consistency fields (`scripts/mcp_servers/mdq/mdq_service.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 and Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in rows 06, 08, 09, 13 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Row 14 states the contract in the mdq doc |

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
- **Requirement ID**: REQ-001 (request models as the single source of the contract), REQ-003 (machine-readable read consistency), REQ-004 (`get_chunk` metadata), REQ-005 (remove `with_neighbors`)
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
