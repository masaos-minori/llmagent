# Implementation Procedure: `config/shell_mcp_server.toml` (shell_sandbox_backend none → firejail)

## Goal

Set `shell_sandbox_backend = "firejail"` in `config/shell_mcp_server.toml` (line 31), replacing `shell_sandbox_backend = "none"`, so that AgentREPL can start (the `"none"` value is a fatal startup blocker per `scripts/agent/services/security_audit.py:90`) and shell commands run inside sandbox isolation. The `firejail` binary MUST be installed on the deployment host before this change takes effect (see Ordering below).

## Scope

Line 31 of `config/shell_mcp_server.toml` only: the scalar value `"none"` → `"firejail"`. The surrounding comment block (lines 27-30), which already documents the firejail requirement and the binary-missing startup behavior, is left intact. No other key, comment, or file changes.

## Assumptions

- The deployment host uses apt-based package management with privileges to install system packages (`firejail` is currently NOT installed — see UNK-01).
- `"firejail"` is the only viable non-fatal backend: `scripts/shared/protocols/shell.py` validates only `"firejail"` / `"none"`, and `"none"` is fatal everywhere, so firejail must be installable for the agent to run at all.
- Changing the repo default affects every environment (dev included), because `"none"` is fatal regardless of environment (`security_audit.py:89-91`).

## Design decisions

- Single textual substitution `shell_sandbox_backend = "none"` → `shell_sandbox_backend = "firejail"` on line 31. Only the quoted scalar changes; the key, spacing, and surrounding comments are untouched.
- Load-bearing ordering: `firejail` MUST be installed and confirmed on PATH **before** this config switch. If the config becomes `"firejail"` while the binary is absent, `init_sandbox()` (`scripts/mcp_servers/shell/shell_service_static_helpers.py:34-37`) raises `RuntimeError` and the agent still cannot start. So installation is Phase 1 and the config edit is Phase 2.
- No Python code, interface, schema, or module-boundary change is involved.

## Alternatives considered

- **Keep `shell_sandbox_backend = "none"`**: rejected — it is a fatal startup blocker (`security_audit.py:90`); AgentREPL cannot start.
- **Add a new sandbox backend beyond `"firejail"` / `"none"`**: rejected — out of scope; the protocol (`shell.py:41,56`) validates only those two values.

## Implementation

### Target file

`config/shell_mcp_server.toml`

### Procedure

1. **Prerequisite (must pass before step 2):** install `firejail` on the deployment host (`apt-get install -y firejail`) and confirm `command -v firejail` resolves to an executable. If it cannot be installed, STOP — the task cannot proceed without a sandbox backend (UNK-01, blocking).
2. Open `config/shell_mcp_server.toml`.
3. At line 31, change:
   `shell_sandbox_backend = "none"`
   to:
   `shell_sandbox_backend = "firejail"`
4. Leave the comment block on lines 27-30 unchanged.
5. (Context, not a file edit here) Redeploy via `bash deploy/deploy.sh` so `/opt/llm/config/shell_mcp_server.toml` matches the repo, then run `bash /opt/llm/start_agent.sh` and confirm `security_audit` passes (no fatal sandbox error) and shell tool calls execute within the sandbox.

### Method

Textual edit of the scalar token only. Locate line 31 with `rg -n 'shell_sandbox_backend' config/shell_mcp_server.toml` (expected: line 31), confirm it reads `shell_sandbox_backend = "none"`, then replace only the `"none"` literal with `"firejail"`. Do not touch the key, quotes, spacing, or the comment block above it.

### Details

- Line 31 (current): `shell_sandbox_backend = "none"` — fatal per `scripts/agent/services/security_audit.py:90` (`"shell_sandbox_backend=none is not permitted"`), recorded FATAL at `scripts/agent/startup_validation.py:48-53`.
- Guarded by the comment block lines 27-30, which already states production uses `"firejail"` (requires `apt-get install firejail`) and that a missing binary raises at startup — keep these as-is.
- When set to `"firejail"`, `security_audit.py:103-106` and `shell_service_static_helpers.py:34-36` require the `firejail` binary in PATH; hence the Phase 1 prerequisite.

