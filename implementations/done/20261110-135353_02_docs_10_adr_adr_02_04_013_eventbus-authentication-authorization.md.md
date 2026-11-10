## Goal
- Record in ADR-013 the EventBus keep decision and the caller-model status: producers and consumers are not yet defined, with the responsible component named as a pending item (REQ-001: the keep decision and its producer/consumer status).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: a new `Context` sub-section stating the caller-model status, and one `Approval Record` line.
- Not in scope: `Review Triggers` (item 1 was added by plan 002's implementation, commit `add36ad68` — do not edit), Decision, Invariants, Verification, Alternatives text.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (documents 01, 02, 05, 06), then Phase 2 (documents 03, 07), then Phase 3 (document 04).

## Assumptions
- Approval inputs: repository owner statements of 2026-11-09 (keep the EventBus) and 2026-11-10 (option B); recorded as "task-level approval decision (repository owner instruction)" per `docs/00_governance/governance_01_documentation-policy.md`, following this ADR's existing convention (lines 287-290). No approver name is invented.
- Step 3a re-verification (2026-11-10): `Review Triggers` item 1 (line 272) reads "A first publisher or consumer client of any kind is added to the EventBus." (added by plan 002's implementation, commit `add36ad68`); the older item at line 273 names replacement of the single trusted Agent process as a trigger and remains as written. The Plan's Background cites both items.
- Overlap with plans 001 and 002 on this ADR: resolved (both plans are in `plans/done/` and their documents were implemented); this Plan adds text beside the rewritten `Review Triggers` item only (Plan Assumptions sequencing held).

## Design decisions
- The caller-model status is a new `### Caller model status` sub-section at the end of `## Context` (after `### Constraints`): the EventBus is kept (recorded in ADR-006, repository owner 2026-11-09); no producers or consumers are defined today; the component that will define them and the integration timing are a marked pending item (Plan UNK-01); any first publisher or consumer client activates `Review Triggers` item 1 (line 272) and must use this ADR's authentication and authorization contract.
- The pending item is named as "maintainer decision (pending)", not as a component name — the Plan leaves the naming to the maintainer.

## Alternatives considered
N/A: documentation-only decision record.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Insert `### Caller model status` after the `### Constraints` list in `## Context`, containing the four statements above in three or four sentences.
2. Add one Current Decision Approval line to `Approval` → `Approval Record` citing the repository owner instructions of 2026-11-09 and 2026-11-10 in the existing task-level-approval wording (the style already at lines 287-290).
3. Run `check_adr_preservation.py` and read its report; this document's edits are intended changes.

### Method
- Edit in place; keep the ADR in English; front matter untouched; `Review Triggers` untouched.

### Details
- The new sub-section links to ADR-006 for the keep decision instead of restating it (Docs content policy).
- The existing `Out of Scope` item "Choosing between static bearer token / rotatable service token / mutual TLS / reverse-proxy authentication" is unchanged; the caller-model status does not reopen it.

## Compatibility considerations
- No new dependency edges in the ADR authority graph; `ADR-013 --Specializes--> ADR-006` already exists (`docs/10_adr/adr_01_index.md:108`).

## Security considerations
N/A: no behavior change; the sub-section states intent only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_preservation.py` (this file's edits are intended), `uv run python tools/check_docs_content_policy.py --strict`.

## Completion criteria
- ADR-013 records the keep decision with date and repository-owner source, states producers and consumers as not yet defined with the responsible component marked pending, and carries the approval record line; `Review Triggers` is unchanged; the checkers pass.

## Out of Scope
- Any other ADR section; `Review Triggers` rewriting (done by plan 002).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` as described in Procedure | Completed | — | — |  |
| 2 | Run the documentation checkers listed in Validation plan | Completed | — | — |  |

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
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`