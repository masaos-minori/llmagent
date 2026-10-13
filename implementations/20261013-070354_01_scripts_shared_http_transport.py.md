## Goal

Correct the unreachable write-retry guard in `HttpTransport.call` so the code's comment
matches the behavior it actually enforces: writes are always retried on a non-timeout
`httpx.RequestError`, with deduplication safety resting on the always-active server-side
`_duplicate_cache`.

## Scope

- **In-Scope**: Remove the dead `if name in _WRITE_TOOLS and not idempotency_key:` branch
  and its REQ-006 comment from the `RequestError` handler in `HttpTransport.call`; replace
  them with a comment documenting the always-retry policy. Preserve the single-per-call key
  and the `X-Idempotency-Key` header.
- **Out-of-Scope**: Any change to `dispatch.py` server-side dedup, the retryable-status set,
  non-MCP HTTP calls, or the `X-Idempotency-Key` header contract.

## Assumptions

- The always-retry policy (Plan option (b)) is the intended design; removing the branch is
  behavior-preserving.
- `idempotency_key` is always a non-empty string, so the guard is provably unreachable.

## Design decisions

- **Behavior preservation**: the removed branch could never execute (`idempotency_key =
  str(uuid.uuid4())` at line 153 is always truthy), so deleting it cannot change observable
  retry counts; the behavior-preserving nature is confirmed characterization-style by the
  companion test's exact attempt counts.
- **Document over gate**: option (b) (explicit always-retry comment) is chosen over option
  (a) (emit the key only for write tools) because (a) would alter the `X-Idempotency-Key`
  header contract that `_duplicate_cache` relies on for all-tool deduplication.

## Alternatives considered

N/A: option (a) is ruled out by the Plan's constraint forbidding changes to the
`X-Idempotency-Key` header contract; only dead-branch elimination is viable.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
1. Open `HttpTransport.call` (lines ~145-218) and locate the `except httpx.RequestError as
   e:` handler at lines 206-215.
2. Delete the REQ-006 comment block (lines 207-210) and the unreachable guard
   `if name in _WRITE_TOOLS and not idempotency_key:` ... `raise self._transport_error(...,
   break_flag=True)` (lines 211-214).
3. Insert a replacement comment at the top of the handler documenting that writes are always
   retried on a non-timeout `httpx.RequestError` and that safety rests on the always-active
   server-side `_duplicate_cache` (dispatch.py), keyed on the once-per-call
   `X-Idempotency-Key`.
4. Leave the trailing `self._transport_error(name, f"[{type(e).__name__}]", str(e))` call
   (line 215) intact — it discards its return value and lets the retry loop continue, which
   is the documented always-retry behavior.
5. Do not touch the `idempotency_key` assignment (line 153) or the
   `headers["X-Idempotency-Key"]` assignment (line 159).

### Method
Single localized edit inside one `except` handler; no new symbols, imports, or signatures.

### Details
Before:
```python
            except httpx.RequestError as e:
                # REQ-006: a state-mutating write must not be retried without a
                # server-side dedup key (blind retry could execute it twice).
                # Gate the post-send retry on key presence for write tools; read
                # tools keep the current retry behavior.
                if name in _WRITE_TOOLS and not idempotency_key:
                    raise self._transport_error(
                        name, f"[{type(e).__name__}]", str(e), break_flag=True
                    )
                self._transport_error(name, f"[{type(e).__name__}]", str(e))
```
After:
```python
            except httpx.RequestError as e:
                # REQ-006: writes are always retried on a non-timeout
                # httpx.RequestError (this handler), exactly like read tools.
                # Safety against double execution rests on the always-active
                # server-side _duplicate_cache (dispatch.py), which deduplicates
                # every write keyed on the X-Idempotency-Key emitted once per
                # logical call (lines 153/159). No client-side backstop exists:
                # the key is always present, so a key-presence gate is impossible.
                self._transport_error(name, f"[{type(e).__name__}]", str(e))
```

## Compatibility considerations
N/A: no caller-visible contract change; retry behavior is unchanged.

## Security considerations
N/A: no new secret handling; the comment clarifies that dedup safety is server-side, not a
client-side guard.

## Rollback considerations
Revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/http_transport.py` | Static lint/type | `uv run ruff check scripts/` · `uv run mypy --no-namespace-packages scripts/` | clean |
| `scripts/shared/http_transport.py` | Behavioral (companion test) | `uv run pytest tests/shared/test_http_transport.py -v` | write/read retried 3x, timeout 1x |
| changed lines | Diff-scoped coverage | `uv run coverage run -m pytest tests/` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% |

## Completion criteria
The `not idempotency_key` guard and its REQ-006 comment are gone (no unreachable `raise`
remains), the handler comment documents the always-retry policy, and `ruff`, `mypy`, and
the shared-module suite pass.

## Out of scope
`dispatch.py` server-side dedup semantics, the retryable-status set (`429/502/503/504`),
non-MCP HTTP calls, and the `X-Idempotency-Key` header contract.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove unreachable write-retry branch and document always-retry policy in `scripts/shared/http_transport.py` | Pending | — | — | REQ-001, REQ-002; behavioral test authored in companion doc `20261013-070354_02_tests_shared_test_http_transport.py.md` |
| 3 | Run ruff/mypy/shared-suite/diff-cover and confirm clean | Pending | — | — | REQ-004 |

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
- **Requirement ID**: `REQ-001` (eliminate the dead branch), `REQ-002` (document the always-retry policy)
- **Source issue**: `issues/20261012-184834_mcp001_req-006-write-tool-retry-guard-is-structurally-inactive-in-httptransport.call.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-214127_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-070354
- **Related target files**: `scripts/shared/http_transport.py`
