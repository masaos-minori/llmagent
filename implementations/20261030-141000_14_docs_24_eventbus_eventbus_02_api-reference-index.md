# Implementation Procedure: `docs/24_eventbus/eventbus_02_api-reference-index.md` (EBAUTHGEN001 Phase 3)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-008, AC-7)

## Goal
Refresh the EventBus API-reference index so the admin-topics endpoint entry reflects the
generation parameters and response fields after doc 03, keeping the index aligned with
`eventbus_08_reference_api.md`.

## Scope
### Target
`docs/24_eventbus/eventbus_02_api-reference-index.md` (existing).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
### Context and prior decisions
- Index-only doc: pointers and one-line summaries, no duplicated contract text
  (`skills/DESIGN.md` Docs content policy).

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Update the admin-topics entry summary to mention optimistic concurrency (required
   `expected_generation`, `previous_generation`/`new_generation` response, 409) and the
   optional `ttl_seconds`, cross-referencing `eventbus_08_reference_api.md` as the detail
   page. No new pages or section restructuring.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 03 (route contract landed — the index must describe it)
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert the single doc file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` and
  `uv run python tools/generate_reference_table.py --check` pass after the update.

## Completion criteria
- Index matches the landed endpoint contract; docs checkers green.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_03_scripts_eventbus_admin_route.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- Docs-only row: no new constructs; no markers applied.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008; AC-7
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 14
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `docs/24_eventbus/eventbus_02_api-reference-index.md`
