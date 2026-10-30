# Implementation Procedure: eventbus_08_reference_api.md outbox reference surface

## Goal

Refresh `docs/24_eventbus/eventbus_08_reference_api.md` so the EventBus reference matches the
shipped surface after the outbox: new public functions in the auto-generated table and the
new metrics/config knobs named in the responsibilities text (REQ-005, REQ-009; plan AC-4).

## Scope

**In scope:**
- Regeneration of the AUTO-GENERATED class/function table (`eventbus_08_reference_api.md:44-129`).
- One short responsibilities/keywords touch for the outbox knobs and counters.

**Out of scope:**
- Hand-editing between the guard comments (tool-owned region), operational prose (rows 12-13).

## Assumptions
- Verified at HEAD `124e340b4`: the table region is generated from `scripts/eventbus/*.py`
  top-level public classes/functions by `tools/generate_reference_table.py --type eventbus`;
  CI runs `--check`. Existing DLQ entries (`is_promotable`, `sweep_orphans` at 98-99) show the
  row format new entries will take (`process_outbox` (new), row-04 repo functions).
- Metrics are documented in prose docs (docs-03/09), not in the auto table; the reference-doc
  duty here is the function surface plus knob names.

## Design decisions
- Regenerate rather than hand-extend the table (the guard comment forbids manual edits).
- Add the three config knob names and three new counter names to the `dlq` module's
  Responsibilities line in one sentence; values are not duplicated in docs (config file is
  the source of truth).

## Alternatives considered
- Skipping docs-08: rejected — the frozen target table lists it and `generate_reference_table.py
  --check` fails CI once `process_outbox` (new) and the repo functions exist without a refreshed
  table.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. After rows 03-04/06 land, run `uv run python tools/generate_reference_table.py --type eventbus`.
2. Update the dlq-responsibilities sentence (and Keywords line if the generator/tooling
   requires) to name `dlq_outbox` (new) generation, the retry knobs, and the three counters.

### Method
Tool regeneration + one prose sentence.

### Details
- Doc-only change; never appears ahead of the code rows in deploy order.

## Compatibility considerations
- CI `generate_reference_table.py --check` gate (plan row evidence).

## Security considerations
- N/A.

## Rollback considerations
- Revert with the code rows; a stale table fails `--check`, so revert in lockstep.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` + docs checkers per `routing.md`.

## Completion criteria
- Reference table is generator-current and the responsibilities text names the shipped knobs.

## Out of Scope
- Ordering-contract docs (rows 12-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate table after code rows land | Pending | — | — | |
| 2 | Prose sentence for knobs/counters + `--check` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`, `REQ-009`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`