## Compatibility considerations

- The repo default change propagates to all environments via `deploy.sh` (rsynced to `/opt/llm/config/`). Because `"none"` is fatal everywhere, firejail must be available wherever the agent runs; otherwise startup re-fails. Confirm the binary is installed on every host the agent starts on.
- `firejail` is supported once installed; no code or config-schema change accompanies this scalar.

## Security considerations

- This change is a security hardening: it enforces sandbox isolation for shell tool calls, removing unsandboxed arbitrary-command execution. Preserve it; do not weaken back to `"none"`. Verify a real shell tool call completes within sandbox isolation during validation.

## Rollback considerations

- There is **no safe revert**: reverting line 31 back to `"none"` re-introduces the fatal startup error (`security_audit.py:90`) in every environment. The only durable state is `"firejail"` with the binary installed. If firejail cannot be installed, the correct action is to leave the config as `"firejail"` and escalate (provide firejail or expand backend options) rather than revert.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `firejail` (system) | Integration — binary present | `command -v firejail` | Resolves to an executable path |
| `config/shell_mcp_server.toml` | Static — value switched | `grep 'shell_sandbox_backend' config/shell_mcp_server.toml` | Reads `shell_sandbox_backend = "firejail"` on line 31 |
| `/opt/llm/config/shell_mcp_server.toml` | Static — deployed matches repo | `diff config/shell_mcp_server.toml /opt/llm/config/shell_mcp_server.toml` | Identical |
| AgentREPL startup | Integration — startup runs | `bash /opt/llm/start_agent.sh` | `security_audit` reports OK (not FATAL); no `shell_sandbox_backend=none` fatal error; shell tool calls work within the sandbox |

## Completion criteria

- Line 31 of `config/shell_mcp_server.toml` reads `shell_sandbox_backend = "firejail"`; no `shell_sandbox_backend = "none"` remains in the file.
- `firejail` is installed and on PATH (`command -v firejail` resolves).
- After redeploy via `deploy.sh`, `/opt/llm/config/shell_mcp_server.toml` matches the repo.
- `bash /opt/llm/start_agent.sh` starts without the sandbox fatal error and shell tool calls execute within the sandbox.

## Out of scope

- Installing `firejail` is a host prerequisite (Phase 1) but is not a modification to any repository file.
- Any other key, comment, or file in `config/shell_mcp_server.toml`.
- Modifying the sandbox enforcement logic (`scripts/mcp_servers/shell/shell_service_static_helpers.py`, `scripts/agent/services/security_audit.py`, `scripts/shared/protocols/shell.py`, `subprocess_runner.py`).
- Adding sandbox backends beyond `"firejail"` / `"none"`.
- Documentation of `firejail` as a required deployment dependency (`REQ-005`): **outside this document's frozen scope.** The Plan's `Implementation Target Files` table contains no documentation row for REQ-005, and its target doc is flagged "Needs confirmation" (the `docs/02_deployment.md` referenced by `deploy.sh` no longer exists). It is not implemented here; a maintainer must confirm the doc/section before a documentation edit is made.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Install `firejail` and confirm on PATH (prerequisite; blocking if uninstallable) | Pending | — | — | REQ-001; UNK-01 |
| 2 | Switch `shell_sandbox_backend` on line 31 to `"firejail"` | Pending | — | — | REQ-002 |
| 3 | Run the validation sequence (binary present, value switched, deployed matches, startup OK) | Pending | — | — | REQ-002..REQ-004 |
| 4 | Update documentation (REQ-005) | Blocked | — | — | Target doc unconfirmed; outside frozen Implementation Target Files scope — needs maintainer decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `REQ-005` documentation target is unconfirmed and has no row in the frozen `Implementation Target Files` table | N/A: unresolved — escalated to maintainer | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 (set `shell_sandbox_backend = "firejail"` on line 31), REQ-003 (deployed copy matches repo), REQ-004 (startup succeeds within sandbox)
- **Source issue**: `issues/20261005-181900_enable_shell_sandbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-110027_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-174143
- **Related target files**: `config/shell_mcp_server.toml`
