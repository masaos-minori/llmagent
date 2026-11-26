## Goal

Align ADR-002 with the implemented configuration-isolation ownership contract (REQ-004, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The ADR is 23084 B and has no size ceiling recorded in `tools/check_docs_structure.py`
  `SIZE_EXCEPTIONS`, so its edits are not size-constrained (re-verified 20261126).
- The ADR states no open discrepancy remains against the implementation
  (`docs/10_adr/adr_02_01_002_platform-config-isolation.md:344`); the sweep confirms that against
  `scripts/shared/mcp_dedup_config.py` before changing any wording.

## Design decisions
- Ownership is described in the Plan's vocabulary: each process owns its own configuration file,
  and the shared dedup configuration boundary is stated as implemented.
- No approval text is written; the ADR's Approval Record is not touched.

## Alternatives considered

N/A: the ADR already owns the configuration-isolation decision; only the ownership description
is aligned.

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`
### Procedure
- Check the ownership and hot-reload statements against the config field registry and the
  per-process config loading code; correct any description that predates the implemented
  contract.
- Add the proving-test reference for each claim the sweep changes.
### Method
- Verify the boundary against `scripts/shared/mcp_dedup_config.py` and
  `registry/manifests/config_ownership.yaml` before writing.
### Details
- Proving tests: `tests/mcp_servers/test_config_isolation_import.py`
  (`test_a_server_starts_when_only_its_own_config_file_is_present`),
  `tests/mcp_servers/test_config_isolation_fail_closed.py`
  (`test_invalid_own_table_aborts_startup_before_serving`).

## Compatibility considerations

N/A: documentation-only change; the governance file is referenced, not edited.

## Security considerations

N/A: no control is changed; the secret-exposure rationale is left as written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`, `check_docs_quality.py`,
  `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/test_config_isolation_import.py tests/mcp_servers/test_config_isolation_fail_closed.py`

## Completion criteria

- The ownership description matches the implemented per-process contract, no open discrepancy is
  claimed where one exists, and each changed claim cites a proving test that passes.

## Out of Scope

- No configuration behavior change; no approval is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the ADR and docs checkers (`rules/tool-gates.md`) and the cited proving tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (ADR-002 ownership alignment)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
