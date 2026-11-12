## Goal
Add `class: Reference` to the `agent_08_04` front matter (front matter only) so it matches the other generated documents (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The front matter (lines 1-14) has no `class:`; `docs/24_eventbus/eventbus_08_reference_api.md` and `docs/23_agent/agent_13_reference-api-generated.md` carry `class: Reference` on line 4 (checked).
- `tools/generate_reference_table.py` targets this file for the `mandatoriness` rendering; the guarded block is not edited.

## Design decisions
- Place `class: Reference` where the sibling generated documents put it (after `tags:` list, per their front matter order).

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Add the front matter line `class: Reference`.
2. Run `generate_reference_table.py --check` to confirm the guarded block still matches.

### Method
- Insert one line `class: Reference` into the front matter, following the field order of `docs/24_eventbus/eventbus_08_reference_api.md`.

### Details
- Allowed value and meaning: `docs/00_governance/governance_02_documentation-metadata.md`. Do not touch the body or the `AUTO-GENERATED` block.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` — no drift.
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `check_docs_quality.py`, `check_docs_content_policy.py --strict` — pass.

## Completion criteria
- The front matter declares `class: Reference`; no other line changes; the checkers pass.

## Out of Scope
- Any change to the body or the generated block; the ADR-015 text (row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — the generated document declares `class: Reference`
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
