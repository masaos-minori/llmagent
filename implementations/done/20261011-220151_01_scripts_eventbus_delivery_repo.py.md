## Goal
- Make the `nack_event` docstring in `scripts/eventbus/delivery_repo.py` describe the per-consumer failure model, and check the `NackResult` docstring for the same drift (`REQ-001`, `REQ-002`).

## Scope
- Docstring text of `nack_event` (summary line and description) and, only if stale, the `NackResult` docstring.
- No change to executable statements, SQL, return values, signatures, or comments inside the function body.

## Assumptions
- Verified against current source: the body of `nack_event` only upserts `consumer_delivery_failure_count` and `consumer_last_nack_attempt`; it reads the events-level counters back for the return value and never writes them.
- Verified against current source: the only writes to `events` under `scripts/eventbus/` set `dlq_at` or `dlq_requeue_count`.
- Verified against current source: `ack_route.py` uses the events-level `delivery_failure_count` of the result only as the `-1` and `-2` sentinels, and the per-consumer count for DLQ promotion.
- The summary line becomes the generated reference description, so it must be accurate on its own and stay a single line.

## Design decisions
- Rewrite the first line to say NACK records a per-consumer failure for an event, with no mention of incrementing events-level counters.
- In the description, state that the events-level counters are not modified and are returned as stored (legacy values), and keep the statements about DLQ'd events, already-acked consumers, and per-attempt idempotency.

## Alternatives considered
- Edit the generated reference row by hand: rejected; it is regenerated from the docstring.
- Remove the legacy counters from `NackResult`: rejected; out of scope and a behavior change.

## Implementation
### Target file
`scripts/eventbus/delivery_repo.py`

### Procedure
1. Re-run `rg "UPDATE events" scripts/eventbus` and confirm that no statement writes `delivery_failure_count` or `cycle_failure_count`.
2. Replace the `nack_event` docstring text as described in Details; leave every line after the closing quotes untouched.
3. Read the `NackResult` docstring; edit only wording that is stale, otherwise leave it unchanged.
4. Review `git diff` for this file and confirm it touches docstring text only.

### Method
- Use the Edit tool on the docstring lines only.
- Keep the summary line under the line-length limit of the repository's `ruff` configuration and in imperative or descriptive style matching neighboring docstrings.

### Details
- Summary line: record a per-consumer NACK failure for an event.
- Description points: per-consumer failure count and attempt marker are written only when a consumer is given; the events-level counters are left unmodified and returned as stored; an event already in the DLQ or already acked by this consumer is rejected without a write; the same attempt identifier is idempotent.
- Keep the existing "Returns NackResult with" bullet list, correcting only wording that implies the counters are incremented.

## Compatibility considerations
- Docstring only; no signature, return value, or behavior change.

## Security considerations
N/A: docstring only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/delivery_repo.py` before it is committed.

## Validation plan
- Run `uv run pytest tests/eventbus`, `ruff` (check and format), and `mypy` per `rules/toolchain.md`.
- Confirm by `git diff` that no executable line changed.

## Completion criteria
- The docstring no longer says events-level counters are incremented, and the diff is docstring text only.
- Tests, `ruff`, and `mypy` report no new failures.

## Out of scope
- Any executable change, other docstrings, the legacy columns, or the reference API document (handled by the next procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the nack_event docstring and check NackResult | Completed | 20261011-220342 | 20261011-220342 | — Docstring rewritten; NackResult docstring checked and left unchanged (not stale) |
| 2 | Add or update tests per Validation plan | Completed | 20261011-220342 | 20261011-220342 | N/A: docstring only N/A: docstring only |
| 3 | Run tests, ruff, and mypy; confirm the diff is docstring only | Completed | 20261011-220342 | 20261011-220342 | — tests/eventbus 333 passed 1 skipped; ruff and mypy clean; diff is docstring only |

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
- **Requirement ID**: `REQ-001` (nack_event docstring), `REQ-002` (NackResult check)
- **Source issue**: issues/20261011-215944_eb015nackdoc_correct-stale-nack_event-docstring-and-generated-reference-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-220109_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-220151
- **Related target files**: scripts/eventbus/delivery_repo.py