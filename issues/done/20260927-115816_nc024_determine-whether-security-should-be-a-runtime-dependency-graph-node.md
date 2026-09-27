# Determine whether Security should be a runtime dependency graph node

## Priority
Low

## Summary
Confirm whether a Security runtime component exists, and if so decide whether it should be added to `docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph node set, closing Needs Confirmation item NC-024.

## Background
NC-024 records that a quick `find` during a prior Plan's investigation found no `scripts/security/` package, but this was not exhaustively confirmed, leaving open whether the Software Runtime Dependency Graph's node set (Agent, MCP, RAG, EventBus, Shared/DB) is missing a Security node.

## Problem
This issue's own investigation found a `scripts/shared/security/` package (`__init__.py`, `audit.py`, `policy.py`) exporting `HighRiskToolPolicy`, `SecurityMode`, and `AuditLogger` — a real runtime component, not merely governance/policy documentation. However, a repository-wide search (`scripts/`, `tests/`) found zero importers of this package anywhere — no file imports `shared.security` or `scripts.shared.security`. The package appears to be defined but currently unused (dead code), not actively exercised at runtime by any other component.

## Reason for Change
The original NC-024 question ("does a Security runtime component exist?") is answered — yes, one exists in source. But the follow-on question ("should it be a graph node?") is complicated by this new finding: a Software Runtime Dependency Graph node is meant to represent an actively-calling/called component (per that graph's own definition: "A → B means A calls B at runtime"), and a zero-importer package has no current call edge to represent. Adding it as a node now could misrepresent it as wired-in when it is not; leaving it out risks the same "was this ever investigated" ambiguity NC-024 already caused once.

## Implementation Intent
Present both findings (the package exists; it currently has zero importers) to the owner for a decision, rather than resolving the graph-node question unilaterally — this is a documentation-modeling choice, not a pure fact-finding question. If the package is dead code awaiting future wiring, that may itself be a separate, smaller finding worth its own note (not necessarily this issue's scope to resolve).

## Target Files or Areas
- `scripts/shared/security/__init__.py`, `scripts/shared/security/audit.py`, `scripts/shared/security/policy.py` (reference only)
- `docs/00_governance/governance_01_documentation-policy.md` (Software Runtime Dependency Graph section)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-024 entry)

## Required Changes
- Present the owner with: (a) `scripts/shared/security/` exists and defines real security-policy/audit primitives, (b) it currently has zero importers anywhere in `scripts/`/`tests/`.
- Based on the owner's decision, either: add Security to the Software Runtime Dependency Graph's node set (if the package is expected to be wired in soon), or explicitly document it as an as-yet-unused module with no current runtime edge (if not).
- Remove NC-024 from Active Items once the decision is recorded.

## Constraints
N/A: this is a documentation/decision task; no behavior change is expected unless the owner separately requests wiring the package in.

## Acceptance Criteria
- The owner's decision on whether Security becomes a graph node is recorded in `docs/00_governance/governance_01_documentation-policy.md`.
- If added as a node, its actual call edges (once wired in) are documented; if not added, the package's current unused status is noted so a future reader does not need to re-investigate this question.
- NC-024 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
Not required: documentation/decision task, no behavior change.

## Documentation Impact
Update `docs/00_governance/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph section per the owner's decision. Remove the NC-024 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Wiring `scripts/shared/security/` into any calling code — that is a separate implementation task if the owner decides the package should be active.
- Any other dependency-graph node or edge beyond the Security question.

## Dependencies
N/A: none

## Unresolved Questions
- Should `scripts/shared/security/`'s currently-zero-importer status be filed as its own separate dead-code finding (distinct from the graph-node question)? Left to the owner to decide when reviewing this issue.

## AI Implementation Instruction
Do not decide the graph-node question unilaterally — present both findings (package exists; zero importers) and let the owner decide. Do not wire `scripts/shared/security/` into any calling code as a side effect of resolving this issue unless explicitly asked. Re-confirm the zero-importer finding via a fresh repository-wide search before acting on it, since this is a fast-moving codebase and the finding may be stale by the time this issue is picked up.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115816
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, scripts/shared/security/
