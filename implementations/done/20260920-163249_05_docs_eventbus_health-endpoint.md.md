## Goal
Replace the three flagged full JSON response examples (lines 34, 103, 131) in
`docs/eventbus/health-endpoint.md` with a description of the fields carrying
degradation semantics (`status`, `degraded_reasons`) and a pointer to
`scripts/eventbus/health_route.py`, per `REQ-005` (Plan `plans/20260920-160505_plan.md`),
so `tools/check_docs_content_policy.py` reports no finding at any of the three
locations while the "Field Descriptions" and "Possible Degraded Reasons" tables and
the two `curl` command examples remain unchanged.

## Scope
In scope: the three JSON code blocks at lines 34-51 (`### Response Schema`), 103-120
(`### Successful Health Check` response), and 131-148 (`### Degraded Health Check`
response) only. Out of scope: the "### Field Descriptions" table (lines 53-68), the
"### Possible Degraded Reasons" table (lines 80-90), and the two `curl` command blocks
(lines 96-98, 124-126) — none of these were flagged by `check_docs_content_policy.py`
(re-confirmed 2026-09-20). Also out of scope: the pre-existing missing `## Related
Documents`/`## Keywords` sections and missing `area`/`related` front-matter fields for
this file, recorded in the Plan as pre-existing structural findings.

## Assumptions
The three findings (lines 34, 103, 131) and the file's exact current content
(re-verified via Read during this document's creation) have not shifted since the Plan
was frozen — no commit has touched this file or `scripts/eventbus/health_route.py`
since.

## Design decisions
All three JSON examples show the same response shape (`status`, `db`, `dlq_task`,
`active_subscribers`, `max_queue_depth`, `slow_consumers`, `overflow_disconnects`,
`duplicate_connection_rejections`, `degraded_reasons`, `metrics.*`), already fully
enumerated by the untouched "### Field Descriptions" table. Replace each JSON block
with a short sentence naming only the two fields whose *value* carries the
success/degraded distinction (`status` and `degraded_reasons`), pointing to
`scripts/eventbus/health_route.py` for the complete schema — keep both `curl` command
examples exactly as-is (they illustrate the request/auth header shape, which is not
part of any flagged finding).

## Alternatives considered
- Collapse all three sections into one combined section with a single JSON-schema
  pointer: rejected — this would remove the `### Response Schema` / `### Successful
  Health Check` / `### Degraded Health Check` heading structure, which is not part of
  any Requirement and would be an unrequested restructuring.
- Remove the `curl` commands along with their JSON response examples: rejected — the
  `curl` commands are request-shape illustrations (how to call the endpoint with the
  auth header), not part of the flagged findings, and remain useful without the
  hardcoded response body.

## Implementation
### Target file
`docs/eventbus/health-endpoint.md`

### Procedure
1. Read lines 32-148 to confirm current content matches the Plan's recorded evidence.
2. Replace the JSON code block at lines 34-51 with one sentence: the response body's
   fields are described in "Field Descriptions" below; see
   `scripts/eventbus/health_route.py` for the exact JSON schema.
3. Replace the JSON code block at lines 103-120 (under "### Successful Health Check")
   with one sentence: returns `status: "ok"` with an empty `degraded_reasons` array
   when all subsystems are healthy — see `scripts/eventbus/health_route.py` for the
   full response schema.
4. Replace the JSON code block at lines 131-148 (under "### Degraded Health Check")
   with one sentence: returns `status: "degraded"` with a non-empty `degraded_reasons`
   array listing which conditions triggered the degraded state (see "Possible Degraded
   Reasons" above) — see `scripts/eventbus/health_route.py` for the full response
   schema.
5. Leave the "### Field Descriptions" table, the "### Possible Degraded Reasons"
   table, both `curl` command blocks, and every other line unchanged.

### Method
Three independently revertable `Edit` calls, one per flagged JSON block (steps 2, 3,
4). Do not touch the two `curl` command blocks or the two tables.

### Details
Do not restate any field name/value from the three removed examples beyond `status`
and `degraded_reasons` (already named in the replacement sentences for their
semantic role, not as a field/type listing) — `active_subscribers`, `max_queue_depth`,
`slow_consumers`, `overflow_disconnects`, `duplicate_connection_rejections`, and the
`metrics.*` fields are all already covered by the untouched "Field Descriptions"
table and are fully code-derivable from `scripts/eventbus/health_route.py`.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched` — the `Bearer ${MONITORING_TOKEN}`
placeholder in the retained `curl` examples is already a placeholder, not a real
credential, and is unaffected by this edit.

## Rollback considerations
Revert via `git checkout` on this one file. The three edits are independently
revertable from each other and from the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/eventbus/health-endpoint.md` (Plan `AC-5`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/eventbus/health-endpoint.md` —
  confirm the finding count does not exceed the pre-existing findings (missing `##
  Related Documents`/`## Keywords`, missing `area`/`related` front matter) already
  recorded in the Plan.

## Completion criteria
None of the three flagged JSON response examples remains; each is replaced by a
sentence naming only `status`/`degraded_reasons`'s semantic role and pointing to
`scripts/eventbus/health_route.py`; the "Field Descriptions" table, "Possible Degraded
Reasons" table, and both `curl` examples are unchanged; `check_docs_content_policy.py`
reports zero findings for this file.

## Out of scope
- The "Field Descriptions" and "Possible Degraded Reasons" tables, and both `curl`
  command blocks (see Scope) — not flagged, not part of `REQ-005`.
- The pre-existing missing `## Related Documents`/`## Keywords` sections and missing
  `area`/`related` front-matter fields — tracked in the Plan as pre-existing,
  out-of-scope structural findings.
- Any other `docs/*.md` file — this is the last of the Plan's five target-file rows.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-171726 | 20260920-171726 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-171726 | 20260920-171726 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-171726 | 20260920-171726 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-171726 | 20260920-171726 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-005` — replace the healthy/degraded JSON response examples with a fields description and pointer
- **Source issue**: issues/20260920-154603_dcp012_eventbus-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163249
- **Related target files**: docs/eventbus/health-endpoint.md