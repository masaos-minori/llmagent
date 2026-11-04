## Goal
- Describe in the startup and health document the new startup order (config-only validation before server start), its intent (fail before external effects), and the boundary between config-only and runtime-dependent checks, and correct the statements that every check always runs and that all checks complete before the abort (`REQ-007`: documentation matches the new order and the corrected short-circuit behavior).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: four edits in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (the design-intent paragraph, one added paragraph before the severity table, one table cell, and two spans of the `mcp_auth` bullet). The first two sentences of the `mcp_auth` bullet are edited by the disabled-auth Plan's procedure and are not touched here.

## Assumptions
- Execution order: this procedure runs after the disabled-auth Plan's documentation procedure for the same file, which rewrites the first two sentences of the `mcp_auth` bullet; the spans edited here (the lead-in parenthetical and the short-circuit sentence) are outside them.
- The current design-intent paragraph says startup is divided into two phases (server start and health check) with a rollback on an exception in any phase; the severity table cell says FATAL "Throws `RuntimeError` after all checks complete, aborting startup"; the bullet claims `check_services()` does not short-circuit and every check always runs (checked in Step 3a).
- The code behavior documented here is the one the production procedures create: the config-only stage (`mcp_auth`, `component_mandatoriness`, `routing_drift`, `routing_safety_tiers`) runs after component initialization and before any server is spawned, aborts without a rollback, and reports its checks together; the runtime stage skips discovery and RAG after a readiness FATAL.
- The same document is also edited by the disabled-auth Plan and by the interrupted-startup exit Plan, in different text; no contradiction exists.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown.

## Design decisions
- State the boundary rule once, as a new paragraph before the severity table: a check that reads only configuration belongs to the config-only stage, and a check that needs a running service belongs to the runtime stage.
- Edit minimal spans; keep every symbol name in backticks; add no port, timeout, or other concrete value.

## Alternatives considered
N/A: bounded text edits.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Replace the one-sentence design-intent paragraph that starts `The startup process is divided into two phases`.
2. Insert the new paragraph directly after the heading `### Severity Mapping for Startup Verification`, with a blank line before and after it.
3. Replace the FATAL row's behavior cell in the severity table.
4. In the `mcp_auth` bullet, replace the lead-in parenthetical and the short-circuit sentence.

### Method
Design-intent paragraph, Before:

```text
The startup process is divided into two phases: server start and health check. If an exception occurs in any phase, a rollback is triggered to ensure all started subprocesses are reliably terminated.
```

After:

```text
Startup validates configuration before it spawns anything, then starts the servers and checks their health. A configuration-only validation stage runs first, so a configuration failure is reported before any MCP subprocess exists and needs no rollback. If an exception occurs after servers have started, a rollback is triggered to ensure all started subprocesses are reliably terminated.
```

New paragraph before the table:

```text
Startup validation runs in two stages. The config-only stage (`mcp_auth`, `component_mandatoriness`, `routing_drift`, `routing_safety_tiers`) reads only configuration and static registries, so it runs before any MCP subprocess is spawned, reports its checks together, and aborts startup without a rollback. The runtime stage (`readiness`, `mcp_tool_discovery`, `rag_consistency`) needs running services and runs after the servers are started and verified; it skips tool discovery and the RAG check when readiness already reported a FATAL. A check that reads only configuration belongs to the config-only stage, and a check that needs a running service belongs to the runtime stage.
```

FATAL row cell, Before:

```text
Throws `RuntimeError` after all checks complete, aborting startup
```

After:

```text
Throws `RuntimeError` after the checks of the failing stage complete, aborting startup
```

`mcp_auth` bullet lead-in, Before:

```text
("1b. MCP authentication check", runs before the service-readiness check)
```

After:

```text
("1b. MCP authentication check", runs in the config-only stage, before any MCP subprocess is spawned)
```

Short-circuit sentence, Before:

```text
`check_services()` does not short-circuit on an earlier FATAL: every check listed here always runs and reports independently; only the final aggregated `has_fatal` decides whether startup aborts.
```

After:

```text
The four config-only checks always run and report together before the abort decision. The runtime stage skips tool discovery and the RAG check when readiness already reported a FATAL; only the aggregated `has_fatal` of a stage decides whether startup aborts.
```

### Details
- Do not edit the first two sentences of the `mcp_auth` bullet (disabled-auth Plan) or any other bullet.
- Keep the table structure and the heading text unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` shows only the edited spans plus the added paragraph.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain agent` report no findings.

## Completion criteria
- The document describes the config-only stage before server start, the intent, and the stage boundary, and no longer says every check always runs or that all checks complete before the abort (`AC-6`).
- The docs checkers are clean, and no concrete timeout or value was added.

## Out of Scope
- The `mcp_auth` exemption wording (disabled-auth Plan), the interrupted-startup section (exit-status Plan), and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make the edits as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (documentation matches the new order and the corrected short-circuit behavior)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
