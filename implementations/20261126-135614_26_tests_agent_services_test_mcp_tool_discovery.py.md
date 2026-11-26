## Goal
- Update `tests/agent/services/test_mcp_tool_discovery.py` to cover the strict `config_dependent` validation, the capability-based exclusion, and the catalog-driven required-capability proof (REQ-005, REQ-006, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this test file only (standalone row: it is named by four target rows, seq 09, 10, 11, 17, so it is not a companion).
- Out of scope: the implementation changes (seq 09, 10, 11, 17).

## Assumptions
- Verified in Step 3a: the file pins the schema-2.1 field assertions (`test_mcp_tool_discovery.py:201-263`), the drift FATAL counts (`:152-153`), and the posture-gate exclusion outcomes (`:422-502`); those pins must not be weakened.
- The implementation is in seq 09 (reorder and proof), seq 10 (strict bool), seq 11 (pass-through and map), seq 17 (catalog); write the failing tests first.

## Design decisions
- New cases use the same fixture shape as the existing discovery tests (fake server entries plus a gate map), so the pinned assertions stay untouched.

## Alternatives considered
- N/A: test-only change.

## Implementation
### Target file
`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure
1. Add strict-bool cases: a non-bool `config_dependent` entry is rejected with a warning finding; a bool entry passes and reaches `RuntimeTool` with the declared value (T-07).
2. Add capability-exclusion cases: a tool whose owning server's capability is `degraded` or `unavailable` is excluded with reason `capability`; a tool with no capability dependency stays registered (T-06).
3. Add the catalog-driven proof case: a `required=true` server whose required capability is not proven `ok` produces FATAL; a legacy body falls back to `ready` (T-05).
4. Assert the catalog loads before registry construction by making the missing-catalog case observable before any tool row exists.

### Method
- Keep every existing pinned assertion unchanged; add cases only.

### Details
- The exclusion reason assertion reads `get_exclusion_reason()` (seq 13).

## Compatibility considerations
- The catalog fixture for the GitHub case must match seq 17 (`github.api` optional, `github.operations` required).

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The new cases fail before seq 09-11 and 17 and pass after; no existing pinned assertion is weakened.

## Out of Scope
- The implementation changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (required capability proof), `REQ-006` (capability exclusion), `REQ-007` (strict `config_dependent`)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`
