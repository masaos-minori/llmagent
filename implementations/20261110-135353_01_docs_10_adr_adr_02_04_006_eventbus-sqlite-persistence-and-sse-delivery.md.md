## Goal
- Record the EventBus keep decision and the producer/consumer model (its explicit absence) in ADR-006 (REQ-001: the EventBus service is kept with planned future integration).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: ADR-006 `Decision` (new decision item), `Consequences`, and `Approval` record text.
- Not in scope: existing Decision items, Invariants, Verification, Alternatives text.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (documents 01, 02, 05, 06), then Phase 2 (documents 03, 07), then Phase 3 (document 04).

## Assumptions
- Approval inputs are the repository owner's statements of 2026-11-09 (keep the EventBus) and 2026-11-10 (Group 7 option B); they are recorded as "task-level approval decision (repository owner instruction)" per `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard, following the convention ADR-013 already uses (`adr_02_04_013...md:287-290`). No approver name or reviewer date is invented.
- Producers and consumers are stated as "not yet defined" with the defining component left as a marked pending item (Plan UNK-01); registering the pending item through `governance_03` is a maintainer action (the Plan lists `governance_03` as a Reference File, not a target).
- Overlap with plan `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` on this ADR: different statements (the version stamp there; the keep decision here) — compatible (Plan Assumptions, re-confirmed in Step 3a).

## Design decisions
- The keep decision is recorded as a new Decision Details item, not a new section: "the EventBus service is kept (planned future integration); it currently has no defined producers or consumers, and that absence is intentional."
- Role vocabulary: the new text uses the ADR-013 role names (Publisher, Consumer); ADR-006's generic publish/subscribe infrastructure wording in `Context`/`Constraints` is not rewritten.

## Alternatives considered
N/A: documentation-only decision record; the Plan already rejected deferral (the gated Issues stay blocked).

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Add one Decision Details item recording the keep decision (date 2026-11-09, repository owner instruction) and the intentional absence of defined producers and consumers, with the defining component and timing as a marked pending item.
2. Add one Positive Consequences bullet: the intentional-keep status is now explicit, so reviews can distinguish it from abandonment.
3. Add one Current Decision Approval line to `Approval` → `Approval Record` citing the repository owner instruction of 2026-11-09 in the existing task-level-approval wording.
4. Run `check_adr_preservation.py` and read its report; this document's edits are intended changes.

### Method
- Edit in place; keep the ADR in English; front matter untouched.

### Details
- `Context` and `Constraints` keep their generic Subscriber wording (verified in Step 3a); future-client role statements link to ADR-013 and `eventbus_02_api-reference-index.md` instead of restating the role table (Docs content policy: point, do not duplicate).
- ADR-006 already relates to ADR-013 (`Related ADRs`, index Authority Graph line 106, re-verified 2026-11-10 at HEAD `9a86dede9`); no new dependency edge is added.

## Compatibility considerations
- Plan AC-05 names ADR-004 and ADR-013 for the preservation check; the ADR-006 edit made here is also an intended change and must be reported as such.

## Security considerations
N/A: no behavior change; the authorization contract stays owned by ADR-013.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_preservation.py` (this file's edits are intended), `uv run python tools/check_docs_content_policy.py --strict`.

## Completion criteria
- ADR-006 states the keep decision with its 2026-11-09 date and repository-owner source, states the producer/consumer model as not yet defined (marked pending), and carries the approval record line; the checkers pass.

## Out of Scope
- Any other ADR section; changes to `eventbus_01`, `security_01`, or the ADR index (covered by documents 05, 06, 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` as described in Procedure | Pending | — | — | |
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
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
