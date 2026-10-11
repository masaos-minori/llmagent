## Goal
- Rewrite the `NackResult` docstring in `scripts/eventbus/delivery_repo.py` so each field's sentinel and stored-value roles are stated once (`REQ-001`).

## Scope
- Docstring text of `NackResult` only.
- No change to field names, annotations, defaults, executable statements, or `nack_event`.
- The first docstring line ("Return value for nack_event().") stays unchanged because it is the generated reference summary.

## Assumptions
- Verified against current source, the return paths of `nack_event` are:
  - event not found: `NackResult(-1, -1)`;
  - event already in the DLQ, or the consumer already ACKed it: `NackResult(-2, -2)`;
  - idempotent repeat of the same attempt: `NackResult(stored delivery_failure_count, -2, consumer count)`, or `NackResult(-1, -1)` if the consumer row is missing;
  - normal path: stored events-level `delivery_failure_count` and `cycle_failure_count`, plus the per-consumer count when `consumer_id` was provided; `NackResult(-1, -1)` if the event row cannot be read back.
- Verified against current source: the events-level values are not written under the per-consumer model, so they are legacy values.
- Verified against current source: the NACK route reads `delivery_failure_count` for the `-1` and `-2` outcomes and uses `consumer_failure_count` for promotion.

## Design decisions
- Describe, per field, the sentinel values first and the stored legacy value otherwise, and mention the idempotent repeat case where `cycle_failure_count` is `-2` while `delivery_failure_count` holds the stored value.
- Do not change the type annotations even though they are narrower than the real values; that is out of scope.

## Alternatives considered
- Add an explicit outcome field: rejected; needs an owner decision (UNK-01 of the plan).

## Implementation
### Target file
`scripts/eventbus/delivery_repo.py`

### Procedure
1. Re-read the return statements of `nack_event` and confirm the list in Assumptions still holds.
2. Replace the field lines of the `NackResult` docstring, keeping the first line and the `consumer_failure_count` description.
3. Review `git diff` and confirm only docstring text changed.

### Method
- Use the Edit tool on the docstring lines only.
- Keep each line within the repository's line-length convention for docstrings in this file.

### Details
- `delivery_failure_count`: `-1` if the event is not found; `-2` if the event is in an invalid state (already in the DLQ, or already ACKed by the consumer); otherwise the stored events-level value, a legacy value that is not modified under the per-consumer model.
- `cycle_failure_count`: same sentinels; otherwise the stored legacy value; an idempotent repeat NACK of the same attempt returns `-2` here while `delivery_failure_count` holds the stored value.
- `consumer_failure_count`: unchanged wording.

## Compatibility considerations
- Docstring only; no signature, annotation, or behavior change.

## Security considerations
N/A: docstring only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/delivery_repo.py` before it is committed.

## Validation plan
- Run `uv run pytest tests/eventbus`, `ruff` (check and format), and `mypy` per `rules/toolchain.md`.
- Run `uv run python tools/generate_reference_table.py --type eventbus --dry-run` and confirm the block is unchanged.

## Completion criteria
- The docstring documents both sentinels for both fields, the legacy meaning otherwise, and the idempotent case; the diff is docstring text only; checks report no new failures.

## Out of scope
- Executable changes, annotations, `nack_event`, the route, tests, other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the NackResult docstring | Completed | 20261012-084422 | 20261012-084422 | — NackResult docstring rewritten; diff is docstring only |
| 2 | Add or update tests per Validation plan | Completed | 20261012-084422 | 20261012-084422 | N/A: docstring only N/A: docstring only |
| 3 | Run tests, ruff, mypy, and the generator dry-run | Completed | 20261012-084422 | 20261012-084422 | — tests/eventbus 333 passed 1 skipped; ruff and mypy clean; generator output unchanged |

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
- **Requirement ID**: `REQ-001` (NackResult docstring)
- **Source issue**: issues/20261012-083711_eb016nackres_decide-the-contract-of-legacy-events-level-counters-in-nackresult.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-084200_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-084236
- **Related target files**: scripts/eventbus/delivery_repo.py