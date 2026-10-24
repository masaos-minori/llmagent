---
name: mcp-server-add
description: |
  Use this skill PROACTIVELY when adding a new MCP (Model Context Protocol) server
  to this project. Use this when the task involves creating a new MCP server module
  and wiring it into the agent: config files, tool registration, tests, deployment,
  and end-to-end verification.
---

# MCP Server Add Skill

## Purpose

Add a new MCP server end-to-end: server files, config and registration, tests,
deployment, reachability verification. There is no installer or wizard (`/mcp` accepts
only `status` and `tools`); the files are created by hand.

## Required reading

`routing.md` loads this skill's files, `rules/env.md`, and two MCP docs. Also read:

- `docs/22_mcp/mcp_06_12_new-mcp-server-addition-checklist.md` — the canonical addition
  checklist. This skill orders and verifies it; it MUST NOT replace or restate it.
- `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` — tool registration; the live
  `/v1/tools` response is the sole routing basis, and `tool_names` is not a routing input.
- `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` — the `auth_token` every HTTP MCP
  server needs.

## Existing MCP servers (reference)

Port/role table (canonical): `docs/22_mcp/mcp_01_system_overview.md` Server Catalog.
Module paths: `scripts/mcp_servers/<name>/<name>_server.py` (plus `<name>_service.py`,
`<name>_models.py`, `<name>_tools.py`), e.g. `scripts/mcp_servers/web_search/web_search_server.py`.
Servers differ in the extra modules they carry; follow the closest existing server.

New servers MUST use the next free port above every port currently assigned — derive it at
task time (see Prerequisites), per `skills/DESIGN.md` No concrete configuration values.
MUST NOT state the assigned port number in `docs/*.md` once deployed — see
`skills/DESIGN.md` Docs content policy — remove.

## Prerequisites

- The assigned port: the highest MCP server port in `config/agent.toml` plus one.
  `rg -o 'url\s*=\s*"http://127\.0\.0\.1:(\d+)"' -r '$1' config/agent.toml | sort -n | tail -1`
  → use the next integer above that result. MUST NOT derive it from `init.d/`: its
  `--port` values belong to the LLM services, not to the MCP servers (every MCP server is
  `startup_mode = "subprocess"` and is started by the agent).
- To start or restart the agent for verification, see Step 7.

## Phase overview

| Phase | Steps | Goal | Gate |
|---|---|---|---|
| 1 Create | Step 1 | Server files and the server's config file exist and are valid | Step 1's checklist fully passes |
| 2 Register | Steps 2–4 | config copy, binary build/list/staleness entries, `config/agent.toml`, and tool registration updated | `rg` confirms the new `cp` line, the `ENTRIES`, `BINARY_NAMES`, and `BINARY_SOURCES` entries, the `[mcp_servers.<name>]` section (with `auth_token` and `cmd`), `tool_definitions`, `tool_safety_tiers`, and `shared/tool_constants.py` entries all exist |
| 3 Verify | Step 5 | Tests and validation pass before anything is deployed | the Step 5 commands all pass |
| 4 Run | Steps 6–9 | Binary built and deployed (the `deploy` skill's approval gate), started, authenticated, and reachable | `/mcp status` shows the new server `OK` and one of its tools was called successfully |
| (final) | Step 10 | Completion checklist (below) confirmed | Every Completion checklist item is true, or execution stopped in a `Blocked` state |

See `workflow.md` for detailed step content and idempotency notes.

## Completion checklist

**This task is complete when, and only when**: every item below is confirmed true, or
execution stopped in a `Blocked` state per a `workflow.md` step's own bound, or at the
`deploy` skill's approval gate.

- the server module syntax check passes and the Step 1 checklist passes
- `deploy/deploy.sh` has a `cp` line for the new server's `config/<name>_mcp_server.toml` and `mcp_<name>` in `BINARY_NAMES`
- `deploy/build_binaries.sh` has the `ENTRIES` entry and `tools/manage_binaries.py` has the `BINARY_SOURCES` entry for `mcp_<name>`; `skills/deploy/workflow.md` Phase 1's list checks print no difference
- `config/agent.toml` has `[mcp_servers.<name>]` (with `startup_mode = "subprocess"`, `auth_token`, and `cmd` pointing at the binary), `[[tool_definitions]]` entries, and `tool_safety_tiers` entries for every new tool
- every new tool is declared in the server's `GET /v1/tools` response (schema 2.0) and in the `shared/tool_constants.py` frozenset
- tests for the new server exist under `tests/mcp_servers/<name>/` and pass
- the generated MCP reference table is current: `uv run python tools/generate_reference_table.py --check` exits 0
- the other applicable `routing.md` Tools → "When to run which tool" checkers pass (Step 5)
- `uv run python tools/check_docs_consistency.py --domain mcp` passes when docs were edited
- the service is running, `/mcp status` shows the new server `OK`, and one tool of the new server was called successfully
- no errors mentioning the server in `agent.log`

## Composes with

- `deploy` — Step 6 delegates to the deploy skill's Phases 1, 1b, and 2, and Step 7 to its Phase 3; these are distinct from this skill's phases

## Called by

- `issue-to-plan` — when a plan includes adding a new MCP server

## Required behavior

- Use the port computed in Prerequisites; re-run its command immediately before assigning
  it, because another change may have taken it.
- Use `ConfigLoader().load(...)` to read the new server's config module (an instance of
  `rules/coding.md`'s `config_loader.py`-only `json.load()` rule — See `rules/coding.md`,
  section "Constraint checks (run before every commit)").
- MUST NOT deploy to `/opt/llm` or start or restart services without the user's explicit
  approval: this changes shared infrastructure (`AGENTS.md` Execution policy). The approval
  gate is the `deploy` skill's (`skills/deploy/workflow.md` Phase 2); this skill does not
  duplicate or bypass it.

See `rules/coding.md` Mandatory conventions ("Module addition", "MCP server addition"
rows) for the `deploy/deploy.sh` `cp` line and `config/agent.toml`
`[mcp_servers.<name>]` requirements.

## Improvement feedback

If a step was missing or a registration point changed: update `workflow.md`, and update
`docs/22_mcp/mcp_06_12_new-mcp-server-addition-checklist.md` when the change is to the
checklist itself.
