## Goal
Make the deploy skill describe the binary-based runtime: add the rebuild phase and freshness gate, correct the rollback, `uv run`, restart, and `setup_services.sh` statements (`REQ-006`).

## Scope
- The Deploy scripts table, the Phase overview table, the Completion checklist, the Scope notes Rollback bullet, and the Required behavior bullet about full deploys.

## Assumptions
- The tool and script behavior are as specified in the sibling procedures; this file points to the tool for the source-path table.

## Design decisions
- Add "Phase 1b: Build affected binaries" instead of renumbering phases, so existing references to Phases 1 to 4 stay valid.
- Do not repeat the source-to-binary table; point to `tools/manage_binaries.py`.

## Alternatives considered
N/A: documentation wording.

## Implementation
### Target file
`skills/deploy/SKILL.md`

### Procedure
1. Update the `setup_services.sh` row to say it checks the remote LLM health and starts the Event Bus.
2. Add a row for the tool and for Phase 1b in the Phase overview, with the gate "every stale binary rebuilt, `check` reports no stale or unknown binary".
3. Add completion checklist items: freshness check reported, stale binaries rebuilt, deployed revision recorded.
4. Rewrite the Rollback bullet and the `uv run` claim; replace the "use a full deploy whenever `scripts/` files changed" bullet.
5. Run the skill checkers.

### Method
- New Rollback text: restore the previous binary set with `bash deploy/build_binaries.sh --rollback`; for components that run from deployed source (Event Bus, ingestion, workflow validation), re-run the deploy from the previous commit; service state is not rolled back; if the same failure recurs, stop and report (`AGENTS.md` Loop Prevention).
- The `uv run` claim: remove it for the agent; state that only MCP servers can be launched through their `cmd` entries and the agent always starts as `/opt/llm/bin/agent`.
- New Required behavior bullet: a change under `scripts/` reaches the agent and MCP servers only after their binaries are rebuilt; run the tool's `check` and rebuild the stale ones; the Event Bus and ingestion run from deployed source and need a process restart instead.

### Details
- Keep headings unchanged so cross-references do not break; run `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py`.
- A skill edit that revises procedure does not go through `python-documentation` (`routing.md` Documentation row exception).

## Compatibility considerations
N/A: wording change only; no other document restates the replaced sentence differently (see the Plan's Implementation Target Files rows for the sibling documents).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit (documents and the `SQLiteHelper` default must be reverted together to stay consistent).

## Validation plan
- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`

## Completion criteria
- The skill has the rebuild phase and freshness gate and no statement says `deploy.sh` alone delivers a code change to the agent or MCP servers.
- The rollback, `uv run`, restart, and `setup_services.sh` statements match the scripts.

## Out of scope
- `skills/deploy/workflow.md` (separate procedure)
- Other skills

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the table rows, phase overview, checklist, Scope notes, and Required behavior | Completed | 20261019-112524 | 20261019-112524 |  |
| 2 | Run the skill reference and heading-cycle checkers | Completed | 20261019-112524 | 20261019-112524 | checkers passed |

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
- **Requirement ID**: `REQ-006` (rebuild phase, freshness gate, corrected statements)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: skills/deploy/SKILL.md