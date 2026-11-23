## Goal

Document the session generation, the transition snapshot, and per-session title pending in the agent state model reference (REQ-010 state-model documentation; AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

Documentation-only change to the session state model doc.

## Assumptions
- The doc currently has no generation concept (plan evidence, checked in Step 3); structure is the existing state-model sections.

## Design decisions
- Add generation and `SessionTarget` (owned by seq 01) to the session state description as runtime-only state (no schema claim), and describe the transition snapshot as the unit of atomic commit/rollback.
- Title pending is described as per-session-id state, matching the seq 01 behavior.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`
### Procedure
1. Extend the session state section with generation, target capture, and per-session title pending.
2. Add a short transition-snapshot subsection referencing the transition semantics documented in seq 15 without restating the pipeline.
### Method
Prose additions to existing sections; no tables removed.
### Details
N/A: none beyond the plan text.

## Compatibility considerations
- Claims must match seq 01-03 implementations (write after those rows land); the agent-domain checker cross-checks symbol references.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Doc checkers per `rules/tool-gates.md`: check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py, check_docs_consistency.py --domain agent, check_docs_japanese.py.

## Completion criteria
The state model names generation, the transition snapshot, and per-session title pending consistently with the implemented behavior, with no checker findings (AC-6).

## Out of Scope
Command-facing text (seq 15), the compression doc (seq 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add generation, snapshot, and per-session pending sections | Completed | — | 20261123-121907 | Docs-only row: no test step Changed: docs/23_agent/agent_04_01_state-and-persistence-state-model.md (generation/target, transition and persistence snapshots, memory finalization marker, title fallback audit format) |
| 2 | Run the doc checkers named in `rules/tool-gates.md` | Completed | — | 20261123-121907 | Same doc checkers as seq 15 pass |

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
- **Requirement ID**: `REQ-010` (state-model documentation)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`