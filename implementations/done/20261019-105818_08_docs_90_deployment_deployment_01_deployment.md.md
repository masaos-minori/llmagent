## Goal
Describe the build, freshness check, revision record, rollback, and the binary-versus-source component split in the deployment reference (`REQ-007`).

## Scope
- Section 2.6 (Compiled Artifacts), plus the deploy-script description in section 2.2 where it states what `deploy.sh` copies.

## Assumptions
- Behavior is as implemented by the sibling procedures; this document states intent and operations and points to the tool for the source-path table (`skills/DESIGN.md` Docs content policy).

## Design decisions
- Add a short component table: agent and MCP servers run from binaries; the Event Bus, ingestion, `init_db.sh`, and the workflow validation run from deployed source.
- State failure behavior: integrity failures stop the deploy, stale or unknown binaries warn unless strict.

## Alternatives considered
N/A: documentation wording.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Extend section 2.6 with: build to a staging directory, build info per binary, freshness check, revision record at `DEPLOYED_REV` (new), previous set kept for rollback.
2. Fix the sentence that says `deploy.sh` copies the binaries so it also says it checks them and records the revision.
3. Add the component-to-runtime table.
4. Run the documentation checkers.

### Method
- Write in English; no line numbers or concrete configuration values; refer to `tools/manage_binaries.py` for the source-path table and option details.

### Details
- Keep the existing statements about `/opt/llm/bin/` permissions and the external dictionary and config.

## Compatibility considerations
N/A: wording change only; no other document restates the replaced sentence differently (see the Plan's Implementation Target Files rows for the sibling documents).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit (documents and the `SQLiteHelper` default must be reverted together to stay consistent).

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain deployment`

## Completion criteria
- Section 2.6 describes build, freshness check, revision record, rollback, and the component split, and the checkers pass.

## Out of scope
- Any file other than the target file
- Code, tests, or configuration changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend section 2.6 and the `deploy.sh` description, and add the component table | Completed | 20261019-112524 | 20261019-112524 |  |
| 2 | Run the documentation checkers named in `routing.md` Tools (docs quality, structure, content policy, consistency for the touched domain) | Completed | 20261019-112524 | 20261019-112524 | checkers passed |

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
- **Requirement ID**: `REQ-007` (deployment reference)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: docs/90_deployment/deployment_01_deployment.md