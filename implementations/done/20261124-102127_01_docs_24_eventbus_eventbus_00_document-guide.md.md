## Goal
Route retention, replay-floor, capacity, and archive questions in the document guide to the revised documents and state the sole-source-of-truth fact in the canonical-source list (REQ-001).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_00_document-guide.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- Add routing rows only; keep the existing tables' format and every existing row.
- Cite the Known Issues instead of describing code state.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_00_document-guide.md`

### Procedure
1. AI Query Routing table: add one row each for retention and purge (`eventbus_05`, `eventbus_07`), replay floor and HTTP 410 (`eventbus_11`, `eventbus_05`), and capacity and readiness signals (`eventbus_10`, `eventbus_07`).
2. Canonical Sources: state that `eventbus.sqlite` is the only EventBus system of record and name ADR-006 as its authority.
3. Known Issues / Deferred Items: name EVENTBUS-001 and EVENTBUS-002 in the existing pointer to the governance document.

### Method
- Edit with the Edit tool; match the row style of neighboring routing rows (topic cell, then document cell).

### Details
- Do not change the front matter `related` list (no new file is added).
- The Reading Order and Purpose text stay unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_structure.py`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The routing table has retention, replay-floor, and capacity rows; the Canonical Sources text names `eventbus.sqlite` as the only system of record; all links resolve.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102547 | 20261124-102547 | Changed: docs/24_eventbus/eventbus_00_document-guide.md |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261124-102753 | 20261124-102753 | Release unit eventbus-docs eventbus consistency, docs structure/quality/content-policy, known-deviation sync, needs-confirmation inventory, reference drift checks and 77 tests pass; preservation findings are intended |

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
- **Requirement ID**: REQ-001 (guide routing), REQ-009 (checks)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_00_document-guide.md`