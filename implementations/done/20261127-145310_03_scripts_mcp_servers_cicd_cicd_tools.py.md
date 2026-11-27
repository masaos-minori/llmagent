# Implementation Procedure — scripts/mcp_servers/cicd/cicd_tools.py

## Goal

Publish each tool's `inputSchema` from the strict request models through `build_input_schema()` instead of hand-written property dicts, so the contract a client discovers at `/v1/tools` equals the contract enforced at call time.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-004 (published tool schemas generated from the strict request models). Acceptance criterion: AC-3.

## Assumptions
- The tool names, export names, and endpoints do not change, so the generated tool-ownership matrix and the schema-export policy docs are not affected (Plan consumer scan).
- Descriptions currently carried by the module-level property dicts must survive the switch; re-pin them on the model fields in the `cicd_models.py` row before removing the dicts here.
- Step 3a verification (20261127): the wording that moves is the tool-side text currently in the property dicts — `Repository slug in 'owner/repo' format`, `Workflow file name (e.g. ci.yml) or numeric workflow ID`, `Workflow run ID (from get_workflow_runs output)` — not the shorter wording the models carry today (user decision, 20261127). The `cicd_models.py` row performs the move; this row removes the dicts after it.
- Step 3a verification (20261127): `McpToolProperty` (`cicd_tools.py:13`) becomes unused once the dicts are removed and must be dropped from the import; `TOOL_FIELD_SET_VERSION` stays because `policy_version` uses it (line 55).

## Design decisions
- `build_input_schema()` from `scripts/mcp_servers/request_contract.py` (line 44) is the only schema generator; no local dict assembly remains.

## Alternatives considered
- Keep the shared property dicts and add constraints manually: rejected — REQ-004 names the models as the single source, and the guardrail test compares the published schema with the dispatch table.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_tools.py`

### Procedure
- Replace each `TOOL_LIST` entry's hand-written `inputSchema` with `build_input_schema(Model)` for the corresponding strict request model from `cicd_models.py`.
- Remove the module-level `_REPO_PROPERTY`, `_WORKFLOW_PROPERTY`, `_RUN_ID_PROPERTY` dicts once no entry uses them.

### Method
- Entries currently build `inputSchema` from the property dicts with `type` and `description` only and do not import `build_input_schema` (verified in Step 3a); the metadata fields (`requires_serial`, `resource_scope_kind`, `policy_version`) stay unchanged.
- Step 3a verification (20261127): the guardrail test compares tool names, dispatch keys, and write/serial flags; it does not compare schema content. Model-to-schema equality is asserted for the file and github domains only (`tests/mcp_servers/file/test_file_schema_consistency.py`, `tests/mcp_servers/github/test_github_tool_registry.py`), so the cicd description equality is pinned by `tests/mcp_servers/cicd/test_cicd_models.py` (sibling row), not by this reference file.

### Details
- Field descriptions move to the model field definitions (`Field(description=...)`) so `build_input_schema()` emits the same description text the pinned tests assert.

## Compatibility considerations
- Clients see the same tool names and field names; the schema gains `additionalProperties: false` and the numeric/non-empty constraints, which is the intended change (Plan Risks: newly rejected inputs are listed in the change record).

## Security considerations
- N/A: no security behavior changes here; the enforcement lives in the models row.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Integration: published schema equals the model schema — `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (reference file, not modified).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Every published `inputSchema` is produced by `build_input_schema()` and matches the model schema including `extra="forbid"` (AC-3); the layer-consistency guard passes.

## Out of Scope
- The model constraints themselves (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-162349 | 20261127-162349 | files: scripts/mcp_servers/cicd/cicd_tools.py |
| 2 | Add or update tests per Validation plan | N/A | — | — | the guardrail test is a reference file, not a modification target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-162349 | — | ruff/mypy/bandit/lint-imports clean; tests/mcp_servers/cicd/ + tests/mcp_servers/test_tool_schema.py 256 passed; full suite deferred to end of batch end-of-batch full suite: 6 failures all matching tools/known_test_failures_baseline.txt; diff-cover 96% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-004 (published tool schemas generated from the strict request models)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_tools.py`