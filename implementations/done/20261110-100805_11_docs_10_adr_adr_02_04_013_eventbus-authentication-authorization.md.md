## Goal
- Correct the ADR-013 `Current State` paragraph so it states where consumer authorization actually lives (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one sentence in `### Current State` about `Depends(require_consumer_identity)`.
- Not in scope: `Context` and `Review Triggers` (plans 002 and 006), decisions, invariants, approval text.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14). Phase 4.

## Assumptions
- After Phases 2-3, `/subscribe` runs consumer-pair authorization through a dependency in `subscribe_route.py`, and ack/nack run it inside `authorize_event_pair` called by the handler. Falsifiable by reading `scripts/eventbus/subscribe_route.py` and `ack_route.py` after the code phases.
- Overlap with plans 002 and 006 on this ADR: different sections (compatible; plan 002 first for `Review Triggers`).

## Design decisions
- State intent and boundary only (docs content policy): each route has one handler carrying its role dependency; consumer routes additionally authorize the `(consumer_id, topic)` pair, through a dependency for subscribe and inside the handler for ack and nack because the topic comes from the event.

## Alternatives considered
N/A: documentation-only correction.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Replace the sentence "Consumer-facing routes (/subscribe, /ack, /nack) additionally require `Depends(require_consumer_identity)` for consumer identity validation." in `### Current State` with the accurate statement above, without symbol names beyond those the ADR already uses.
2. Do not change any other paragraph; run `check_adr_preservation.py` and read its report.

### Method
- Edit in place; keep the ADR in English and the front matter untouched.

### Details
- The ADR text (line 46) is the only inaccurate statement found (checked in Step 3a).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no behavior change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py` (expect no ERROR for this sentence), `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_quality.py`.

## Completion criteria
- `### Current State` describes the actual layering; the checkers pass.

## Out of Scope
- Any other ADR section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` as described in Procedure | Completed | 20261110-113335 | 20261110-113335 |  |
| 2 | Run the documentation checkers listed in Validation plan | Completed | 20261110-113335 | 20261110-113335 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`