# Implementation Procedure: `config/documentation_canonical_sources.toml`

## Goal

Register the mandatoriness registry as the canonical source for mandatoriness claims (plan row: register the registry as canonical source; supports AC-4 drift governance and the Canonical Source policy in `skills/DESIGN.md`).

## Scope

- One new `[[canonical_sources]]` entry appended to `config/documentation_canonical_sources.toml`.
- Existing entries untouched; the registry schema is validated by `tools/check_canonical_source_registry.py` (its `VALID_CLAIM_TYPES` set at :29-43).

## Assumptions

- Lightweight row: single TOML entry.
- Cross-plan overlap: toolexec001 (row 18 of that plan) also appends entries to this file. Landing order is append-only and order-insensitive; rebase conflicts here are line-appends only — record for the implementation phase.

## Design decisions

- Entry fields (existing entry shape, e.g. the eventbus entries at :3-16): `decision_target = "mcp.component-mandatoriness"`, `claim_type = "security-policy"` (mandatoriness is a fail-closed policy classification; `security-policy` is in `VALID_CLAIM_TYPES` and matches the claim nature better than `configuration-schema`, which describes field schemas), `source_paths = ["registry/component_mandatoriness.yaml"]`, `area = "MCP"`, `notes` naming ADR-004 Group 3 item 13 and that the `agent_08_04` table is generated from it.
- Single source path (no multi-path exemption needed: `check_canonical_source_registry.py` :122-125 restricts multi-path entries by claim type).

## Alternatives considered

- `claim_type = "verification-contract"` — rejected: that type describes test/verification claims (used by ADR matrix entries); mandatoriness is the policy itself. Needs Confirmation: registry-owner review of the claim-type choice at implementation time.

## Implementation

### Target file

`config/documentation_canonical_sources.toml`

### Procedure

1. Append the entry per Design decisions, after the last existing `[[canonical_sources]]` block.

### Method

Literal TOML append following the file's existing entry formatting (`version = "1"` header stays).

### Details

- `source_paths` points at the registry file row 1 creates; the entry becomes meaningful only once rows 1 and 26 exist — land 28 in the same commit group as 01 (or later), never before, so no canonical source points at a missing file (the registry checker validates path existence per `check_canonical_source_registry.py` semantics).

## Compatibility considerations

- `uv run python tools/check_canonical_source_registry.py` and `check_canonical_source_conflicts.py` must pass; new `decision_target` must not collide with existing targets (grep shows none for mandatoriness today).

## Security considerations

- N/A: registry metadata.

## Rollback considerations

- N/A: revert the commit (remove the entry).

## Validation plan

- `uv run python tools/check_canonical_source_registry.py`, `uv run python tools/check_canonical_source_conflicts.py`, `check_canonical_document_prose.py` (routing.md Canonical Source checker set).

## Completion criteria

- Docs making mandatoriness claims resolve to the registry through the Canonical Source Registry; all three canonical-source checkers green.

## Out of Scope

- Registry file (row 1), generated table (row 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the canonical-source entry | Pending | — | — | Land with/after row 1 |
| 3 | Run the Canonical Source checker set | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 1 must exist so the source path resolves | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (drift governance: single authoritative source registered)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `config/documentation_canonical_sources.toml`
