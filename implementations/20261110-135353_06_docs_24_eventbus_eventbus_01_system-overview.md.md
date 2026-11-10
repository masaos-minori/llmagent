## Goal
- State the EventBus keep decision and the producer/consumer status in `eventbus_01` consistently with ADR-006 and ADR-013 (REQ-001: the keep decision's visibility in the EventBus overview).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the Note block under `Purpose` (lines 27-28) and the `Agent Integration Status` section (lines 48-54).
- Not in scope: Architecture, Security Model, Known Issues, Keywords.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (documents 01, 02, 05, 06), then Phase 2 (documents 03, 07), then Phase 3 (document 04).

## Assumptions
- Step 3a re-verification (2026-11-10): lines 25-28 state the publish/subscribe purpose and that the Agent neither publishes nor subscribes; line 52 states that no Agent-side producer exists and the API accepts publishing from any HTTP client — the Plan's evidence is exact. The Agent-side clients were removed on 2026-11-10 (plan 002's implementation), so no client removal instruction is needed here.
- The keep decision and the "not yet defined" producer/consumer status are owned by ADR-006 (document 01); this document only states them consistently with links, per Docs content policy.

## Design decisions
- The status is added to the existing Note block (one sentence) and one sentence in `Agent Integration Status`; no new section and no role restatement (the role model stays owned by `eventbus_02_api-reference-index.md` and ADR-013).

## Alternatives considered
N/A: documentation-only statement.

## Implementation
### Target file
`docs/24_eventbus/eventbus_01_system-overview.md`

### Procedure
1. Extend the Note block (lines 27-28) with one sentence: the Event Bus is intentionally kept for a planned future integration; its producers and consumers are not yet defined (ADR-006, keep decision recorded 2026-11-09); future clients use the Publisher/Consumer role model (`eventbus_02_api-reference-index.md`, ADR-013).
2. In `Agent Integration Status` (after line 54), add one sentence: this status is intentional pending the producer/consumer definition recorded in ADR-006 and ADR-013.

### Method
- Edit in place; keep the document in English; link style follows the existing `See ...` / relative-path links in the file.

### Details
- Line 41's Security Model already names the five roles; no change needed there.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no behavior change; authorization content stays owned by ADR-013.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`.

## Completion criteria
- `eventbus_01` states the intentional keep decision with its date and the "not yet defined" producer/consumer status with links to ADR-006 and ADR-013; the checkers pass and no ADR content is duplicated.

## Out of Scope
- The Architecture and Security Model sections; the ADR files (documents 01-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/24_eventbus/eventbus_01_system-overview.md` as described in Procedure | Pending | — | — | |
| 2 | Run the documentation checkers listed in Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261109-112739_adrrev006_eventbus-future-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095717_adrrev006_eventbus-future-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-135353
- **Related target files**: `docs/24_eventbus/eventbus_01_system-overview.md`
