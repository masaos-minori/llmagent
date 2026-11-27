## Goal

Expose the canonicalized roots used by the SQL source predicate, so authorization lives in one place and the query boundary does not re-implement it (REQ-001, REQ-002, AC-1, AC-2).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 2 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- Companion test row (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_mdq_path_jail.py`.
- `tests/mcp_servers/mdq/test_auth.py` is a related test but not a target row, so it is not a companion; it is run unchanged as the authorization behavior lock.
- The SQL predicate is built in `scripts/mcp_servers/mdq/search.py` (seq 01); this document exposes the roots, it does not build the predicate.
- Execution-order dependency on plan 001: its procedures are still Pending, so the Step 3c gated marker is written on each pending row of this document. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed; the marker records the substantive dependency, not tool readiness.

## Design decisions
- The module returns the canonicalized root set as data; it does not decide authorization for the caller.
- `authorize_path()` stays as the last gate for symlink escapes, which a SQL prefix predicate cannot see.

## Alternatives considered
- Let `search.py` canonicalize the roots itself — rejected: the requirement keeps authorization in one place, and a second canonicalization path can diverge from the first.

## Implementation
### Target file
`scripts/mcp_servers/mdq/auth.py`

### Procedure
- Add `canonicalized_roots()` (new) that returns the resolved roots from the same `allowed_dirs` the authorization decision uses.
- Keep `authorize_path()` (line 19) and `_is_within_root()` (line 12) unchanged, including the empty-allowlist branch (line 27).

### Method
- The roots are resolved with the same `Path.resolve()` call the authorization loop already performs (line 35), so the predicate and the authorization decision compare the same values.

### Details
- No I/O and no logging in the new function.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_path_jail.py`
  - Procedure: add the canonicalized-prefix cases for the SQL source predicate, including a symlinked root and a prefix outside `allowed_dirs`; `test_symlink_escape_denied` stays as the Python-gate test.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_path_jail.py tests/mcp_servers/mdq/test_auth.py`

## Compatibility considerations
- Existing callers of `authorize_path()` are unchanged, so the tool paths that use it keep the same behavior.

## Security considerations
- A prefix outside `allowed_dirs` must not match rows through the SQL predicate (AC-2).

## Rollback considerations
- N/A: revert the commit; the companion test's added cases fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_path_jail.py tests/mcp_servers/mdq/test_auth.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The query boundary reads the roots from this module rather than re-implementing canonicalization.
- The symlink-escape and outside-root cases are covered through the SQL predicate.

## Out of Scope
- The SQL predicate itself (seq 01).
- The documentation of the filter semantics (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Depends on plan 001 procedures, which are still Pending |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Companion test file is covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Documentation is a separate row (seq 11) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-001 (single authorization place), REQ-002 (authorized source predicate)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `scripts/mcp_servers/mdq/auth.py`, `tests/mcp_servers/mdq/test_mdq_path_jail.py`
