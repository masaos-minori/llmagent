## Goal

Declare the tier that maps to `medium` for the two MDQ write tools, and declare the dry-run
preview capability plus the `dry_run` input property, so approval classification and the
preview seam read the declaration instead of a config map.

## Scope
**Release unit**: tier change and its pins

- The two write-tool entries in `TOOL_LIST`: `agent_safety_tier` and `preview_capability`, and
  the `dry_run` property in both `inputSchema` blocks.
- The tier part is Phase 2; the capability and schema property are Phase 3, so the capability
  declaration lands only after the handler pass-through and the decision split can honor it.

## Assumptions

- `WRITE_DANGEROUS` is the only tier in the closed vocabulary that maps to `medium`
  (`scripts/agent/tool_policy.py` `_TIER_TO_RISK`, 78-82); the tier vocabulary is validated at
  registration and no new tier value is added.
- `config/agent.toml:186-187` are tool allowlist entries, not tier settings, so no configuration
  row changes (the issue's stale claim).
- The plan default for UNK-01 applies the MEDIUM floor to these two tools only; other
  `WRITE_SAFE` tools keep their tier.

## Design decisions

- The declared tier is the single risk source, so the floor is expressed here rather than as a
  per-tool risk rule or a config map.
- `preview_capability` is declared as `dry_run` only for the two write tools; the no-op contract
  requires the server to perform no side effect under `dry_run=True`, which is what the preview
  path in `scripts/mcp_servers/mdq/indexer.py` provides.

## Alternatives considered

- Changing `_TIER_TO_RISK["WRITE_SAFE"]` to `medium`: rejected, it moves every `WRITE_SAFE` tool
  at once and needs an owner decision (UNK-01).
- Adding a new tier value: rejected, the tier vocabulary is closed.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_tools.py`

### Procedure
1. Phase 2: in the `index_paths` entry (line 170) and the `refresh_index` entry (line 203), set
   `agent_safety_tier` to `WRITE_DANGEROUS`.
2. Phase 3: in the same two entries, set `preview_capability` from `none` (lines 175, 208) to
   `dry_run`, and add a `dry_run` boolean property to each `inputSchema` `properties` block.

### Method
`TOOL_LIST` entries are read by approval classification, plan-mode blocking, and the preview
seam (`scripts/mcp_servers/execution_context.py` `configure_tool_preview_capabilities()`, 63-79),
so a value change here is the whole change; no lookup code is added.

### Details

- `dry_run` property: `{"type": "boolean", "description": "Preview the planned effect without writing (default: false)"}`;
  it is not added to `required`, matching the optional-argument convention of the other schemas.
- `side_effect_class`, `retry_policy`, `idempotency_required`, `requires_serial`,
  `resource_scope_kind` and `resource_scope_keys` are unchanged; the field-set contract
  (`tests/mcp_servers/test_tool_schema_contract.py`, line 40) already asserts `preview_capability`
  presence, so only its value changes.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_tool_schema.py`
  - Procedure: assert the `dry_run` boolean property is present in both write-tool schemas.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_schema.py`

## Compatibility considerations

- The tier value is pinned by `tests/mcp_servers/mdq/test_mdq_routing.py` (target row 7) and by the
  shipped tier-`NONE` set in `tests/agent/test_tool_policy.py` (target row 11); both must land in
  the same phase as this declaration.
- `tests/agent/_producer_registry.py` derives `PRODUCER_TIERS` from these declarations, so the
  agent-layer risk tests follow the declaration automatically.

## Security considerations

- The change moves MDQ writes from automatic approval to a `y/N` prompt, which is the intended
  safety outcome; plan-mode blocking already covers both tools.

## Rollback considerations

- Revert the commit; the declaration has no persisted state and no migration path.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py tests/mcp_servers/mdq/test_mdq_tool_schema.py tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
- Full sequence per `rules/toolchain.md`: `uv run python tools/run_validation_gates.py`, `uv run lint-imports`, `uv run pytest`.

## Completion criteria

- Both write tools resolve to `medium` through the declared tier, and both declare `dry_run`
  (AC-1, AC-5).

## Out of Scope

- The classification lookup order and the risk mapping table: not changed here.
- The handler pass-through and the preview path: `scripts/mcp_servers/mdq/mdq_server.py` and
  `scripts/mcp_servers/mdq/indexer.py` rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 15 covers the tier statement |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`
