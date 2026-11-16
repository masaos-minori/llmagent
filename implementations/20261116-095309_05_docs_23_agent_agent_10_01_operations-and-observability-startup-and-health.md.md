## Goal

State in the startup and health document that each MCP server's posture is observed once per startup and that tool discovery uses that observation (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `readiness` description bullet in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.
- Out of scope: ADR text, other bullets, other documents, and any concrete value.

## Assumptions

- Execute after documents `01` and `02` of this Plan, so the text describes landed behavior.
- The `readiness` bullet covers required-service availability and every MCP server's Security Posture gate and defers the `FAILED` handling to ADR-004; it says nothing about how often posture is observed (re-read in Step 3a).
- Plan overlap judgment: this document is also a target of Plans `startrev006` and `startrev004`, each editing a different statement of the same document; the sentences do not contradict each other, and this Plan goes first.

## Design decisions

- Add one sentence of policy to the `readiness` bullet: the posture of each MCP server is observed once per startup, readiness classifies that observation, and tool discovery uses the same observation (ADR-003 Decision Detail 16 already states this; the document now agrees). No counts, timeouts, ports or file names (`skills/DESIGN.md` Docs content policy).

## Alternatives considered

N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Append the one-sentence rule to the end of the `readiness` bullet, in English, keeping the existing ADR-004 link intact.
2. Run the documentation checkers named in the Validation plan and fix findings in the added text only.

### Method
- Reuse the bullet's terms (Security Posture gate, readiness, tool discovery); introduce no new identifiers and no implementation-location statements.

### Details
- Leave the other startup-check bullets, the front matter and the Keywords section as they are.

## Compatibility considerations

N/A: documentation-only; no document is renamed or moved.

## Security considerations

N/A: no secrets or values are added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The `readiness` bullet states that posture is observed once per startup and that discovery uses that observation (`REQ-006`, AC-6), and all checkers above report no finding.

## Out of Scope

- Code, tests, ADR changes, and wording changes outside the one bullet.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the once-per-startup observation to the `readiness` bullet | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (startup health document states the one-observation rule)
- **Source issue**: issues/20261115-214905_startrev005_posture-probed-twice-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220913_startrev005_posture-probed-twice-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095309
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
