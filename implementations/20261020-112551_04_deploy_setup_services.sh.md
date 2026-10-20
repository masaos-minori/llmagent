## Goal
Make `deploy/setup_services.sh` load the operator `.env` file, stop with an actionable `[FATAL]` gate when the
Event Bus configuration references a variable that is unset or empty, start the Event Bus through the production
venv, and authenticate both Event Bus health probes.

## Scope
- Source `deploy/load_env.sh` after `REPO_ROOT` is defined (line 17 region).
- Add the `.env` selection and `parse_env_file` (new) call, the Event Bus configuration selection, and the
  `require_env_vars` (new) gate immediately before the Event Bus section (lines 131-135).
- Replace the bare `python -m eventbus.app` launch with the production `uv run` form used elsewhere in the
  script (for example line 28).
- Add the bearer header to the health probe at line 137 and the checklist probe at line 143.

## Assumptions
- The script runs under `set -euo pipefail` (line 12), so every new expansion of a possibly-unset variable uses
  the `:-` form, and no new bare `[ ... ] && cmd` statement is added at top level.
- `/health` requires the monitoring role and the shared `auth_token` holds it, so the shared token is the correct
  credential for a probe.
- `deploy/deploy.sh` has already copied `config/eventbus.toml` to `/opt/llm/config/eventbus.toml`, so the
  deployed file is the one gated.
- Names written with the (new) marker are constructs introduced by this cycle, not constructs this file already
  has: the two gate functions come from seq 03's library, and the header variable and the environment variable
  name are introduced by seq 02 and seq 04. The tool's scoped-path rule cannot read a `.sh` citation, so the
  marker is what keeps those citations from being reported as stale.

## Design decisions
- The `.env` load and the gate sit directly above the Event Bus launch rather than at the top of the script: the
  gate is about the Event Bus only, and placing it there keeps the existing workflow checks unchanged.
- Configuration precedence copies `deploy/start_agent.sh` lines 102-110 (deployed file first, repository file as
  fallback) so the gate reads the same file the launched process will read.
- `EVENTBUS_AUTH_TOKEN` (new) is expanded with `:-` in the probes: the script must not abort under `set -u` if a host
  keeps a literal token in its deployed TOML, and an unauthenticated probe then reports a failure instead of
  killing the deployment.
- One `EB_AUTH_HEADER` (new) variable is defined once and reused by both probes so the two probes cannot drift.

## Alternatives considered
- Gate on a hardcoded variable list: rejected; `REQ-003` requires the gate to follow whatever the Event Bus
  configuration references, which is what `collect_required_env_vars` (new) provides.
- Keep the bare `python -m eventbus.app`: rejected; it uses whatever interpreter is on `PATH` instead of the
  production venv pinned by `UV_PROD_FLAGS`, which is `REQ-004`.
- Probe without a token and accept 401: rejected; `AC-5` requires the probe to be authenticated so a 401 is not
  confused with a healthy service.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. Source the shared library after `REPO_ROOT`.
2. In the Event Bus section: load the `.env` file, select the Event Bus configuration file, and run the gate
   before launching.
3. Launch through `uv run`.
4. Authenticate both probes.

### Method
- Four edits, all inside the existing Event Bus section plus one line group after line 17.
- The gate label is `Event Bus` and the re-run command is `bash deploy/setup_services.sh`, matching the script's
  documented usage in its own header.
- The launch keeps the existing log redirection and backgrounding so the PID line and the later checklist stay
  valid.

### Details
Edit 1:

```bash
# Before:
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# After:
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# .env パースと必須環境変数ゲートの共有ライブラリ（sourcing 専用。set オプションは本スクリプトの責任）
source "${REPO_ROOT}/deploy/load_env.sh"
```

Edit 2 (launch and gate; the `# After:` block replaces the four lines shown in `# Before:`):

