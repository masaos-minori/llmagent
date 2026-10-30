# Implementation Procedure: agent_13_reference-api-generated.md manifest-rendered block

## Goal

Move the Agent reference doc's guarded block onto the manifest rendering path
(REQ-005/REQ-008; same mechanism as docs 19-20 for the agent domain).

## Scope

**In scope:**
- Refresh of the guarded region `docs/23_agent/agent_13_reference-api-generated.md:31-205`
  via generator regeneration (guard markers unchanged).

**Out of scope:**
- Generator code (doc 05), agent manifest entry content.

## Assumptions
- Block regeneration is byte-identical at migration time (Phase 3 condition).
- The agent manifest is the entry source for this block once the agent builder lands
  (doc 05 step 5 porting sequence).

## Design decisions
N/A: docs-only row.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. After the agent manifest builder lands, run `uv run python
   tools/generate_reference_table.py --manifests` and commit the regenerated block.

### Method
Docs-only (generator-produced content).

### Details
- Guard markers `:31`/`:205` unchanged.

## Compatibility considerations
CI `--check` step (`.github/workflows/ci.yml:35`) must be green in the same commit.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` green; docs checker
  sequence (`routing.md`).

## Completion criteria
Block renders from the agent manifest with no content drift.

## Out of Scope
Generator, manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate block via `--manifests` and commit | Pending | — | — | Phase 3 |
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
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
