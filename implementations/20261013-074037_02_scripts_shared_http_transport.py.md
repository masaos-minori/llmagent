## Goal

Clarify in `HttpTransport.call` that its retry loop performs multiple HTTP attempts
without re-entering the per-logical-call gates, so readers do not assume the
health/lifecycle/semaphore gates run once per attempt.

## Scope

- **In-Scope**: Add a comment in `scripts/shared/http_transport.py` inside `call`, near
  the retry loop (lines 163-217), stating that the loop performs multiple HTTP attempts
  without re-entering the pre-call gates.
- **Out-of-Scope**: Any change to the retryable-status set, exponential backoff
  (`2**attempt`), `_RETRY_MAX`, headers, or the idempotency-key logic.

## Assumptions

- Option (a) (document-and-assert) is the intended resolution; the change is purely
  additive.
- The per-logical-call model is already enforced by `ToolTransportInvoker`
  (`_run_precall_gates` runs the gates once); this comment records that invariant at the
  point where the retries actually happen.

## Design decisions

- **Additive only**: a comment carries no runtime effect, so it cannot alter the retry
  loop, backoff, or exhaustion behavior; it only documents what the code already does.
- **Place it at the retry loop** (not in `call`'s docstring) so the non-re-entry claim
  sits next to the code that performs the attempts, where a future reader is most likely
  to look.

## Alternatives considered
N/A: option (b) (per-attempt re-check) is explicitly rejected by the Plan as
non-minimal and semantically inconsistent; this document only records the resolved
option (a).

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
1. Open `HttpTransport.call` (lines 143-218).
2. Locate the retry-loop entry at line 163: `for attempt in range(self._RETRY_MAX):`.
3. Insert a comment immediately above line 163 (after the `last_retryable_status`
   declaration at line 162) stating that the loop performs multiple HTTP attempts and
   does NOT re-enter the pre-call gates on retry.
4. Do not modify any executable line, the `call` docstring, headers, or the
   idempotency-key block (lines 150-153).

### Method
One comment insertion inside `call`; no new symbols, imports, or behavioral change.

### Details
Current context around the retry-loop entry (lines 161-163):
```python
        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_retryable_status: int | None = None
        for attempt in range(self._RETRY_MAX):
```
Proposed:
```python
        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_retryable_status: int | None = None
        # Per-logical-call gating: this loop may issue multiple HTTP attempts
        # (retryable statuses in _RETRYABLE_STATUS, up to _RETRY_MAX=3) but each
        # attempt reuses the single idempotency key above and does NOT re-enter
        # the pre-call gates. The health/lifecycle/semaphore gates run once per
        # logical call in ToolTransportInvoker._run_precall_gates; they are not
        # re-evaluated between these attempts. See REQ-002.
        for attempt in range(self._RETRY_MAX):
```
Evidence the claim matches control flow: the loop (lines 163-217) calls
`self._http.post` and either `continue`s on a retryable status or returns/raises; no
gate re-invocation occurs inside it. Gates live in
`tool_transport_invoker.py::_run_precall_gates` (lines 231-278), which calls
`transport.call` exactly once per logical call.

## Compatibility considerations
N/A: comment-only change; no caller-visible contract or behavior change.

## Security considerations
N/A: no secret handling touched; the comment references the idempotency key (REQ-005)
that makes the multi-attempt write retry safe via server-side dedup.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Static lint/type | `uv run ruff check scripts/shared` · `uv run mypy --no-namespace-packages scripts/shared` | clean |
| `scripts/shared/` | Shared-module suite | `uv run pytest tests/shared/` | no new failures |

## Completion criteria
The comment near the retry loop states that multiple HTTP attempts do not re-enter the
pre-call gates, and `ruff`, `mypy`, and the shared-module suite pass.

## Out of scope
`scripts/shared/tool_transport_invoker.py` (REQ-001), the test (REQ-003), and any
retry/backoff or health-failure-counting change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document retry-loop non-re-entry in `call` (`http_transport.py`) | Pending | — | — | REQ-002 |
| 3 | Run ruff/mypy/shared-suite validation | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: structural non-issue | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (clarify retry-loop non-re-entry in `call`)
- **Source issue**: `issues/20261012-185100_mcp002_health-and-lifecycle-gates-run-once-per-logical-call-not-per-http-retry-in-mcp-transport.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-223034_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-074037
- **Related target files**: `scripts/shared/http_transport.py`
