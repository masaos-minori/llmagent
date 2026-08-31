# No current Specification records per-component required/non-required classification required by ADR-004

## Priority
Medium

## Summary
`docs/adr/ADR-004-environment-failure-handling-policy.md` (Decision Group 3) requires that "the
appropriate Startup, Agent, or MCP Specification records each component's approved
classification" as required or non-required. No such Specification currently exists anywhere in
`docs/`.

## Background
Discovered while rewriting ADR-004 on 2026-08-31. ADR-004 deliberately does not list individual
components as required/non-required itself (per its own instruction not to invent
classifications without an authoritative source), and instead delegates that recording
responsibility to area Specifications. A search of the MCP and Agent configuration Specifications
(`docs/05_agent_08_01` through `08_04`, `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`)
found no document that classifies any MCP server or other component as required or non-required.

## Problem
(Evidence: Needs confirmation — absence confirmed by search, not by exhaustive enumeration of
every Specification in the repository) `scripts/shared/mcp_config.py`'s `McpServerConfig` has
`required_in_production`/`required_in_local` fields (both defaulting to `True`), but no
Specification document explains which servers should be `True` vs `False`, or by what criteria a
maintainer should decide. `config/agent.toml` does not override these fields for any server, so
in practice every configured MCP server is currently treated as required.

## Reason for Change
ADR-004's non-required-component behavior (Decision Groups 3, 7) cannot be correctly implemented
or operated without an authoritative record of which components are actually non-required —
without it, any implementation must either guess (which ADR-004 explicitly forbids) or leave
every component required by default indefinitely, making the new non-required/partial-availability
model unused in practice.

## Implementation Intent
Create or extend an Agent or MCP Specification that records, per configured component (starting
with MCP servers), its classification as required or non-required against ADR-004's Decision
Group 3 criteria, with a stated rationale per component. This is a documentation task; it does
not itself change `McpServerConfig` or runtime behavior (that is
`issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`'s
concern), but its output is a prerequisite for that issue's implementation.

## Target Files or Areas
- New or extended Specification under `docs/04_mcp_*` or `docs/05_agent_08_*` (exact placement
  needs an owner decision — this may belong in a new document or as a section added to an
  existing configuration Specification)
- `docs/adr/ADR-004-environment-failure-handling-policy.md` — read-only reference for the
  classification criteria (Decision Group 3, items 9–13)

## Required Changes
- Decide, with the architecture/component owners, which current MCP servers (and any other
  configured components) are required vs. non-required, applying ADR-004's stated criteria.
- Record each classification and its rationale in an appropriate Specification.
- Cross-reference this Specification from ADR-004's Related Documents once it exists.

## Constraints
- Do not classify a component as non-required merely because doing so is convenient or because
  startup is technically possible without it — ADR-004 explicitly prohibits this.
- Do not implement the classification in code as part of this issue — this issue is
  documentation-only; code alignment is tracked separately.

## Acceptance Criteria
- A Specification exists that lists every currently configured MCP server (at minimum) with an
  explicit required/non-required classification and a stated rationale referencing ADR-004's
  criteria.
- ADR-004's Related Documents references the new/extended Specification.

## Testing Expectations
Not applicable — documentation-only change.

## Documentation Impact
This issue is itself the documentation gap it closes. Update ADR-004's Related Documents once
the Specification exists.

## Out of Scope
- Changing `McpServerConfig` or any runtime classification logic (see
  `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`).
- Classifying components outside MCP servers unless an owner requests it in the same pass.

## Dependencies
Blocks `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`.
Follows the 2026-08-31 ADR-004 rewrite (Decision Group 3).

## Unresolved Questions
Which document (new or existing) should own this classification record — needs an owner
decision on placement before drafting.

## AI Implementation Instruction
Do not invent a classification for any component without an owner decision or existing
authoritative evidence. If asked to implement this issue, present the candidate list of
currently configured components and ask the owner to classify each one against ADR-004's
criteria rather than deciding unilaterally.
