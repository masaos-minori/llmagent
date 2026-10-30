# Implementation Procedure: tests/shared/test_http_transport.py

## Goal

Add deterministic-key regression coverage for the transport fallback (REQ-001 deterministic
key; REQ-010 cross-process determinism), test-first for row 01.

## Scope

**In scope:**
- `tests/shared/test_http_transport.py`: new deterministic-key tests and a cross-process
  determinism test.

**Out of scope:**
- Transport implementation (row 01).

## Assumptions

- Evidence correction: this file currently contains no idempotency-key assertions (grep for
  `idempotency|uuid|X-Idempotency` returns 0 hits at HEAD), so "adapt existing key
  assertions" reduces to adding new ones; existing tests stay byte-identical as
  characterization locks.
- Cross-process check uses `subprocess` with the repo venv interpreter running a tiny
  script that imports `derive_idempotency_key` (new) (row 01's new function) — if subprocess
  proves too heavy for CI, fall back to `importlib.reload`-based re-derivation (Needs
  Confirmation at implementation; determinism claim must genuinely cross processes).

## Design decisions

- New tests: same (tool, args-dict-insertion-order-variants, uid) → same key; different
  args → different key; key matches `^[A-Za-z0-9_-]{1,64}$`; two `HttpTransport.call`
  invocations against a stubbed local server capture the same `X-Idempotency-Key` value.
- Use the module-level `derive_idempotency_key` (new) (row 01) for unit-level equality and the
  captured-request headers (existing stub-server fixtures in this file) for end-to-end.

## Alternatives considered

- Asserting only regex shape — rejected: must pin cross-process equality (REQ-010), not
  shape.

## Implementation
### Target file
`tests/shared/test_http_transport.py`

### Procedure
1. Add the key tests described in Design decisions at the end of the file, reusing the
   existing fixture style (`server_key="srv"` constructions, e.g. `:48`).
2. Add the cross-process test (Assumptions).

### Method
Test-first: these tests fail until row 01 lands (expected red state until then).

### Details
- No changes to the existing 224 lines of test bodies.

## Compatibility considerations

- N/A: additive test cases only.

## Security considerations

- N/A: synthetic keys only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py` (red before row 01, green after);
  `uv run mypy --no-namespace-packages tests/shared`.

## Completion criteria

- Identical inputs derive identical keys in-process and cross-process; the suite passes
  with rows 01 landed and existing cases untouched.

## Out of Scope

- Dispatcher dedup tests (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add deterministic + cross-process key tests | Pending | — | — | Red until row 01 lands |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (deterministic key), `REQ-010` (cross-process determinism)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/shared/test_http_transport.py
