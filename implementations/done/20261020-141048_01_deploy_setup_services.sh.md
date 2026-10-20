## Goal

Make the remote-LLM health gate in `deploy/setup_services.sh` classify each service the way
the agent's own startup does: `agent-llm` (required) stays fatal, `embed-llm` (optional)
becomes a non-fatal warning by default, and `LLM_GATE_STRICT=1` restores the current
"abort if either is not ready" behavior. The script then reaches the Event Bus block, prints
both statuses, and ends with a summary of what was started and what is degraded (REQ-001,
REQ-002, REQ-003, REQ-004).

## Scope

Only `deploy/setup_services.sh`:

- Replace the single `ready` flag in the gate (current lines 111-130) with per-service flags
  and a per-service severity decision.
- Add the `LLM_GATE_STRICT` (new) switch (default off).
- Print a `[WARN]` and continue when `embed-llm` is unreachable in the default mode.
- Make the existing `ヘルスチェック` echo lines (current 163-167) report each service's real
  state instead of the fixed "上記ゲートで確認済み".
- Print a started/degraded summary before the final completion banner.

The pre-flight checks (lines 22-74), `read_llm_base`, and the Event Bus block (lines
134-161, including the `require_env_vars "Event Bus"` credential gate) are left untouched.

## Assumptions

- `check_service_health` (`scripts/agent/services/mcp_health.py`) is the reference: `llm`
  required, `embed-llm` optional.
- `ebsec001` is already implemented: the Event Bus block uses `uv run` and is preceded by the
  credential gate, which still exits non-zero without `EVENTBUS_AUTH_TOKEN`.
- `LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL` keep their current meaning and defaults.
- No test file under `tests/` exercises this gate (`rg` over `tests/` finds only
  `tests/deploy/test_load_env_gate.py`, which sources `load_env.sh`, not the gate).

## Design decisions

- **Per-service flags, one failure helper.** `embed_ok` (new) and `llm_ok` (new) are
  recomputed each attempt from the last HTTP code. A `gate_fail` (new) function holds the
  existing three `[FATAL] LLM services did not become ready ...` echo lines and `exit 1`, so
  the `agent-llm` branch and the strict-mode `embed-llm` branch emit identical text.
- **Wait loop unchanged.** The loop still waits up to `LLM_HEALTH_RETRIES` attempts for both
  services and exits early only when both are ready. In the default mode an unreachable
  `embed-llm` therefore still costs the full wait before the warning (see Plan Gap in
  Details); shortening it needs a new knob the Plan does not define.

## Alternatives considered

- Exit the loop as soon as `agent-llm` is ready in the default mode. Rejected for this row:
  it would stop waiting for a slow-loading `embed-llm` and adds behavior the Plan does not
  specify; recorded as a Plan Gap instead.

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

1. Add `LLM_GATE_STRICT` (new) next to `LLM_HEALTH_RETRIES`, defaulting to `0`.
2. Rewrite the wait loop to set `embed_ok` / `llm_ok` (new) and break only when both are 1.
3. Add `gate_fail` (new) and the severity decision after the loop.
4. Set `EMBED_STATE` (new) and `LLM_STATE` (new) for the later output.
5. Capture the Event Bus PID in `EB_PID` (new) right after the launch line.
6. Update the `ヘルスチェック` echo lines and add the summary block before the completion banner.

### Method

- Gate shape (all conditionals are explicit `if` tests; `curl` keeps `|| true`):

  ```bash
  LLM_GATE_STRICT="${LLM_GATE_STRICT:-0}"

  gate_fail() {
      echo "[FATAL] LLM services did not become ready within ${LLM_HEALTH_RETRIES} attempts (~$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))s)." >&2
      echo "  embed-llm (${HEALTH_URL_EMBED}): last status ${code_embed:-unreachable}" >&2
      echo "  agent-llm (${HEALTH_URL_LLM}): last status ${code_llm:-unreachable}" >&2
      exit 1
  }

  embed_ok=0; llm_ok=0
  for (( attempt=1; ... )); do
      code_embed=$(curl ... || true); code_llm=$(curl ... || true)
      embed_ok=0; llm_ok=0
      if [ "${code_embed}" = "200" ]; then embed_ok=1; fi
      if [ "${code_llm}" = "200" ]; then llm_ok=1; fi
      if [ "${embed_ok}" -eq 1 ] && [ "${llm_ok}" -eq 1 ]; then break; fi
      echo "  ...待機 ..."; sleep "${LLM_HEALTH_INTERVAL}"
  done

  if [ "${llm_ok}" -ne 1 ]; then gate_fail; fi
  if [ "${embed_ok}" -ne 1 ]; then
      if [ "${LLM_GATE_STRICT}" = "1" ]; then gate_fail; fi
      echo "[WARN] embed-llm unreachable (...): continuing; RAG embedding features are degraded" >&2
  else
      echo "OK: remote LLM services healthy (embed-llm=..., agent-llm=...)"
  fi
  ```

