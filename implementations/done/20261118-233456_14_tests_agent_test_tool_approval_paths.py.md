## Goal

Pin that a path-bearing ruled tool escalates to `HIGH` under the shipped protected paths, so any future
DT-06 change is visible as an intentional delta (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Fixture: `tests/agent/test_tool_approval_paths.py:1-30` builds the approval context and config used
  by the pre-flight cases.
- Measured posture (DT-06 Option A): with `allowed_root = "/opt/llm"` and the shipped protected paths,
  `write_file`, `edit_file`, `move_file` resolve to `high` in-jail; paths outside the jail are denied by
  `check_allowed_root()` before escalation.

## Design decisions
- Assert the escalation outcome (level `HIGH` and the escalation branch), not the prompt UI text.
- Add a companion assertion that an out-of-jail path is rejected by the jail check, so the two
  mechanisms stay distinguishable.

## Alternatives considered
Asserting the `[y/N]` prompt appearance — rejected; the prompt is a downstream rendering concern.

## Implementation
### Target file
`tests/agent/test_tool_approval_paths.py`
### Procedure
1. Add a parametrized test over `write_file`, `edit_file`, `move_file` asserting `HIGH` for an
   in-jail protected path.
2. Add an assertion that the same paths outside `allowed_root` fail the jail check.
### Method
Extend the existing fixture-driven case set; no existing assertion changes.
### Details
- Use the shared fixture constants from `tests/agent/_config_test_defaults.py` (row 20) rather than a
  local copy of the protected-path list.

## Compatibility considerations
Test-only; must pass against unmodified production code (Phase 1 gate).

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_paths.py -q`

## Completion criteria
The escalation and jail assertions pass against unmodified code and name the escalation branch
(AC-003).

## Out of Scope
The rule-over-tier gap pinning (row 15), protected-path semantics wording (rows 21/24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the escalation and jail assertions per Procedure | Completed | 20261119-075223 | 20261119-075223 | `TestProtectedPathEscalation` added (3+3 parametrized + jail test); provenance via medium-vs-high contrast on the same path; escalation evidence = audit `tool_approval` event risk field. Procedure corrections found in verification: (a) no protected-path fixture constant existed, so `SHIPPED_APPROVAL_PROTECTED_PATHS` was added to `tests/agent/_config_test_defaults.py` (folded into row 20's mirror duty); (b) HIGH prompts require the full word "yes" (`_prompt_user_approval` :131-133); (c) audit JSON uses compact separators (`"risk":"high"`) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-075223 | 20261119-075223 | ruff format/check pass; 10 tests pass (3 pre-existing jail tests + 7 new) |

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
- **Requirement ID**: `REQ-003` (characterization tests)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_tool_approval_paths.py`
