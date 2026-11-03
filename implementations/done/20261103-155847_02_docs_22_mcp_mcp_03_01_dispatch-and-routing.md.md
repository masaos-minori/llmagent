## Goal

Extend the "Idempotency and retry" section of `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` so it names the Agent-audit logical idempotency key and states how it differs from the transport `X-Idempotency-Key`, preventing a reader from conflating the two (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **A1**: The audit key (`workflow_id:task_id:turn_id:call_id`) and the transport `X-Idempotency-Key` are two distinct keys established by `toolstate001` (REQ-003/D3, REQ-009); this document describes the split without changing either key's derivation or ownership.
- **A2**: The existing transport-key description in the section must remain unchanged; only an audit-key sentence is added.

## Design decisions
- **DD-1 — Where the correction goes.** Add one sentence at the start of the "Idempotency and retry" section naming the audit-side logical key and its distinction from the transport `X-Idempotency-Key`. This places the disambiguation where the reader first meets the section, before the transport-key bullets.

## Alternatives considered
- Add the audit-key sentence at the end of the section. Rejected: placing it at the head prevents the conflation before the transport-key details are read.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
Insert one sentence at the beginning of the "Idempotency and retry" section, immediately after the existing opening paragraph and before the bullet list, naming the Agent-audit logical key and distinguishing it from the transport `X-Idempotency-Key`.

### Method
In `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, locate the "Idempotency and retry" heading (currently around line 57). The section opens with:
```markdown
The `X-Idempotency-Key` request header gives a logical call a stable identity on the server: it drives server-side de-duplication of state-mutating calls and lets the Agent reuse one key across that call's retries.
```
Append the following sentence directly after that paragraph (leave the transport-key paragraph and the entire bullet list below it unchanged):
```markdown
In addition to this transport key, the Agent also records a separate audit-side key in the `tool_exec` event's `idempotency_key` field — the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`) — which identifies the logical call for the audit log and is **not** used for server-side de-duplication.
```

### Details
- The audit key comes from `tool_runner.py::_idempotency_key` (`:133-141`) → `audit_tool_exec(..., idempotency_key=...)` (`:273-284`); the transport key is derived/emitted in `http_transport.py` (`:62`, `:193-203`) and consumed by the dispatcher's dedup cache. This sentence makes that split explicit in the doc.
- Do not reword or reorder any existing sentence in the section; the transport-key description must stay byte-for-byte as written.

## Compatibility considerations
Documentation-only change; no code or behavior impact.

## Security considerations
N/A: the change clarifies documentation; it does not alter key derivation, storage, or comparison.

## Rollback considerations
N/A: revert the added sentence.

## Validation plan
- Doc checkers run clean: `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_consistency.py --domain mcp`.
- Confirm the transport-key paragraph and bullet list are unchanged and the audit-key sentence is present.

## Completion criteria
- The "Idempotency and retry" section names the Agent-audit logical key (`workflow_id:task_id:turn_id:call_id`) and states it is distinct from the transport `X-Idempotency-Key`.
- The existing transport-key description is unchanged.

## Out of Scope
- Changing the transport `X-Idempotency-Key` description, the empty-key rule, cache keying, TTL/eviction, or write-tool retry behavior.
- Any other section of the doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend "Idempotency and retry" in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Completed | 20261103 | 20261103 | doc-only; transport-key description unchanged |
| 2 | Add or update tests per Validation plan | Completed | 20261103 | 20261103 | N/A: doc-only, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103 | 20261103 | doc checkers clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103 | 20261103 | N/A |

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
- **Requirement ID**: `REQ-002` — extend the dispatch doc's "Idempotency and retry" section to name the audit-side logical key and distinguish it from the transport `X-Idempotency-Key`
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-155847
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
