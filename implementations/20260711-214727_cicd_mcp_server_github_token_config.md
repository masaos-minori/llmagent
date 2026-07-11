# Implementation Procedure: config/cicd_mcp_server.toml — configure GITHUB_TOKEN

Source plan: `plans/20260711-200907_plan.md` — Phase 2 (Core Logic Implementation)

## Goal

Provide a valid GitHub PAT to the CICD MCP server so its 4 tools (`trigger_workflow`, `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs`) become operational once `startup_mode` is restored (companion doc `20260711-214700_agent_toml_cicd_rag_pipeline_startup_mode_subprocess.md`).

## Scope

**In:**
- `config/cicd_mcp_server.toml:27` (or the equivalent `github_token` key location): set to a valid PAT, OR configure via environment variable instead, per the security consideration below.

**Out:**
- No change to server internal logic or API contracts.
- No conditional startup based on token presence.
- No attempt to make `/health` return 200 without a GitHub token — explicitly out of scope per the plan (limited value, since all 4 CICD tools require the token regardless).

## Assumptions

1. **This is the plan's one explicitly Blocking unknown (UNK-01, marked `Blocking: True`)**: "Whether a valid GitHub PAT is available and authorized for the required repositories" has **no resolution path recorded in the plan beyond 'ask user for the token or confirm provisioning status.'** This implementation procedure document describes *how* to wire the token in once it is available — it does NOT itself supply, generate, or confirm a token value. Whoever executes this procedure must first obtain a valid PAT through the organization's normal credential-provisioning process before this step can be completed; do not fabricate, guess, or request a token value be pasted into chat/logs.
2. Per the plan's Risk table: token exposure if committed to the repository is a real risk (Likelihood: Medium) — environment-variable configuration is preferred over writing the raw token into `config/cicd_mcp_server.toml` where it could be committed accidentally.
3. This change is independent of `config/agent.toml`'s `startup_mode` change (companion doc) but both must be in place for the `cicd` server to be genuinely operational — `startup_mode = "subprocess"` alone starts the process; this token is what makes its tools actually succeed at call time.

## Implementation

### Target file

`config/cicd_mcp_server.toml`

### Procedure

1. Confirm with the operator/user (out-of-band, via a secure credential channel — not via this document or any command output) that a valid GitHub PAT exists and is authorized for the repositories the CICD tools need to operate against.
2. Choose one of two configuration approaches:
   - **Environment variable (preferred, per Assumption 2)**: set `GITHUB_TOKEN` (or the specific env var name `cicd_mcp_server.toml`'s loader expects — confirm by reading how `github_token` is resolved in `scripts/mcp_servers/cicd/` at implementation time) in the deployment environment (e.g. systemd unit env file, `.env` loaded by the process manager) rather than the TOML file.
   - **Config file** (only if the loader does not support environment-variable resolution, or per existing repo convention): set `github_token = "<PAT value>"` directly in `config/cicd_mcp_server.toml`, ensuring this file is excluded from version control if it contains a live secret (confirm `.gitignore` coverage before committing anything).
3. Apply the same configuration to both `/opt/llm` (production) and this repository's development environment, per the plan's Deploy Impact section — as two independent, environment-specific credential provisioning actions (do not copy the same literal secret value between environments if the organization's security policy requires per-environment tokens; confirm this policy before proceeding).

### Method

Credential configuration, not code change — either an environment-variable set in the deployment environment, or (if unavoidable) a config-file value edit. No TOML schema change beyond populating an already-defined key.

### Details

- Never print, log, or commit the actual token value as part of executing this procedure.
- If the config file approach is used, verify the file is listed in `.gitignore` (or an equivalent secret-exclusion mechanism) before considering this step complete — a leaked PAT is a security incident, not a rollback-able mistake.
- Track token expiration/rotation per the plan's Risk table ("Token expiration causing silent degradation," Likelihood Low-Medium) — this is a long-term follow-up (e.g. a watchdog alert for expiring tokens), not part of this immediate fix.

## Validation plan

Filtered from the plan's Validation Plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Secret validation | Check file/env contains a non-empty `github_token`/`GITHUB_TOKEN` (without printing its value) | Token value present |
| cicd server | `cd /opt/llm && uv run python scripts/mcp_servers/cicd/server.py &` | Server starts without crash |
| Health endpoint | `curl http://127.0.0.1:8012/health` | HTTP 200 |
| CICD functionality | `curl -X POST http://127.0.0.1:8012/v1/call_tool ...` (e.g. `get_workflow_status` against a known repo/workflow) | Tool call succeeds, not an auth-failure error |
