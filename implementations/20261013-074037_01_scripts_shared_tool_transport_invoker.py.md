## Goal

Make the per-logical-call gate model explicit in `ToolTransportInvoker`: document that the
pre-call gate chain in `_run_precall_gates` runs exactly once per logical call and that
in-call HTTP retries inside `HttpTransport.call` intentionally bypass these gates.

## Scope

- **In-Scope**: Expand the docstring of `_run_precall_gates` and add a clarifying note to
  the docstring of `invoke` in `scripts/shared/tool_transport_invoker.py` stating that the
  gate chain runs once per logical call and that in-call HTTP retries bypass the gates.
- **Out-of-Scope**: Any behavioral change to the gate chain, retry loop, exponential
  backoff (`2**attempt`), `_RETRY_MAX`, or health-failure counting.

## Assumptions

- Option (a) (document-and-assert) is the intended resolution; the change is purely
  additive docstrings/comments.
- The per-logical-call model is already enforced by existing code (single HALF_OPEN trial,
  per-call semaphore), so the docstring records reality rather than introducing a contract.

## Design decisions

- **Additive only**: docstrings/comments carry no runtime effect, so this cannot alter the
  retry loop, gate ordering, or health-failure counting; the behavior it describes is
  already what the code does.
- **Anti-misread wording**: the docstrings must state explicitly that gates run ONCE per
  logical call and that retries BYPASS them, so future readers do not infer per-attempt
  re-checking (option (b)).

## Alternatives considered
N/A: option (b) (per-attempt re-check) is explicitly rejected by the Plan as non-minimal
and semantically inconsistent; this document only records the resolved option (a).

## Implementation
### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
1. Open `ToolTransportInvoker._run_precall_gates` (lines 231-278) and expand its
   docstring (currently line 237: `"""Run the pre-call gate chain: health → disabled →
   lifecycle → transport → semaphore → dispatch."""`).
2. Add one sentence stating that this gate chain runs exactly once per logical call and
   that subsequent HTTP retries inside `HttpTransport.call` do NOT re-enter these gates
   (they are intentionally bypassed on retry).
3. Open `ToolTransportInvoker.invoke` (lines 280-287) and extend its docstring (currently
   line 286: `"""Invoke tool via transport; applies health check, lifecycle, semaphore,
   and recording."""`) with a note that the gates apply once at this boundary; in-call
   retries inside `HttpTransport.call` do not re-run them.
4. Do not modify any method body, signature, or the gate chain logic.

### Method
Two docstring edits inside `tool_transport_invoker.py`; no new symbols, imports, or
behavioral change.

### Details
Current `_run_precall_gates` docstring (line 237):
```python
        """Run the pre-call gate chain: health → disabled → lifecycle → transport → semaphore → dispatch."""
```
Proposed:
```python
        """Run the pre-call gate chain once per logical call: health → disabled →
        lifecycle → transport → semaphore → dispatch.

        The chain runs exactly once per logical call. In-call HTTP retries inside
        HttpTransport.call (the retry loop in scripts/shared/http_transport.py::call)
        intentionally bypass these gates; they are NOT re-evaluated between attempts.
        Per-logical-call gating is enforced by the single HALF_OPEN trial
        (_check_health) and the per-call semaphore (_execute_with_semaphore)."""
```
Current `invoke` docstring (line 286):
```python
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
```
Proposed:
```python
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and
        recording exactly once per logical call. In-call HTTP retries inside
        HttpTransport.call do not re-enter these gates."""
```
Evidence the claim matches control flow: `_run_precall_gates` (lines 231-278) runs the
chain then delegates via `_invoke_and_record` (line 269) → `_execute_with_semaphore`
(line 204) → `transport.call`; the retry loop lives entirely in
`http_transport.py::call` (lines 163-217). Importer `tool_executor.py::_raw_execute`
(line 88) returns `self._run_precall_gates(...)`.

## Compatibility considerations
N/A: docstring-only change; no caller-visible contract or behavior change.

## Security considerations
N/A: no secret handling or security-relevant behavior touched; the comment clarifies that
per-logical-call gating (fail-closed on writes) is a single-trial property.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_transport_invoker.py` | Static lint/type | `uv run ruff check scripts/shared` · `uv run mypy --no-namespace-packages scripts/shared` | clean |
| `scripts/shared/` | Shared-module suite | `uv run pytest tests/shared/` | no new failures |

## Completion criteria
`_run_precall_gates` and `invoke` docstrings state that the gate chain runs once per
logical call and that in-call retries bypass the gates, and `ruff`, `mypy`, and the
shared-module suite pass.

## Out of scope
`scripts/shared/http_transport.py` (REQ-002), the test (REQ-003), and any retry/backoff or
health-failure-counting change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document per-logical-call gating in `_run_precall_gates`/`invoke` (`tool_transport_invoker.py`) | Pending | — | — | REQ-001 |
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
- **Requirement ID**: `REQ-001` (document per-logical-call gating in `_run_precall_gates`/`invoke`)
- **Source issue**: `issues/20261012-185100_mcp002_health-and-lifecycle-gates-run-once-per-logical-call-not-per-http-retry-in-mcp-transport.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-223034_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-074037
- **Related target files**: `scripts/shared/tool_transport_invoker.py`
