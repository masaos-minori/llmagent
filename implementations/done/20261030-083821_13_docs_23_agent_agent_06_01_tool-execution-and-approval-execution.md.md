# Implementation Procedure: agent_06_01 loop bound and availability hint behavior

## Goal

Describe the unavailable-repeat loop bound and the advisory availability hint in the
tool-execution doc (REQ-008; plan AC-2).

## Scope

**In scope:**
- `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`: one behavior
  subsection (the doc's section set at HEAD `124e340b4`: Purpose, Design Intent,
  Responsibility Boundary, Key Constraints, Known Limitations, Keywords).

**Out of scope:**
- Any other agent spec doc; `agent_06_03` (HALF_OPEN trial semantics doc) is a reference
  only, not edited.

## Assumptions
- Docs content policy (`skills/DESIGN.md`): describe behavior, intent, and boundaries —
  no implementation locations (no file paths or class names); the loop-guard behavior is
  already described at behavior level in this doc family.

## Design decisions
- Add a subsection under Design Intent stating:
  - When a tool result signals server unavailability (normalized reason, circuit state,
    optional retry timing — the same vocabulary as `docs/22_mcp/mcp_06_10`), the signal is
    advisory: routing, LLM tool visibility, and static availability are unchanged.
  - Repeated selection of tools from the same unavailable server within a turn is bounded
    by the existing empty-result repeat configuration; at the bound the turn ends with an
    observable system hint. A successful call for that server clears the accumulated
    count (recovery removal).
  - The bound is off when the reused configuration is 0 (repo default).
- Keywords section: append the terms already used by the MCP doc (availability hint,
  retry_after) only if the Keywords convention requires cross-doc terms.

## Alternatives considered
- Documenting in `agent_06_03` (concurrency safety): rejected — that doc owns HALF_OPEN
  trial mechanics; the loop bound is turn-execution behavior owned here.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
1. Re-read Design Intent at current HEAD before inserting (doc churn 12/30d per plan).
2. Insert the subsection; keep existing sections byte-identical.

### Method
- Behavior-level prose matching the doc's existing tone.

### Details
- No threshold numbers beyond "the reused configuration"; config-key naming is allowed
  only if the doc already names config keys (it names `tool_result_max_llm_chars`-style
  dials today — match its existing convention).

## Compatibility considerations
- Wording must match ADR-003 Decision 17 (row 12) exactly in normative claims: advisory
  only, no routing/visibility effect.

## Security considerations
- State explicitly that server-supplied free text is not part of the bounded-hint signal.

## Rollback considerations
- Remove the inserted subsection.

## Validation plan
- Docs checkers from `routing.md` green; `tools/stale_detector.py` green for this doc.

## Completion criteria
- Bound, hint, recovery-clearing, and default-off semantics described; no implementation
  locations named; checkers green.

## Out of Scope
- ADR-003 (row 12), MCP reason-code doc (row 14), code rows 01-06.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert availability-hint/loop-bound subsection | Completed | — | 20261030-204921 | Design Intent subsection 'Dynamic Availability Hints and the Unavailable-Repeat Bound' inserted before Responsibility Boundary; Keywords appended |
| 2 | Run docs checkers from `routing.md` | Completed | — | 20261030-204921 | check_docs_quality + check_docs_structure + stale_detector green |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`