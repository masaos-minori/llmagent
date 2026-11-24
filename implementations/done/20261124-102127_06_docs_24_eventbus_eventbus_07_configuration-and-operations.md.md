## Goal
Document the retention task, capacity measurements, backup and archive retention, WAL checkpoint around retention and shutdown, and the absence of retention keys in the configuration and operations document (REQ-003, REQ-006, REQ-007, REQ-008).

## Scope
**Release unit**: eventbus-docs

- Edits only `docs/24_eventbus/eventbus_07_configuration-and-operations.md`; applied with the other documents of the release unit because the EventBus documents cross-link and are validated together.

## Assumptions
- The amended ADR-006 (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) is the contract; the document links to it instead of restating numbers.
- Where current code differs, the document cites EVENTBUS-001 (code still appends `events.jsonl`) or EVENTBUS-002 (no retention, purge, capacity signal, replay floor, or HTTP 410); no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Before removing or renaming a heading, search the repository for links to its anchor (`rg -n "#<anchor>" docs`); no link to a retired heading exists today (checked in Step 3a), and a new link must not point to a removed heading.

## Design decisions
- One new "Retention and Capacity Operations" section; the health detail stays in `eventbus_10`, the retention rules in `eventbus_05`.
- Configuration Fields lists only keys that exist.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. Configuration Fields: add one bullet that no retention or capacity key exists in `EventBusConfig` or `config/eventbus.toml`, so none is documented (EVENTBUS-002).
2. Health Endpoint Semantics: add a pointer to the retention and capacity signals in `eventbus_10`.
3. Add "Retention and Capacity Operations": the dedicated retention task (separate from the DLQ repair loop and the authorization sweep) and where it is defined; measurements (database size, WAL size, archive size, DLQ artifact size, audit-log size, free disk); the audit-log destination is deployment-defined and outside `eventbus.sqlite`; warning versus critical behavior by reference to `eventbus_10`; all marked not yet implemented (EVENTBUS-002).
4. Backup and archive retention: `python -m eventbus.db_tools rotate` writes a verified archive through the SQLite backup API; retention of verified archives by generation, age, and total size, a minimum number of verified recovery generations, and protection of the latest verified candidate are required, with values undefined (EVENTBUS-002); the existing statement that no retention logic exists stays.
5. Shutdown: add that the retention task stops between batches, and that a WAL checkpoint accompanies retention and shutdown per ADR-008's WAL requirement.
6. DLQ Operations > Monitoring: keep the sweep statement and add DLQ artifact size as a measurement.

### Method
- Edit with the Edit tool; keep the existing headings and add the new section after "Delivery Operations" and before "DLQ Operations" (or after DLQ Operations).

### Details
- `tests/eventbus/test_eventbus_config.py` docstrings cite this file by path only; no heading it cites changes.
- Do not describe thresholds or key names.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run pytest tests/eventbus/test_eventbus_config.py -q`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The retention task, measurements, archive retention requirements, and shutdown behavior are documented; no invented key, field, or threshold appears; each undefined item cites EVENTBUS-002.

## Out of Scope
- Any other file, code, configuration, the API manifest, and the generated block of `eventbus_08_reference_api.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-102658 | 20261124-102658 | Changed: docs/24_eventbus/eventbus_07_configuration-and-operations.md |
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
- **Requirement ID**: REQ-003, REQ-006, REQ-007, REQ-008 (operations and configuration)
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-101736_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-102127
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`