## Goal
- Add the EventBus to the `security_01` trust-boundary diagram and the threat vector list (REQ-003: the EventBus must be named in the trust-boundary model; its authN/authZ section already exists).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the diagram code block (lines 40-43), the boundary-crossing list (lines 45-51), and the threat vector list (lines 67-75).
- Not in scope: `Protected assets` (line 61 already names the EventBus database), the existing `EventBus Authentication and Authorization` section (line 272), the loopback constraint (line 129), anything else.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (documents 01, 02, 05, 06), then Phase 2 (documents 03, 07), then Phase 3 (document 04).

## Assumptions
- Step 3a re-verification (2026-11-10): the diagram code block (lines 40-43) names only Agent/LLM/MCP/RAG paths, the boundary-crossing list intro at line 45 counts two crossings (items at lines 47 and 49), the threat vectors (lines 69-75) name no EventBus vector, and the per-API table (lines 77-90) lists MCP servers only — the Plan's evidence is exact; the EventBus authZ section at line 272 already carries the role table, so no role table is duplicated here (Docs content policy: point, do not duplicate).
- Role vocabulary: Publisher and Consumer (ADR-013 roles); the term "Subscriber" is not introduced.

## Design decisions
- One boundary crossing is added (Client → EventBus), making the list three items; the EventBus process keeps its existing status as a standalone trusted process described by the line 272 section — the diagram only names the crossing and its controls.

## Alternatives considered
N/A: documentation-only addition; duplicating ADR-013's role table here was rejected by the content policy.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. In the diagram code block (lines 40-43), add one line after line 42: `      \-> EventBus client (Publisher/Consumer role) -> EventBus process -> SQLite / SSE delivery`
2. Change line 45 ("Two primary boundary crossings exist:") to "Three primary boundary crossings exist:" and add a third numbered item after line 49: **Client → EventBus** — Publisher/Consumer-role clients call the EventBus HTTP API; the boundary enforces per-route Bearer-token authentication, role and `consumer_id`/topic authorization, and loopback-only binding; authority: an `ADR-013-eventbus-authentication-authorization` link in the existing link style used inside the `EventBus Authentication and Authorization` section, and a pointer to that section (line 272).
3. Append one threat vector after line 75: **Unauthorized EventBus access**: an unauthenticated or wrongly-scoped caller publishes, consumes, acknowledges, or administers delivery state; mitigated by ADR-013's fail-closed authentication and authorization boundary and the loopback-only bind (INV-01, INV-02, INV-06, INV-07).

### Method
- Edit in place; keep the document in English; do not renumber existing items other than the boundary-list intro sentence.

### Details
- The threat vector cites ADR-013 invariants by name only; the mitigation detail lives in the line 272 section and ADR-013 itself.
- The per-API table (lines 77-90) stays MCP-only: the EventBus is covered by its own authZ section, per the Plan's evidence that the table lists MCP servers only.

## Compatibility considerations
N/A: documentation only; no code or configuration references change.

## Security considerations
- Names the boundary and threat explicitly; states no secret or token value (INV-05 of ADR-013 is untouched).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`.

## Completion criteria
- The diagram and the boundary list name the EventBus crossing with its controls, the threat vector list names the EventBus threat with its mitigation link, and no role table or ADR-013 content is duplicated; the checkers pass.

## Out of Scope
- The `EventBus Authentication and Authorization` section; the protected-assets list; ADR-013 itself (document 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/91_security/security_01_architecture-and-trust-boundaries.md` as described in Procedure | Pending | — | — | |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261109-112739_adrrev006_eventbus-future-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095717_adrrev006_eventbus-future-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-135353
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`
