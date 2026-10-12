## Goal

Update `docs/90_deployment/deployment_01_deployment.md` to document the Nuitka `--onefile` layout, the two environment variables, the failure behavior, and the rollback. Implements `REQ-007` / AC-10.

## Scope

Updates `docs/90_deployment/deployment_01_deployment.md`: add the binary/dictionary layout, the `LLMAGENT_CONFIG_DIR` and `LLMAGENT_SUDACHI_DICT` variables and their fail-fast behavior, and the rollback procedure. Aligns with `docs/00_index.md`'s "Document References by Task" routing for this document.

## Assumptions

- The current document describes the existing `uv run` deployment layout; it does not yet mention the compiled binaries or the two environment variables.
- AC-10 requires the doc to describe the layout, the two environment variables, failure behavior, and rollback.

## Design decisions

- Add a "Binary layout" section documenting `/opt/llm/bin/<binary>` (11 binaries, not group/world-writable), `/opt/llm/dict/system.dic` (external Sudachi dictionary), and the external `config/`.
- Document the two environment variables, how they are exported by `deploy/start_agent.sh`, and that a missing config directory or dictionary fails startup with an explicit error naming the path (AC-01, AC-05).
- Add a rollback subsection: revert `config/agent.toml` to the `uv run` `cmd` entries and redeploy; `scripts/` stays deployed so the `uv run` path keeps working.

## Alternatives considered

- Referencing `skills/deploy/SKILL.md` for all detail: acceptable, but this deployment document is the canonical layout reference, so the layout belongs here.

## Implementation

### Target file

`docs/90_deployment/deployment_01_deployment.md`

### Procedure

Add the binary layout, environment variables, failure behavior, and rollback to the deployment document.

### Method

1. Add a "Binary layout" subsection documenting the `/opt/llm/bin/`, `/opt/llm/dict/`, and external `config/` layout and the non-group/world-writable requirement for `/opt/llm/bin/`.
2. Document `LLMAGENT_CONFIG_DIR` and `LLMAGENT_SUDACHI_DICT`: purpose, exporter (`deploy/start_agent.sh`), and fail-fast behavior on a missing path.
3. Add a rollback subsection covering the `config/agent.toml` revert plus redeploy.

### Details

- Keep the document consistent with `docs/00_index.md`'s task routing and with the sibling deployment document referenced in the skill.
- Use English body text per the template language rule.

## Compatibility considerations

- The change is additive documentation; it does not change deployment behavior.

## Security considerations

- N/A: documentation only. Note in the doc that `/opt/llm/bin/` must not be group/world-writable (the CommandValidator rejects binaries under a writable directory).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_skills_references.py` pass (AC-10).
- Confirm every backtick-quoted `skills/`/`rules/`/`templates/` reference resolves.

## Completion criteria

- `docs/90_deployment/deployment_01_deployment.md` documents the layout, the two environment variables, failure behavior, and rollback; the docs checkers pass.

## Out of scope

- The deploy skill (`skills/deploy/SKILL.md`) is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the binary/dictionary layout section | Pending | — | — | |
| 2 | Document the two environment variables and failure behavior | Pending | — | — | |
| 3 | Add the rollback subsection | Pending | — | — | |
| 4 | Run the docs checkers | Pending | — | — | AC-10 |

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
- **Related target files**: docs/90_deployment/deployment_01_deployment.md
