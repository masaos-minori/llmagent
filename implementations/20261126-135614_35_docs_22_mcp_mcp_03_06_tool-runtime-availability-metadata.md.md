## Goal
- Document explicit `config_dependent`, the capability dependency exclusion, and the restart-required registry (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the availability-metadata sections; the reason codes (seq 34) are out.

## Assumptions
- Verified in Step 3a: the document describes the status-derived `config_dependent` behavior being replaced (`mcp_03_06_tool-runtime-availability-metadata.md:25-53`) and is the canonical source for the `enabled` / `disabled_reason` invariant cited by `runtime_tool_registry.py:276`.

## Design decisions
- `config_dependent` is the producer-declared value carried on `RuntimeTool`, not derived from `status` (REQ-007); the registry is immutable after construction apart from the single policy rebinding, so an availability change requires a restart (REQ-008, D-2).

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure
1. Replace the status-derived description with the explicit-field rule.
2. Add the capability exclusion reason `capability` and the immutability and restart-required statement.

### Method
- Keep the `enabled` iff `disabled_reason == ""` invariant wording unchanged.

### Details
- The capability reason `capability` and the restart-required statement must match seq 13 and seq 14.

## Compatibility considerations
- N/A: consumers read diagnostics rows by key, unchanged shape.

## Security considerations
- N/A: documentation-only; metadata fields only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- docs gate: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`; then `rules/toolchain.md`.

## Completion criteria
- The document states the rule as implemented; docs gates pass.

## Out of Scope
- Code changes and the other docs files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document and run the docs gates (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-009` (Documentation Impact)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`
