## Goal

Reword the `RepositoryGateway` docstrings so they name the process boundary they guard — the
Agent-side write path toward the MCP git server — without claiming Agent-side approval authority
(REQ-009), as fixed by DT-05 Option A (REQ-004); the docstring text is also what the regenerated API
reference publishes (REQ-011).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- The module docstring line 3 "Single write enforcement boundary" is accurate for the git server
  process but is readable as Agent-side approval authority; ADR-012 Decision
  (`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:43`) and INV-04 (`:133`) are
  the authority texts the wording must match.
- The automated evidence for ADR-014 INV-03 is the test in Plan row 36; this document does not add it.

## Design decisions
- Wording names both sides: the gateway guards the Agent-side write path (allowlist, allowed root,
  approval gate); the MCP git server independently enforces refspec, protected-branch, and
  forced-update rules regardless of approval state.
- No behavior change: docstrings only.

## Alternatives considered
DT-05 Options B/C wording/authority variants — rejected by the maintainer decision.

## Implementation
### Target file
`scripts/agent/repository_gateway.py`
### Procedure
1. Reword the module docstring (`:3`) from "Single write enforcement boundary" to a two-process
   formulation consistent with ADR-012 Decision/INV-04.
2. Mirror the same formulation in the `RepositoryGateway` class docstring.
### Method
Docstring-only edit; no code, signature, or docstring-adjacent behavior changes.
### Details
- Cite `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` from the docstrings so a
  reader lands on the authority text.
- Keep the wording identical in spirit to ADR-014 INV-03 (`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md:130-132`):
  the Agent does not take over the server's technical safety judgments.

## Compatibility considerations
The regenerated API reference and `registry/manifests/agent_api.yaml` (rows 33/34, Phase 6) republish
the docstrings in the same release unit; never hand-edit them. `tests/agent/test_repository_gateway.py`
is a reference test — this document adds no instructions for it.

## Security considerations
Clearer wording prevents a future maintainer from weakening either side of the split; no runtime change.

## Rollback considerations
N/A: revert the commit; regeneration (row 33) must be re-run after any revert.

## Validation plan
- `uv run pytest tests/agent/test_repository_gateway.py -q` (behavior-neutral).
- `uv run python tools/generate_reference_table.py --check` after Phase 6 regeneration.
- `uv run python tools/check_adr_preservation.py` confirms the reword is intended, not a weakened invariant.

## Completion criteria
Both docstrings name the guarded process and cross-reference ADR-012; no behavior change; ADR
checkers pass.

## Out of Scope
The INV-03 gate test (row 36), ADR document edits (rows 27/28), artifact regeneration (rows 33/34).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the two docstrings per Procedure/Method/Details | Completed | 20261119-073438 | 20261119-073438 | Module + class docstrings now name the Agent-side boundary and cite ADR-012 INV-04 / ADR-014 INV-03; module line was "Single enforcement boundary..." (procedure quoted "Single write enforcement boundary" — verified against source) |\n| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-073438 | 20261119-073438 | ruff/mypy pass; 9 gateway tests pass unchanged; check_adr_preservation clean; artifact regeneration deferred to row 33 (Phase 6) as planned |

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
- **Requirement ID**: `REQ-009` (record the Agent-approval/server-enforcement boundary), `REQ-004` (DT-05 decision), `REQ-011` (generated artifacts)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/repository_gateway.py`
