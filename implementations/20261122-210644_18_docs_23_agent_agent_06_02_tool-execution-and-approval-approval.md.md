## Goal

Document request-bound approval, required versus optional previews, HIGH fail-closed, the MEDIUM setting, masking, and audit provenance (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` only; documentation text is written in English (`skills/DESIGN.md` Output language).

## Assumptions

- Verified: the document lists fail-closed items at lines 95 and 122 (allowlist and `gitops_push_blocked`) and has no section on preview failure or request binding.

## Design decisions

- Describe the behavior the code procedures implement; do not document anything the Plan did not decide.

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

### Procedure
1. Add a subsection on approval request binding (request id, operation id, outcomes that deny).
2. Add preview rules: required for HIGH and failing closed on any preview failure; MEDIUM static fallback follows the setting; static previews and dry-run text are masked before truncation.
3. Add audit fields: request id, preview source, fallback reason, decision; no answer text.
4. Add the new items to the fail-closed list.

### Method
Edit the named sections in place; keep the front matter and keyword lists consistent.

### Details
- Name the new denial reasons exactly as the approval procedure defines them.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- The documentation checkers named in `rules/tool-gates.md` "When to run which tool" for a changed `docs/` file (run `uv run python tools/run_validation_gates.py`).

## Completion criteria

- The document matches the approval procedure's behavior; checkers pass.

## Out of Scope

Code changes and the CLI docs consolidation Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file | Pending | — | — | |

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
- **Requirement ID**: `REQ-009` (approval request binding and fail-closed preview)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
