## Goal
Add a new section to
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
documenting the coverage, platform-capability requirements, and manual
socket-check fallback of the new
`tests/integration/test_production_security_regression.py` regression suite
(`REQ-008`).

## Scope
- **In-Scope**: `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
  only — adding a new section documenting the regression suite from this
  Plan's other target row (seq 01).
- **Out-of-Scope**: writing or modifying the test file itself (owned by seq
  01); any other documentation file; `localremoval`'s/`loopbackonly`'s/
  `mcpauth`'s own documentation impact (separate Plans).

## Assumptions
- `tests/integration/test_production_security_regression.py` (this Plan's
  seq 01 row) is the file being documented — its exact test function names
  and REQ-006 fallback behavior should be confirmed against that file's
  actual content at the time this row executes (it may be generated after
  seq 01 completes, per Sequential Target Processing), not assumed from the
  Plan text alone.
- Re-confirmed 2026-09-03: `docs/05_agent_10_04_...md`'s current sections
  (`Workflow Startup Verification`, `Workflow Deployment Runbook`, `MCP
  Server Reloading Semantics`, `` `/context` Interpretation ``, `` `/stats`
  Interpretation ``) contain no coverage of a production-security regression
  suite — this is a genuinely new topic for this document.

## Design decisions
- Add the new section as a sibling `##`-level section (matching the existing
  `## Workflow Startup Verification` / `## Workflow Deployment Runbook` / `##
  MCP Server Reloading Semantics` pattern), rather than nesting it under an
  existing section — the regression suite is a distinct topic, not a
  refinement of Workflow Startup/Deployment or MCP Reloading.
- Document platform-capability requirements and the manual fallback
  explicitly and separately from the test-coverage list, so an operator
  running these tests in a capability-limited environment (no `unshare`
  permission) knows what to expect and how to verify manually — mirrors the
  source Issue's own Documentation Impact requirement.

## Alternatives considered
- Folding this content into the existing `## MCP Server Reloading Semantics`
  section — rejected: that section is about reload behavior, not
  process-level security regression test coverage; conflating the two would
  make both harder to find.

## Implementation
### Target file
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure
1. Add a new `## Production Security Regression Suite` section (placement:
   after `## MCP Server Reloading Semantics`, before `` ## `/context`
   Interpretation `` — keeps operational/startup-adjacent content grouped
   together, ahead of the interactive-command reference sections).
2. Document what the suite covers: Production-only policy enforcement,
   strict configuration validation, MCP server loopback-socket binding, MCP
   startup failure handling (required vs. optional), MCP authentication and
   log redaction, and external-unreachability — cross-referencing
   `tests/integration/test_production_security_regression.py` by path.
3. Document platform-capability requirements: which test(s) require
   `unshare --net` (or equivalent) capability, and what happens when that
   capability is unavailable (fallback path).
4. Document the manual-fallback verification procedure: how to manually
   confirm loopback-only binding and external unreachability when the
   automated namespace-isolation test falls back (e.g. steps to bind a probe
   socket to a non-loopback interface and confirm connection refusal).
5. State that these tests are expected to fail or be marked `xfail` until
   `localremoval`, `loopbackonly`, and `mcpauth` are implemented — cite them
   by Plan path, do not restate their content.

### Method
Direct `Edit` to `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`,
inserting the new section between the existing `## MCP Server Reloading
Semantics` and `` ## `/context` Interpretation `` sections.

### Details
- Cite `tests/integration/test_production_security_regression.py`'s actual
  test function names once seq 01 has created the file — re-read that file
  at execution time rather than guessing names from this Plan's Details.
- Cite `localremoval` (`plans/20260903-091417_plan.md`), `loopbackonly`
  (`plans/20260903-091921_plan.md`), and `mcpauth`
  (`plans/20260903-092407_plan.md`) by path only.
- Preserve the existing `## Related Docs` section at the end of the file —
  add this new section before it, not after.

## Compatibility considerations
N/A: documentation-only, no code compatibility impact.

## Security considerations
None — documentation-only description of an existing (once seq 01 lands)
test suite; no credentials or access-control content is affected.

## Rollback considerations
Single-file documentation edit under version control; revert via `git
revert` if needed. No other file depends on this document's structure.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_04_...md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No structural findings in the changed file |
| `docs/05_agent_10_04_...md` | Manual cross-check | Confirm the new section's test-name/path references match `tests/integration/test_production_security_regression.py`'s actual content | No stale or invented references |

## Completion criteria
- The new section documents the regression suite's coverage,
  platform-capability requirements, and manual-fallback procedure (AC-7).
- `check_docs_quality.py` reports no new errors.

## Out of scope
Writing/modifying `tests/integration/test_production_security_regression.py`
itself (seq 01); any other documentation file; `localremoval`'s/
`loopbackonly`'s/`mcpauth`'s own documentation impact.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Should execute after seq 01 (`test_production_security_regression.py`) so actual test names/behavior can be cited accurately |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document's own target file is the documentation being updated; no separate doc row applies |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/done/20260902-143337_prodregression_add_production_auth_network_isolation_regression_coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171258
- **Related target files**: docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
