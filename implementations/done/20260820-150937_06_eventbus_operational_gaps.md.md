# Implementation Procedure: Document EventBus operational-lifecycle gaps as explicit known issues

## Goal
Add five new entries (`EVENTBUS-008` through `EVENTBUS-012`) to `docs/06_eventbus_90_inconsistencies_and_known_issues.md` documenting currently unimplemented EventBus operational-lifecycle mechanisms (retention/capacity, DLQ file retention, consumer-ID lifecycle, slow-consumer recovery, API schema canonicity), and add a one-sentence cross-reference to the relevant new entry in each of the five related EventBus doc files — with zero changes to any `.py` file or CI workflow.

## Goal
Add five new entries (`EVENTBUS-008` through `EVENTBUS-012`) to `docs/06_eventbus_90_inconsistencies_and_known_issues.md` documenting currently unimplemented EventBus operational-lifecycle mechanisms (retention/capacity, DLQ file retention, consumer-ID lifecycle, slow-consumer recovery, API schema canonicity), and add a one-sentence cross-reference to the relevant new entry in each of the five related EventBus doc files — with zero changes to any `.py` file or CI workflow.

## Scope
- Target files:
  - `docs/06_eventbus_90_inconsistencies_and_known_issues.md` — add 5 new entries
  - `docs/06_eventbus_03_persistence_schema_and_replay.md` — cross-reference to `EVENTBUS-008`
  - `docs/06_eventbus_05_06_dlq-operations.md` — cross-reference to `EVENTBUS-009`
  - `docs/06_eventbus_05_04_consumer-id-stability.md` — cross-reference to `EVENTBUS-010`
  - `docs/06_eventbus_02_03_nack-health-dlq.md` — cross-reference to `EVENTBUS-011`
  - `docs/06_eventbus_06_02_reference-api-route-handlers.md` — cross-reference to `EVENTBUS-012`

## Assumptions
- The `EVENTBUS-NNN` numbering is a flat, file-wide sequence; continuing from `EVENTBUS-007` to `EVENTBUS-008..012` is correct
- "Severity/status tag" style `(Medium/open)`, `(Low/deferred)` is the only tag convention in this file
- The five cross-reference target files' "Related Documents" list is a Markdown bullet list; adding one sentence near it satisfies the requirement
- No changes to any file under `scripts/eventbus/` (Global Rule 8)

## Design decisions
- Place all 5 new entries under a new subsection within "保留中" (deferred), titled to group them as operational-lifecycle gaps
- Each entry tagged `(Medium/deferred)` except API-schema entry (`EVENTBUS-012`) which is `(Low/deferred)`
- Cross-reference sentences added to each target file's existing "Related Documents" area as a plain sentence

## Implementation steps
1. **Preparation**: immediately before editing, re-run `grep -n "EVENTBUS-0" docs/06_eventbus_90_inconsistencies_and_known_issues.md` to confirm `008`-`012` are still unclaimed; renumber if a collision is found.

2. **Core edit 1**: edit `docs/06_eventbus_90_inconsistencies_and_known_issues.md` — add the new "保留中" subsection with the five `EVENTBUS-008`..`012` entries.

3. **Core edit 2**: edit `docs/06_eventbus_03_persistence_schema_and_replay.md` — add the one-sentence cross-reference for `EVENTBUS-008`.

4. **Core edit 3**: edit `docs/06_eventbus_05_06_dlq-operations.md` — add the cross-reference for `EVENTBUS-009`.

5. **Core edit 4**: edit `docs/06_eventbus_05_04_consumer-id-stability.md` — add the cross-reference for `EVENTBUS-010`.

5. **Core edit 5**: edit `docs/06_eventbus_02_03_nack-health-dlq.md` — add the cross-reference for `EVENTBUS-011`.

6. **Core edit 6**: edit `docs/06_eventbus_06_02_reference-api-route-handlers.md` — add the cross-reference for `EVENTBUS-012`.

7. **Verification**: run the validation commands in Validation plan below.

## Entry details

### EVENTBUS-008: Retention / purge / DB capacity (WAL/VACUUM/disk) undefined
- **Severity/status**: Medium/deferred
- **Description**: No retention window, purge routine, or `VACUUM`/disk-space check exists in `scripts/eventbus/db.py`; events persist indefinitely in SQLite and in the JSONL archive. Resolving this requires code changes forbidden by `AGENTS.md` Global Rule 8.

