## Goal

Start the agent via its compiled binary instead of `uv run python -m agent.repl`, and export `LLMAGENT_CONFIG_DIR` and `LLMAGENT_SUDACHI_DICT` so the binary resolves the external config directory and Sudachi dictionary. Implements `REQ-007` / AC-09.

## Scope

Modifies `deploy/start_agent.sh`: replace the final launch line (line 186) with the binary invocation plus the two environment-variable exports. The `.env` parsing, required-env-var listing, and workflow validation above are unchanged.

## Assumptions

- Line 186 currently reads `PYTHONPATH="${PYTHONPATH}" UV_SYSTEM_CERTS=true uv run python -m agent.repl`.
- The agent binary lives at `/opt/llm/bin/agent` (built by `deploy/build_binaries.sh`).
- The deployed config directory is `/opt/llm/config` and the dictionary is `/opt/llm/dict/system.dic` (placed by `deploy/deploy.sh`).

## Design decisions

- Export `LLMAGENT_CONFIG_DIR="/opt/llm/config"` and `LLMAGENT_SUDACHI_DICT="/opt/llm/dict/system.dic"` before launching the binary, so the resolver uses the external files (fail-fast if missing, per AC-01/AC-05).
- Replace the `uv run python -m agent.repl` line with a direct exec of `/opt/llm/bin/agent`, preserving the `UV_SYSTEM_CERTS` setting used elsewhere in the script.

## Alternatives considered

- Relying on the binary's compiled-adjacent `config/` branch: rejected — the plan makes the config directory explicit via `LLMAGENT_CONFIG_DIR` for clarity and testability, and the dictionary cannot use the adjacent branch (it is not bundled), so `LLMAGENT_SUDACHI_DICT` must be set regardless.

## Implementation

### Target file

`deploy/start_agent.sh`

### Procedure

Replace the launch line and add the two exports.

### Method

1. Before the `=== AgentREPL 起動中 ===` block (or immediately before the launch), add:
   ```bash
   export LLMAGENT_CONFIG_DIR="${DEPLOY_CONFIG}"
   export LLMAGENT_SUDACHI_DICT="/opt/llm/dict/system.dic"
   ```
   where `${DEPLOY_CONFIG}` is the already-defined deployed-config directory variable (confirm its name in the script; default `/opt/llm/config`).
2. Replace line 186 `PYTHONPATH="${PYTHONPATH}" UV_SYSTEM_CERTS=true uv run python -m agent.repl` with:
   ```bash
   UV_SYSTEM_CERTS=true /opt/llm/bin/agent
   ```
   Keep the `UV_SYSTEM_CERTS` export consistent with the rest of the script.

### Details

- Keep the fail-fast behavior: if `/opt/llm/config` or `/opt/llm/dict/system.dic` is missing, the resolver raises an explicit error naming the path (AC-01, AC-05).
- Do not change the `.env` parsing or the required-env-var listing; they precede the launch and are unaffected.

## Compatibility considerations

- Reverting line 186 to `uv run python -m agent.repl` and removing the two exports restores the pre-change path. The `uv run` path keeps working because `scripts/` stays deployed.

## Security considerations

- N/A: the exports only set the resolver inputs; the CommandValidator still gates the binaries at start time. Ensure the dictionary path points at the trusted `/opt/llm/dict/system.dic`, not a world-writable location.

## Rollback considerations

- N/A: revert the commit; the change is one replaced line plus two exports.

## Validation plan

- Deploy smoke test: after deploying, `/opt/llm/start_agent.sh` starts the agent binary and the agent lists MCP servers via the binary entries (AC-09).
- Confirm the agent resolves `/opt/llm/config` and `/opt/llm/dict/system.dic` (no silent fallback).

## Completion criteria

- `start_agent.sh` launches `/opt/llm/bin/agent` with `LLMAGENT_CONFIG_DIR` and `LLMAGENT_SUDACHI_DICT` exported; the deploy smoke test passes.

## Out of scope

- The build script (`deploy/build_binaries.sh`), the `cmd` rewrite (`config/agent.toml`), and the deploy rows.

## Implementation notes

- **Placement.** The two `export`s go immediately before the `# ── AgentREPL 起動` section (after the workflow-validation gate), so they are set only after all prior fail-fast checks pass.
- **`${DEPLOY_CONFIG}`.** Reuses the already-defined deployed-config variable (line 147, `/opt/llm/config`) rather than hard-coding the path — consistent with the script's other `DEPLOY_*` variables.
- **No `PYTHONPATH` on the launch line.** The Nuitka `--onefile` binary is self-contained; the `PYTHONPATH="${REPO_ROOT}/scripts"` export (line 22) is retained for any residual interpreter use but is not needed by the binary. The `UV_SYSTEM_CERTS=true` prefix is kept inline to match the other `uv` invocations in the script.
- **No `exec` builtin.** Method step 2 specifies `UV_SYSTEM_CERTS=true /opt/llm/bin/agent`; interactive Ctrl+C delivers SIGINT to the foreground process group either way.
- **`set -e` safety.** `LLMAGENT_SUDACHI_DICT` points at `/opt/llm/dict/system.dic` which `deploy.sh` creates (warn-if-missing); the resolver then fails fast at runtime if the file is absent (AC-01/AC-05), so a deploy-time warn does not mask a real missing dict.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `LLMAGENT_CONFIG_DIR`/`LLMAGENT_SUDACHI_DICT` exports | Completed | 20261012 | 20261012 | `${DEPLOY_CONFIG}`(/opt/llm/config) を使用。missing は resolver が fail-fast (AC-01/AC-05) |
| 2 | Replace the launch line with the agent binary | Completed | 20261012 | 20261012 | `UV_SYSTEM_CERTS=true /opt/llm/bin/agent`(run-time の PYTHONPATH 不要・system cert は inline 維持) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012 | 20261012 | bash -n 合格。launch セクションを stub バイナリで分離実行 (exports 値・binary 呼出確認)+ resolver fail-fast 2件確認 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261012 | 20261012 | N/A |

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
- **Related target files**: deploy/start_agent.sh
