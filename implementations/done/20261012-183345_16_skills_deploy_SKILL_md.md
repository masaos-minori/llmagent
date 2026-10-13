## Goal

Update `skills/deploy/SKILL.md` to document the Nuitka `--onefile` deployment path: the build script, the binary/dictionary layout under `/opt/llm/`, the two environment variables, the failure behavior, and the rollback. Implements `REQ-007` / AC-10.

## Scope

Updates `skills/deploy/SKILL.md`: add the build script to the deploy-scripts table, document the binary/dictionary layout and the two environment variables, and extend the rollback section to cover the `cmd` switch. Does not change the skill's phase model or required-behavior sections beyond what the onefile path requires.

## Assumptions

- The current table lists `deploy/deploy.sh`, `deploy/init_db.sh`, and `deploy/setup_services.sh`.
- AC-10 requires the doc to describe the layout, the two environment variables (`LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`), failure behavior, and rollback.

## Design decisions

- Add `deploy/build_binaries.sh` to the deploy-scripts table with its purpose (build the 11 binaries) and when to run (once per release, on the build host).
- Add a short "Binary layout" subsection documenting `/opt/llm/bin/<binary>`, `/opt/llm/dict/system.dic`, and the external `config/`, plus the two environment variables and their fail-fast behavior.
- Extend the Rollback paragraph to state that reverting `config/agent.toml` and redeploying restores the `uv run` path.

## Alternatives considered

- Pointing to the deployment document instead of duplicating detail: acceptable, but the deploy skill is the operator-facing entry point, so the key facts belong here too.

## Implementation

### Target file

`skills/deploy/SKILL.md`

### Procedure

Extend the deploy-scripts table, add a binary-layout subsection, and extend the rollback section.

### Method

1. Add a row to the deploy-scripts table: `deploy/build_binaries.sh | Build the 11 Nuitka --onefile binaries into /opt/llm/bin/ | Once per release, on the build host`.
2. Add a "Binary layout" subsection after the deploy-scripts table documenting: `/opt/llm/bin/` holds the 11 binaries (not group/world-writable); `/opt/llm/dict/system.dic` is the external Sudachi dictionary; `config/` stays external; the agent exports `LLMAGENT_CONFIG_DIR=/opt/llm/config` and `LLMAGENT_SUDACHI_DICT=/opt/llm/dict/system.dic`; a missing config dir or dictionary fails startup with an explicit error naming the path.
3. Extend the Rollback paragraph: reverting `config/agent.toml` to the `uv run` `cmd` entries and redeploying restores the `uv run` path; `scripts/` stays deployed so the `uv run` path keeps working.

### Details

- Keep the existing `see \`rules/env.md\`` and `see \`workflow.md\`` cross-references intact.
- Do not alter the phase model or required-behavior sections beyond the onefile additions.

## Compatibility considerations

- The change is additive documentation; it does not change deploy behavior.

## Security considerations

- N/A: documentation only. Note in the doc that `/opt/llm/bin/` must not be group/world-writable (the CommandValidator rejects binaries under a writable directory).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_skills_references.py` pass (AC-10).
- Confirm every backtick-quoted `skills/`/`rules/`/`templates/` reference resolves.

## Completion criteria

- `skills/deploy/SKILL.md` documents the binary layout, the two environment variables, failure behavior, and rollback; the docs/skills checkers pass.

## Out of scope

- The deployment document (`docs/90_deployment/deployment_01_deployment.md`) is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `deploy/build_binaries.sh` to the deploy-scripts table | Completed | 20261012 | 20261012 | Added as 4th row (build-host, once per release) |
| 2 | Document the binary layout and the two environment variables | Completed | 20261012 | 20261012 | New "Binary layout" subsection after deploy-scripts table |
| 3 | Extend the rollback section for the `cmd` switch | Completed | 20261012 | 20261012 | Rollback bullet now covers reverting `config/agent.toml` `cmd` entries |
| 4 | Run the docs/skills checkers | Completed | 20261012 | 20261012 | check_skills_references + check_docs_quality/structure/content_policy all pass (AC-10) |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: skills/deploy/SKILL.md