```bash
# Before:
# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"
PYTHONPATH=/opt/llm/scripts \
    python -m eventbus.app \
    >> /opt/llm/logs/eventbus.log 2>&1 &
# After:
# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"

ENV_FILE=""
if [[ -f "/opt/llm/.env" ]]; then
    ENV_FILE="/opt/llm/.env"
elif [[ -f "${REPO_ROOT}/.env" ]]; then
    ENV_FILE="${REPO_ROOT}/.env"
fi
if [[ -n "${ENV_FILE}" ]]; then
    parse_env_file "${ENV_FILE}"
fi

EVENTBUS_CONFIG=""
if [[ -f "/opt/llm/config/eventbus.toml" ]]; then
    EVENTBUS_CONFIG="/opt/llm/config/eventbus.toml"
elif [[ -f "${REPO_ROOT}/config/eventbus.toml" ]]; then
    EVENTBUS_CONFIG="${REPO_ROOT}/config/eventbus.toml"
fi
require_env_vars "Event Bus" "bash deploy/setup_services.sh" "${EVENTBUS_CONFIG}"

EB_AUTH_HEADER="Authorization: Bearer ${EVENTBUS_AUTH_TOKEN:-}"

PYTHONPATH=/opt/llm/scripts UV_SYSTEM_CERTS=true \
    uv run "${UV_PROD_FLAGS[@]}" python -m eventbus.app \
    >> /opt/llm/logs/eventbus.log 2>&1 &
```

Edit 3:

```bash
# Before:
echo "  Health: $(sleep 2 && curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
# After:
echo "  Health: $(sleep 2 && curl -s -H "${EB_AUTH_HEADER}" http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
```

Edit 4:

```bash
# Before:
echo "  eventbus       (:8015): $(curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
# After:
echo "  eventbus       (:8015): $(curl -s -H "${EB_AUTH_HEADER}" http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
```

## Compatibility considerations
- The existing pre-flight, workflow-schema, and remote LLM health sections are untouched. The remote LLM gate at
  lines 108-129 still aborts before the Event Bus section; that is the separate defect tracked by
  `issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md` and is out of scope here.
- `UV_PROD_FLAGS` (line 14) is already defined in this script, so the launch change adds no new variable.
- A host whose deployed TOML still holds a literal token keeps starting; only the probe wording changes.

## Security considerations
- No token value is printed: the gate prints variable names and a generation hint, and the probes pass the token
  on the command line of a loopback request only.
- Fail-closed: the gate exits 1 before the background process is spawned, so a missing credential can no longer
  appear as a silently dying process.
- `EB_AUTH_HEADER` (new) is assigned once and never exported, so child processes of the script do not inherit it
  through this change.

## Rollback considerations
Single-path revert: `git checkout HEAD -- deploy/setup_services.sh`. seq 03 (`deploy/load_env.sh`) can stay in
the tree unused without affecting the agent, but if seq 03 is also removed the source line must be removed with
it.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Syntax | `bash -n deploy/setup_services.sh` | no output, exit 0 |
| Static | `grep -n 'uv run' deploy/setup_services.sh` | the Event Bus launch line appears with `UV_SYSTEM_CERTS=true` and `"${UV_PROD_FLAGS[@]}"` |
| Static | `grep -c 'curl -s -H "${EB_AUTH_HEADER}"' deploy/setup_services.sh` | 2 (both probes reuse the one header variable) |
| Gate | `uv run pytest tests/deploy/test_load_env_gate.py -q -p no:randomly` | green (seq 06 exercises the library the script sources) |

## Completion criteria
- `bash -n` is clean and the four edits are present.
- No unguarded expansion of `EVENTBUS_AUTH_TOKEN` (new) exists (every use is `${EVENTBUS_AUTH_TOKEN:-}`).
- Both Event Bus probes send the bearer header.

## Out of Scope
- The embed-llm / agent-llm health gate (ebops002) and any retry or skip flags for it.
- systemd units, service restarts, and writing a real token into `/opt/llm/.env` (Plan Out-of-Scope).
- `deploy/start_agent.sh` and `deploy/deploy.sh`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-131116 | 20261020-131116 | four edits applied at :17 and the Event Bus section; all Before anchors matched source |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-131116 | tests are owned by seq 06 N/A here: gate behavior executed by the seq 06 cases (8 green) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-131116 | bash -n clean; launch line now carries UV_SYSTEM_CERTS=true and the UV_PROD_FLAGS array; probe-count grep = 2; the doc's original grep -c 'Authorization: Bearer' pattern was wrong (probes reference the variable, literal appears once) and the Validation row was corrected |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-131116 | docs are owned by seq 07, 08 N/A: docs owned by seq 07, 08; end-to-end run of this script stays blocked by ebops002 |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `deploy/setup_services.sh`, `deploy/load_env.sh` (seq 03),
  `config/eventbus.toml` (seq 02), `tests/deploy/test_load_env_gate.py` (seq 06),
  `deploy/start_agent.sh` (read-only source of the precedence pattern)