## Goal

Create the closed MDQ domain error-code vocabulary and the mapping from the MDQ exception classes to codes (REQ-004 closed error vocabulary).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 2 is not listed in any `### Release units` entry)

## Assumptions
- Companion test row (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`.
- `CONTROL_ERROR_CODES` in `scripts/shared/mcp_call_state_contract.py` is closed to the control API and cannot carry domain codes, so the vocabulary stays in its own module.
- UNK-01 (non-blocking): the plan's default is the documented tool-level policy, so codes are defined without transport status bindings; the classification decision stays with the transport owner.
- The `timeout` code is defined here but its behavior lands in plan `mdqmcp002`; that is a consumption dependency, not a conflict.
- Cross-plan overlap on `docs/22_mcp/mcp_04_04_mdq.md` is a documentation-sequencing dependency: the error-code table in that doc is written by seq 27 from this vocabulary.

## Design decisions
- The vocabulary is a frozenset of lowercase-snake codes: validation, authorization, disabled tool, not found, database unavailable, consistency, timeout, unexpected.
- The module is policy only: no I/O, no logging, no transport status mapping.
- The exception-to-code mapping is a single function keyed by the MDQ exception classes, so the handlers in seq 01 render from it without owning the vocabulary.

## Alternatives considered
- Extend `CONTROL_ERROR_CODES` — rejected: that set is closed to the control API and its documented scope excludes domain codes.
- Keep `type(exc).__name__` as the code — rejected: AC-5 requires a stable code from a closed vocabulary.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_error_codes.py` (new)

### Procedure
- Define `MDQ_DOMAIN_ERROR_CODES` (new) as the frozenset of the eight codes.
- Define `code_for_exception()` (new) mapping `MdqValidationError`, `MdqAuthorizationError`, `MdqNotFoundError`, `MdqIndexNotReadyError`, `MdqDatabaseError`, `MdqConsistencyError`, `MdqServiceError` to codes, with `unexpected` as the fallback.
- Add `tool_disabled` to the set as the code the dispatch boundary uses for the refusal.

### Method
- The mapping returns a code from the set for every exception the MDQ path can raise; the search path's exception classes are covered by the same mapping (`scripts/mcp_servers/mdq/search.py`).

### Details
- No module-level I/O or logging; the module is import-safe.
- Retry semantics are not encoded here; they are documented in `docs/22_mcp/mcp_03_03_transport-and-health.md` and referenced by seq 27.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`
  - Procedure: add assertions for the closed code set and for the exception-to-code mapping; the existing exception-hierarchy assertions stay.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`

## Compatibility considerations
- Three later plans (search, file-processing, schema) consume this vocabulary; a late change here propagates, which is why the set is closed and in one module.

## Security considerations
- Codes must not carry exception text, SQLite detail, or paths (AC-5).

## Rollback considerations
- N/A: delete the new file and revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py tests/mcp_servers/mdq/test_mdq_exception_handlers.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- Every domain failure resolves to a code in the closed set.
- The mapping covers every MDQ exception class.
- No raw exception text, SQLite detail, or path is reachable from the module.

## Out of Scope
- The transport rendering (seq 01) and the documentation table (seq 27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion test file is covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is a separate row (seq 27) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-004 (closed domain error-code vocabulary)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_error_codes.py`, `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`
