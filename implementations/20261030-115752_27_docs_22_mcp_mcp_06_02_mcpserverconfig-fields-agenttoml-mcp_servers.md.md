# Implementation Procedure: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

## Goal

Update the `required` field semantics in the MCP operator reference: the value is validated against the mandatoriness registry at startup and cannot weaken the approved classification (plan row: `required` field semantics validated against the registry).

## Scope

- The `required` bullet in `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` (:45-48): add the registry-validation sentence.
- No other field bullets change.

## Assumptions

- Lightweight row: one bullet's prose update.
- Existing text (:45-48) already describes abort/WARNING behavior and the subprocess rejection; the addition only states the validation source.

## Design decisions

- Append to the bullet: the effective `required` value is checked at startup against `registry/component_mandatoriness.yaml`; a `required = false` conflicting with a registry-`required` classification aborts startup with a named fatal (`component_mandatoriness` (new)), and a configured server absent from the registry is likewise fatal (ADR-004 Group 4 item 14 "Undeterminable component mandatoriness").
- Keep the subprocess-rejection sentence (:47-48) byte-identical.

## Alternatives considered

- N/A: docs-only change.

## Implementation

### Target file

`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure

1. Extend the `required` bullet (:45-48) with the validation sentence per Design decision.

### Method

Sentence insertion at the end of the bullet; line-width/format consistent with the file's existing bullets.

### Details

- Do not describe loader internals or pipeline stages (Docs content policy); name the registry path and the fatal label only.

## Compatibility considerations

- `check_docs_consistency.py --domain mcp` must pass; wording must match the fatal label row 5 implements (`component_mandatoriness` (new)).

## Security considerations

- N/A: operator documentation of an existing rule.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain mcp`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py` (routing.md docs checker set).

## Completion criteria

- An operator reading mcp_06_02 learns that config `required` cannot contradict the registry and what happens if it tries; docs checkers green.

## Out of Scope

- All code rows; ADR wording (row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `required` bullet | Pending | — | — | |
| 3 | Run the docs checker set | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (config-vs-registry contract as operator-facing semantics)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
