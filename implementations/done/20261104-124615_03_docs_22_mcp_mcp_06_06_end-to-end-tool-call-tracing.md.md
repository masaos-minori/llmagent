## Goal
- Correct the audit-trace document's description of the `tool_exec` record's `idempotency_key` and its example line, so they describe the workflow-scoped logical-call identity instead of the transport key (`REQ-003`: remove the claim that the audit key is the dispatched key and matches the store and `tool_call_state` rows).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one paragraph and the `idempotency_key` value of one example line in `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`. This row was added to the Plan by an owner-approved scope amendment on 2026-11-04.

## Assumptions
- The audit value is `{workflow_id}:{task_id}:{turn_id}:{call_id}`, built for the audit event only; the key the call is dispatched under is the transport `X-Idempotency-Key`, and the durable store and the `tool_call_state` row use the transport-derived key (checked in Step 3a against the runner, the transport, and the db dedup document).
- The document already explains how to follow one call: join on `mcp_request_id` (its first section); the corrected paragraph points there instead of describing another join.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Replace the paragraph rather than append a note, because the sentence "the key the call was dispatched under" is itself the error.
- Keep the example line otherwise unchanged and change only the `idempotency_key` value to a synthetic workflow-scoped value, so the other fields stay as documented.

## Alternatives considered
N/A: two bounded text edits; the Plan's `REQ-003` fixes the required content.

## Implementation
### Target file
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`

### Procedure
1. In the section "Idempotency and Dedup Fields in the Audit Trace", replace the two-line paragraph that starts with `The record also carries` and ends with `` the workflow `tool_call_state` row. `` by the paragraph below.
2. In the example line of the same section, replace the value of the `idempotency_key` key (a 64-character hex string) with `wf-0001:task-0001:turn-0001:call-0001`.

### Method
New paragraph (English, one paragraph, no file or function names):

```text
The record also carries `idempotency_key`: the workflow-scoped logical-call identity (workflow, task, turn, and call id joined by colons) that the Agent derives for the audit log. It is not the `X-Idempotency-Key` the call was dispatched under, and it is neither the durable store row's key nor the workflow `tool_call_state` row's key, so it cannot be used to match an audit line against those rows. To follow one call, join on `mcp_request_id` as described at the top of this document.
```

### Details
- Do not edit the table above the paragraph, the `error_type` paragraph, the snapshot paragraph, or any other field of the example line.
- The example stays marked as synthetic values.

## Compatibility considerations
N/A: documentation only; no behavior, API, or reference-table change.

## Security considerations
N/A: the new value in the example is synthetic and names no real workflow, task, or token.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `rg -n "the key the call was dispatched under" docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` returns nothing, and the example line's `idempotency_key` value contains colons and no 64-character hex string.
- `git diff -U0 docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` shows changes only in that paragraph and in that one value.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` report no findings.

## Completion criteria
- The section names the workflow-scoped logical-call identity, states that it is not the dispatched transport key and not the stored key, and no longer says it matches the durable store or `tool_call_state` row (`AC-3`).
- The example line shows a workflow-scoped `idempotency_key` and the docs checkers are clean.

## Out of Scope
- Changing which key the audit event records, the dedup fields table, the snapshot or `error_type` text, and any other document.
- The dispatch-and-routing document and the code comment (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the paragraph and the example value as described in Implementation > Procedure/Method | Completed | 20261104-130522 | 20261104-130535 | Changed: docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md (one paragraph and one example value). Step 2 stale check: clean. Procedure target is the doc itself, so the edit is Step 3d; Step 5 N/A |
| 2 | Run the documentation checkers and the search in the Validation plan | Completed | 20261104-130535 | 20261104-130610 | Search for the old wording returns nothing; example idempotency_key is workflow-scoped; diff has two hunks only; check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_docs_consistency --domain mcp, fast gates: pass. Step 4 N/A: documentation-only, no tests in Validation plan |

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
- **Requirement ID**: `REQ-003` (audit-trace doc describes the audit key as the logical-call identity, not the dispatched key)
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-124615
- **Related target files**: `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`