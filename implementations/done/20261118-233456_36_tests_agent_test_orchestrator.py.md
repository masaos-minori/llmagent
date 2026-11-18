## Goal

Add the automated evidence for ADR-014 INV-03 that DT-05 Option A requires: a test gate replacing the
Manual-Review-only status of the "server-side safety judgments are not re-implemented Agent-side"
invariant (REQ-009, AC-009).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- No test currently cites INV-03; the suite's ADR-014 block is the INV-02 section at
  `tests/agent/test_orchestrator.py:3205-3209`.
- No `scripts/agent/` module imports `mcp_servers.tool_validators` today (verified by grep), so the gate
  passes against unmodified code.
- The Agent-side layers named by INV-03 are `scripts/agent/orchestrator.py`,
  `scripts/agent/llm_turn_executor.py`, and the tool-execution modules `scripts/agent/tool_runner.py`,
  `scripts/agent/tool_preparation.py`, `scripts/agent/tool_scheduler.py`.

## Design decisions
- Gate as a source-boundary assertion, not a behavior test: assert the Agent-side layers do not import or
  define the server-side validator entry points (`scripts/mcp_servers/tool_validators.py`'s
  `validate_tool_args`, `register_validator`, and its path/sandbox helpers), and that they keep delegating
  to the Agent-side boundary checks (`check_allowed_root()`, `check_allowed_repo()`,
  `RepositoryGateway`) rather than reimplementing them.
- Keep it in this suite: it is the file that already cites ADR-014 (Plan amendment 2026-11-18).

## Alternatives considered
An import-linter contract — rejected for this row: `.importlinter` already permits
`agent → mcp_servers` for the installer path, so a contract would either over-permit or require an unrelated
architecture change.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`
### Procedure
1. Add an `# ── INV-03: no server-side safety re-implementation (ADR-014) ──` section after the INV-02 block
   (`:3205`).
2. Add `TestNoServerSideSafetyReimplementation` (new) with a source-scan test asserting the named Agent-side
   modules contain no import of `mcp_servers.tool_validators` and no definition of a path-validation,
   sandboxing, or allowlist helper of the kind the MCP servers own.
3. Add a delegation assertion: the Agent-side modules still call the existing boundary checks named in
   Design decisions.
### Method
Static source inspection via `pathlib` (the pattern already used in this suite's other source-scanning
tests); no new fixtures.
### Details
- Cite ADR-014 INV-03 in the class docstring so `check_adr_reference.py` and the invariant matrix
  (row 31) can resolve the evidence identifier.
- Class and method names must match exactly what rows 27 and 31 cite.

## Compatibility considerations
Test-only; the invariant statement itself is unchanged (row 27 edits only the verification statements).

## Security considerations
Adds a regression gate against Agent-side duplication of MCP server safety checks.

## Rollback considerations
N/A: revert the commit; rows 27/31/35 must be reverted with it because they cite this test.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator.py -q`
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` after
  rows 27/31 land.

## Completion criteria
The test passes against unmodified code, and the ADR text, matrix row, and generated manifest all cite it
(AC-009).

## Out of Scope
ADR-014's own text (row 27), the matrix (row 31), the manifest (row 35).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the INV-03 gate section and test class per Procedure | Completed | 20261119-081511 | 20261119-081511 | `TestNoServerSideSafetyReimplementation` added after the INV-02 block in `tests/agent/test_orchestrator.py` with ADR-014 INV-03 cited in the class docstring: 5 parametrized source-scan tests (no `mcp_servers.tool_validators` import, no re-definition of the 8 validator entry points in the named Agent-side modules) + 1 delegation test (tool_policy defines and calls `check_allowed_root()`/`check_allowed_repo()` inside `check_preflight()`; `RepositoryGateway` class + factory construction). Verified assumption: no `mcp_servers` import exists in the five modules today. Name matches rows 27/31 citations. Note: this suite had no prior pathlib source-scan tests (Procedure's claim); the `_REPO_ROOT`/`read_text` idiom from other suites was used instead |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-081511 | 20261119-081511 | ruff format/check pass; 6 new tests pass; full `tests/agent/test_orchestrator.py` 144 passed; check_adr_reference and check_adr_invariant_matrix pass after rows 27/31 land |

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
- **Requirement ID**: `REQ-009` (ADR-014 INV-03 automated evidence), `REQ-004` (DT-05 decision)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_orchestrator.py`