### EVENTBUS-009: DLQ file retention undefined
- **Severity/status**: Medium/deferred
- **Description**: DLQ JSON files written by `scripts/eventbus/dlq.py` (`_atomic_write`) under `{deadletter_dir}` are never deleted or expired by any code path. Resolving this requires code changes forbidden by `AGENTS.md` Global Rule 8.

### EVENTBUS-010: Consumer-ID expiration / reuse / offset cleanup undefined
- **Severity/status**: Medium/deferred
- **Description**: Consumer IDs and their offset files (`scripts/eventbus/offsets.py`) persist indefinitely with no expiration, ownership, or cleanup logic. Distinct from the already-documented lack of collision detection (`06_eventbus_05_04_consumer-id-stability.md`). Resolving this requires code changes forbidden by `AGENTS.md` Global Rule 8.

### EVENTBUS-011: Slow-consumer recovery undefined (detection only)
- **Severity/status**: Medium/deferred
- **Description**: Slow-consumer *detection* exists (`EventBroker.slow_consumer_count()` in `scripts/eventbus/broker.py`, surfaced as `slow_consumers_detected` in `health_route.py`), but no automatic or manual recovery procedure (disconnect/backpressure/reset) or sequence diagram exists. Any recovery design work is blocked pending a policy change to Global Rule 8.

### EVENTBUS-012: API schema canonicity / CI drift detection undefined
- **Severity/status**: Low/deferred
- **Description**: No Pydantic request/response models or `response_model` annotations exist in any `scripts/eventbus/*_route.py` file, so the FastAPI-generated OpenAPI schema is not a deliberately designed contract. Making OpenAPI canonical, generating/validating Markdown against it, and adding CI schema-drift detection are all blocked for the same reason as EVENTBUS-011.

## Cross-reference sentences

1. `docs/06_eventbus_03_persistence_schema_and_replay.md`: "Note that retention/purge/capacity policy is an open gap, see `EVENTBUS-008` in `06_eventbus_90_inconsistencies_and_known_issues.md`."
2. `docs/06_eventbus_05_06_dlq-operations.md`: "Note DLQ file retention is undefined, see `EVENTBUS-009`."
3. `docs/06_eventbus_05_04_consumer-id-stability.md`: "Note consumer-ID expiration/cleanup is undefined (distinct from the collision-detection gap already documented on this page), see `EVENTBUS-010`."
4. `docs/06_eventbus_02_03_nack-health-dlq.md`: "Note slow-consumer recovery is undefined beyond detection, see `EVENTBUS-011`."
4. `docs/06_eventbus_06_02_reference-api-route-handlers.md`: "Note API schema canonicity/CI drift detection is undefined, see `EVENTBUS-012`."

## Validation plan
- Entry count/format check: `grep -n "^### EVENTBUS-" docs/06_eventbus_90_inconsistencies_and_known_issues.md` — shows `EVENTBUS-001` through `EVENTBUS-012` with no gaps or duplicates
- Diff scope: `git diff --stat` — only `docs/06_eventbus_*.md` files changed
- Factual accuracy: Re-verify each new entry's claim against source files
- Cross-references: `grep -n "EVENTBUS-0" docs/06_eventbus_03_persistence_schema_and_replay.md docs/06_eventbus_05_06_dlq-operations.md docs/06_eventbus_05_04_consumer-id-stability.md docs/06_eventbus_02_03_nack-health-dlq.md docs/06_eventbus_06_02_reference-api-route-handlers.md` — each file shows exactly one reference to its assigned ID
- Global Rule 8 compliance: `git diff --name-only | grep -E '^scripts/eventbus/|^\.github/workflows/'` — empty output

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-222438_require.md
- Source plan: plans/20260819-180452_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-150937
- Related target files: docs/06_eventbus_90_inconsistencies_and_known_issues.md, docs/06_eventbus_03_persistence_schema_and_replay.md, docs/06_eventbus_05_06_dlq-operations.md, docs/06_eventbus_05_04_consumer-id-stability.md, docs/06_eventbus_02_03_nack-health-dlq.md, docs/06_eventbus_06_02_reference-api-route-handlers.md