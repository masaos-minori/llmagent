## Goal

Document the new MEDIUM preview-fallback field next to the other approval settings (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` only; documentation text is written in English (`skills/DESIGN.md` Output language).

## Assumptions

- Verified: the approval settings list sits near line 107 (`gitops_push_blocked`).

## Design decisions

- Describe the behavior the code procedures implement; do not document anything the Plan did not decide.

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Add a bullet for the new field: type, default (allowed), effect on MEDIUM only, and that HIGH never falls back.

### Method
Edit the named sections in place; keep the front matter and keyword lists consistent.

### Details
- Keep any generated configuration table untouched; regenerate only if the checker requires it.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- The documentation checkers named in `rules/tool-gates.md` "When to run which tool" for a changed `docs/` file (run `uv run python tools/run_validation_gates.py`).

## Completion criteria

- The field is documented with its default; checkers pass.

## Out of Scope

Code changes and the CLI docs consolidation Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-213744 | 20261122-213744 | Changed: docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file | Completed | 20261122-213744 | 20261122-213744 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-009` (new approval configuration field)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
