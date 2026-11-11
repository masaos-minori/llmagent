## Goal

Document, in `docs/24_eventbus/eventbus_10_health_endpoint.md`, the two new `/health` response fields (`terminal_failed_outbox`, `last_dlq_sweep`) and the two new degraded reasons (`dlq_outbox_failed`, `dlq_sweep_failing`), each with its description and its placement under the existing 503-for-any-degraded rule and outside the liveness/readiness gate (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The sibling route change (`scripts/eventbus/health_route.py`, seq 03) adds `terminal_failed_outbox` (int, count of `dlq_outbox.status='failed'` rows; `None` on count-query failure) and `last_dlq_sweep` (`{"result": str, "time": str | None}`) to the response body, and appends `dlq_outbox_failed` when the count is `> 0` and `dlq_sweep_failing` when `last_result == "failed"`.
- `last_dlq_sweep.result` is `"ok"` / `"failed"` / `"not_run"` and `time` is an ISO-8601 string or `None` (recorded by `scripts/eventbus/app.py`, seq 02).
- The two new reasons are ordinary entries in `degraded_reasons`, so they yield HTTP 503 exactly like every other reason and do not touch `liveness`/`readiness`.

## Design decisions
- Add the two reasons to the existing "Possible Degraded Reasons" table and the two fields to the documented response body, mirroring the style of the existing rows.
- State explicitly that both reasons are real failures (HTTP 503) but are outside the deployment readiness gate, consistent with the existing capacity-only reasons.

## Alternatives considered
- Adding a new top-level section for the outbox reasons: rejected — they belong with the other degraded reasons in the existing table; a separate section would misrepresent them as a different category.

## Implementation
### Target file
`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure
1. "Possible Degraded Reasons" table (lines 52-61): append two rows for `dlq_outbox_failed` and `dlq_sweep_failing`.
2. Document the two new response fields, either in the "Response Content" summary (line 36) or a short "New Fields" subsection near "Health Tiers".
3. Note that both reasons are real failures (503) but outside the liveness/readiness gate.
4. Do not alter the tier definitions, metric sections, or other documents.

### Method
1. Append to the "Possible Degraded Reasons" table:
| `dlq_outbox_failed` | Terminal-failed `dlq_outbox` rows exist (count > 0); reported via `terminal_failed_outbox` |
| `dlq_sweep_failing` | The last `_dlq_loop` cycle returned `"failed"`; reported via `last_dlq_sweep.result` |

2. In "Response Content" (after the mention of `degraded_reasons`), add:
> The body also reports `terminal_failed_outbox` (the count of terminal-failed `dlq_outbox` rows, or `null` if the count query failed) and `last_dlq_sweep` (`{"result": "ok" | "failed" | "not_run", "time": <ISO-8601 str | null>}`), reflecting the last background sweep cycle.

3. Under "Health Tiers" (or a new "New Degraded Reasons" note), add:
> `dlq_outbox_failed` and `dlq_sweep_failing` are real failures: each returns HTTP 503 like every other degraded reason, but neither changes `liveness` or `readiness`. They are not capacity-only reasons; they indicate a genuine DLQ problem (stuck failed events or a repeatedly failing sweep).

### Details
- `terminal_failed_outbox` is `null` when the count query raised `sqlite3.Error`; in that case the route reports `db_unavailable` instead and omits the reason (see seq 03).
- `last_dlq_sweep.result == "not_run"` (before any sweep in this process) does not fire `dlq_sweep_failing`.
- Keep the descriptions terse and parallel to the existing rows.

## Compatibility considerations
- Documentation-only. No other Plan targets `eventbus_10`; `check_docs_consistency.py --domain eventbus` must pass.

## Security considerations
- None: operational telemetry documentation only.

## Rollback considerations
- N/A: revert the commit; the edit is localized to this document.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `dlq_outbox_failed` and `dlq_sweep_failing` appear in the "Possible Degraded Reasons" table with descriptions.
- `terminal_failed_outbox` and `last_dlq_sweep` are documented as response fields.
- Both reasons are stated to return HTTP 503 while leaving `liveness`/`readiness` unchanged.
- `check_docs_consistency.py --domain eventbus` passes.

## Out of Scope
- The route change that produces these fields/reasons — sibling procedure (`scripts/eventbus/health_route.py`, seq 03).
- Recording the sweep result on `app.state` — sibling procedure (`scripts/eventbus/app.py`, seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` — document the new `/health` outbox/sweep fields and degraded reasons
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`
