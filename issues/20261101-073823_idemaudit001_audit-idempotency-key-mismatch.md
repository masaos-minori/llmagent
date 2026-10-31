# The idempotency key written to the audit log is not the key sent to the MCP server

## Priority
Medium

## Summary
`tool_runner` derives a "stable, retry-invariant" idempotency key (`workflow_id:task_id:turn_id:call_id`) for every tool call and writes it into the `tool_exec` audit event. That key never reaches the transport: `HttpTransport.call` generates its own random UUID per call and sends that as `X-Idempotency-Key`. The audit field therefore names a key the server has never seen, and its documented property (stable across retries of the same call) does not hold for the key that actually protects the write. Give the key one owner so that the audit record and the wire agree.

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- `tool_runner._idempotency_key` builds the derived key and `execute_one_tool_call` passes it only to `audit_tool_exec`. `ToolExecutor.execute`, `ToolTransportInvoker.invoke` and `HttpTransport.call` do not accept a key from the caller.
- `HttpTransport.call` creates `uuid.uuid4()` once per logical call and reuses it on its internal HTTP retries; the server's duplicate cache (`mcp_servers/dispatch.py`) keys on that header.
- The audit model (`agent/shared/models.py`, `ToolExecEvent.idempotency_key`) describes the field as a stable, retry-invariant key for deduplication.
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` documents the transport-generated key and its reuse across retries of one call. No document describes the derived key.
- The archived issue `issues/done/20261007-153753_idem01_fix-mcp-idempotency-cache-and-retry-coupling.md` set the contract "the caller owns key generation, one key per logical call, reused across retries of that call"; the transport-generated key satisfies it. The derived key was added later for the audit event.
- The audit event does carry `mcp_request_id` (the response's request id), so a record can still be joined to the server's record by that field.

## Problem
Evidence (`Explicit in code`; no run was needed): the derived key's only consumer is `audit_tool_exec`, and the header value is created inside `HttpTransport.call`. The two values are unrelated.

Effects:
- Anyone searching the server's audit or access data for the audit event's `idempotency_key` finds nothing, and anyone searching for a header value finds no agent record.
- The audit field suggests that a repeated logical call (the same call id replayed) is deduplicated by that key; it is not. A call replayed with the same id would get a new random key and execute again.
- Two keys with the same name and different meanings invite a future change to rely on the wrong one.

## Reason for Change
The key is part of the audit trail for state-changing calls, where the question "was this the same call or a second one?" is the point of recording it. At present the record cannot answer it. The cost of fixing it is small and it is cheaper before anything depends on the field.

## Implementation Intent
Decide one owner for the key. Either the agent supplies the derived key down the call chain and the transport uses it for the header (keeping one UUID-or-derived value per logical call), or the transport reports the key it used back in the result and the audit event records that value. In both cases the audit field must be the value sent on the wire, the server contract from the archived idempotency issue must stay unchanged, and the field's description must say which semantics it has.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (`_idempotency_key`, `execute_one_tool_call`)
- `scripts/shared/http_transport.py` (`HttpTransport.call`)
- `scripts/shared/tool_transport_invoker.py`, `scripts/shared/tool_executor.py` (call chain, if the key is passed down)
- `scripts/shared/transport_dto.py` (`ToolCallResult`, if the key is returned)
- `scripts/agent/shared/models.py` (`ToolExecEvent.idempotency_key` description)
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
- `tests/agent/`, `tests/shared/` tests for the audit event and the transport header

## Required Changes
- Make the value in the audit event equal to the `X-Idempotency-Key` header sent for that call.
- Update the field description to state the actual semantics (scope: one logical call and its transport retries, or wider if the derived key is adopted).
- Add tests: the audit event's key equals the header captured by a mock transport; retries within one call reuse it; two different calls get different keys.
- Update the MCP dispatch documentation to describe the key's origin.

## Constraints
- Keep the server-side cache contract (key plus tool name plus argument hash, reuse with different content rejected).
- If a derived key is sent, it must not exceed what the server accepts for a key and must not leak secrets (it contains ids only).
- Do not change retry behavior, including the fail-closed rules for write tools.

## Acceptance Criteria
- For every executed call, the `idempotency_key` in the `tool_exec` audit event equals the value sent in `X-Idempotency-Key`.
- The documentation states who generates the key and what it identifies.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests with `httpx.MockTransport` capturing request headers, and a stub audit logger capturing the event.
- Regression: run the tool runner, transport, and audit tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Update `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` (key ownership) to name the single source of the key and its scope. Describe intent only.

## Out of Scope
- The server duplicate cache and its eviction.
- Replaying calls after a restart or reconciling in-flight calls.
- Other audit fields.

## Dependencies
N/A: none. `issues/done/20261007-153753_idem01_fix-mcp-idempotency-cache-and-retry-coupling.md` is archived background. `issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md` concerns repeated writes after an interrupted call and would benefit from this key being stable across a replay, but neither issue blocks the other.

## Unresolved Questions
- Which design is wanted: a derived key that also deduplicates a replay of the same call id, or the transport's per-call key reported back: a design choice for the owner.
- Whether any consumer reads the audit `idempotency_key` today: `Needs confirmation`; none was found in `scripts/` (not searched in operational tooling outside the repository).

## AI Implementation Instruction
Write the failing equality test first. Change only how the key is passed or reported, the field description, the documentation, and tests. Do not change the server cache, retry rules, or other audit fields. Stop and report if adopting the derived key would require a server change.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073823
- **Related target files**: scripts/agent/tool_runner.py, scripts/shared/http_transport.py, scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py, scripts/shared/transport_dto.py, scripts/agent/shared/models.py, docs/22_mcp/mcp_03_01_dispatch-and-routing.md
