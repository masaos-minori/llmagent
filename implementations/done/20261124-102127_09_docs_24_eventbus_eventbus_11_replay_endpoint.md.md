## Goal
Add the replay-floor bounds, HTTP 410 `replay_position_expired` (new), and the `since_seq=0` earliest-retained meaning to the replay endpoint document (REQ-004, REQ-008).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_11_replay_endpoint.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- Add one "Retained History and Expired Positions" section after "Invalid Parameters"; keep the existing parameter table and add only the `since_seq=0` wording.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_11_replay_endpoint.md`

### Procedure
1. Parameters: in the `since_seq` row state that `0` means the earliest retained event.
2. Add "Retained History and Expired Positions": `earliest_available_seq` (new) is the lowest retained `seq` and `latest_available_seq` (new) the highest; a `since_seq` before `earliest_available_seq` (new) fails with HTTP 410 and error code `replay_position_expired` (new); replay advances no consumer offset, so nothing is advanced to the floor; where the bounds are exposed in a response is defined by the implementation.
3. State that the same rule applies to a `/subscribe` resume and link to `eventbus_03`; state that the check is not yet implemented (EVENTBUS-002).

### Method
- Use the Edit tool; follow the Markdown style of the existing sections.

### Details
- Keep "Ordering and Consistency" unchanged.
- Do not add the 410 to the Invalid Parameters list, since it is a retention condition and not a parameter error.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py -q`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The `since_seq=0` meaning, the bounds, and the HTTP 410 response are documented with the EVENTBUS-002 citation; existing sections are unchanged.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102725 | 20261124-102725 | Changed: docs/24_eventbus/eventbus_11_replay_endpoint.md |
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
- **Requirement ID**: REQ-004, REQ-008 (replay floor)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_11_replay_endpoint.md`