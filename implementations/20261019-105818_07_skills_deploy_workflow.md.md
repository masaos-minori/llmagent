## Goal
Make the deploy workflow include the freshness report, a rebuild phase, binary-aware restart criteria, and the revision check (`REQ-006`).

## Scope
- Phase 1 (freshness report), a new Phase 1b section, Phase 3 Step 3a criteria, and Phase 4 verification.

## Assumptions
- Sibling procedures define the tool options used in the commands below.

## Design decisions
- Express Step 3a criteria in terms of which binary was rebuilt or which source-run component changed, not source file names.
- Keep Phase numbering; add Phase 1b.

## Alternatives considered
N/A: documentation wording.

## Implementation
### Target file
`skills/deploy/workflow.md`

### Procedure
1. In Phase 1, add the freshness report command and how to read its result.
2. Add "Phase 1b: Build affected binaries" with the command that lists stale names and the build command.
3. Rewrite Step 3a: restart the agent only when the `agent` binary was rebuilt or `config/agent.toml` changed in a restart-only way; kill an MCP server by port when its binary was rebuilt; restart the Event Bus process when `scripts/eventbus/` changed, noting that a repeated `setup_services.sh` run can start a second Event Bus.
4. In Phase 4, add checking that `/opt/llm/DEPLOYED_REV` matches the deployed commit.
5. Run the skill checkers.

### Method
- Phase 1 command: `python3 tools/manage_binaries.py check --bin-dir /opt/llm/bin --rev auto --repo .`; Phase 1b: `BUILD_ONLY="$(python3 tools/manage_binaries.py check --bin-dir /opt/llm/bin --rev auto --repo . --list-stale)" bash deploy/build_binaries.sh`.
- Set `DEPLOY_STRICT_BINARIES=1` for the deploy once all binaries have build info.

### Details
- Add "Completed when" and "Stop and report when" lines to Phase 1b in the existing style (a failed build is reported, not retried a third time).
- Mention the previous-set rollback command in the failure recovery text.

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
- Phase 1b exists with its gate, Step 3a is binary-aware, and Phase 4 checks the revision record.

## Out of scope
- `skills/deploy/SKILL.md` (separate procedure)
- Running the commands against production

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit Phase 1, add Phase 1b, rewrite Step 3a, extend Phase 4 | Pending | — | — | |
| 2 | Run the skill reference and heading-cycle checkers | Pending | — | — | |

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
- **Related target files**: skills/deploy/workflow.md