- When only `agent-llm` is healthy the OK line is replaced by the `[WARN]` line; when both
  are healthy the OK line text is unchanged (AC-04).
- `EMBED_STATE` (new) is `healthy` or `UNREACHABLE (last status ${code_embed:-unreachable}) - degraded, non-fatal`;
  `LLM_STATE` (new) is `healthy`.
- Summary block (printed before `=== setup_services.sh: 完了 ===`): one line per service
  naming URL and state, plus `Event Bus (:8015, PID ${EB_PID}): started`.

### Details

- **Credential gate ordering.** The Event Bus block's `require_env_vars` can still exit 1
  after the LLM gate when `EVENTBUS_AUTH_TOKEN` is missing; that is `ebsec001`'s behavior and
  is not changed here. The summary must therefore be reached only after a launch, never on
  that failure path (it sits after the launch line, so this holds).
- **Plan Gap (reported, not applied).** With `embed-llm` down in the default mode the script
  still waits the full `LLM_HEALTH_RETRIES x LLM_HEALTH_INTERVAL` (about 150 s by default)
  before warning, because the loop only exits early when both services are ready. The Plan's
  Reason for Change cites that wait; closing it needs a Plan revision (for example an
  early-exit rule or a separate embed wait budget).
- `set -euo pipefail` (line 12) stays; `read_llm_base` and the "base URL(s) not configured"
  fatal stay as they are.
- Keep log and message strings in English like the existing `[FATAL]` lines; leave the
  Japanese comments and progress text that already exist unchanged.

## Compatibility considerations

Default behavior changes: an unreachable `embed-llm` no longer aborts the script, and the
exit code is 0 in that case. `LLM_GATE_STRICT=1` restores the old either-or abort with the
same message text. An unreachable `agent-llm` still aborts by default. Operators or CI that
relied on the abort for `embed-llm` must set `LLM_GATE_STRICT=1`.

## Security considerations

N/A: no credential handling changes; the script keeps passing the Event Bus token only through
the existing `Authorization` header and never prints it. The new summary prints URLs and
states only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

Ad hoc script-level harness kept outside the repository (the Plan scopes the committed diff
to three files, UNK-02). It copies the script into a temporary root with `/opt/llm` rewritten
to a temporary directory, so no production path is read or written, and puts stub `curl`,
`uv`, and `sqlite3` on PATH with `EVENTBUS_AUTH_TOKEN` set. Cases, with
`LLM_HEALTH_RETRIES=1` and `LLM_HEALTH_INTERVAL=0`:

- both healthy: exit 0, OK line unchanged, summary shows both healthy and the Event Bus started
  (AC-04);
- `embed-llm` down, default mode: exit 0, `[WARN]` printed, Event Bus block reached, summary
  shows `embed-llm` degraded (AC-01);
- `embed-llm` down with `LLM_GATE_STRICT=1`: exit 1 with the unchanged `[FATAL] LLM services
  did not become ready ...` text (AC-02);
- `agent-llm` down, with and without `embed-llm` down: exit 1 by default (AC-03);
- pre-flight failure (missing workflow JSON): exit 1 before any LLM health request (AC-07);
- `EVENTBUS_AUTH_TOKEN` unset with both healthy: the credential gate still aborts.

Also `bash -n deploy/setup_services.sh` and `shellcheck` if installed (otherwise record as
not available).

## Completion criteria

- Per-service severity: `agent-llm` fatal, `embed-llm` warning by default, fatal under
  `LLM_GATE_STRICT=1` with the unchanged message.
- The Event Bus block is reached when only `embed-llm` is down in the default mode.
- The `ヘルスチェック` lines and the summary never claim an unreachable service was confirmed.
- All harness cases above give the stated outcome and `bash -n` is clean.

## Out of Scope

- Any change to the pre-flight checks, `read_llm_base`, or the Event Bus block.
- A shorter wait for `embed-llm` (Plan Gap above).
- Committing the harness, and the two documentation rows (seq 02, seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the per-service gate, strict switch, warning, echo update, and summary in `deploy/setup_services.sh` | Completed | 20261020-185257 | 20261020-185257 | REQ-001, REQ-002, REQ-003, REQ-004 changed: deploy/setup_services.sh |
| 2 | Run the ad hoc four-state harness and the extra cases in Validation plan | Completed | 20261020-185257 | 20261020-185257 | AC-01..AC-04, AC-07 ad hoc harness (outside repo): 7 cases pass on new script; old script red on embed-down default; no production path written |
| 3 | Run `bash -n` and the validation sequence that applies to a shell script (`rules/toolchain.md`) | Completed | 20261020-185257 | 20261020-185257 | bash -n ok; shellcheck not available; targeted 16 passed; full suite 9663 passed, 14 skipped. Plan Gap recorded: default-mode embed-llm wait still full retry budget |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261020-130914_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-141048
- **Related target files**: deploy/setup_services.sh