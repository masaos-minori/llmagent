# Implementation Procedure: mcp_01_tool_ownership_matrix.md manifest-rendered block

## Goal

State in the MCP ownership doc that its guarded block is now rendered from
`registry/manifests/tool_ownership.yaml` (REQ-008 superseded-copy removal, plan AC-5;
rendering path from doc 05).

## Scope

**In scope:**
- Refresh of the guarded region `docs/22_mcp/mcp_01_tool_ownership_matrix.md:82-97`
  produced by `generate_reference_table.py` (guard markers unchanged); hand-written
  text outside the guards keeps its meaning, with the tool-ownership narrative pointing
  at the manifest as the machine-readable source.

**Out of scope:**
- Generator code (doc 05), manifest content (doc 07).

## Assumptions
- Block regeneration is byte-identical at migration time (pilot condition, AC-4); only
  the welcome line inside the guard changes wording.

## Design decisions
- No structural doc edits outside the guard region — containment and reference checks
  (docs 01-02) stay green.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_01_tool_ownership_matrix.md`

### Procedure
1. After doc 05 lands, run `uv run python tools/generate_reference_table.py
   --manifests` and commit the regenerated guard block.
2. One sentence outside the guards: ownership facts are generated from the manifest.

### Method
Docs-only (generator-produced block content).

### Details
- Guard markers `:82`/`:97` must remain byte-identical.

## Compatibility considerations
`--check` (CI `ci.yml:35`) compares this block; regeneration and commit must happen in
the same change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` green; docs checker
  sequence (`routing.md`).

## Completion criteria
Block renders from the manifest, `--check` green, surrounding prose names the manifest.

## Out of Scope
Generator, manifest file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate block via `--manifests` and commit | Pending | — | — | After doc 05 |
| 2 | Run the documentation checker sequence (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`, `REQ-008`
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `docs/22_mcp/mcp_01_tool_ownership_matrix.md`
