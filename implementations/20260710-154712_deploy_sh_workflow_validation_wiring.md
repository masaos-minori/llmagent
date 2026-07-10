# Implementation: wire the workflow-validation CLI into `deploy.sh`

## Goal

Call `scripts/agent/workflow/validate.py` (from the companion implementation doc `implementations/done/20260710-154648_agent_workflow_validate_cli.md`) from `deploy/deploy.sh`, aborting deployment before any copy if validation fails.

## Scope

**In:**
- `deploy/deploy.sh`: add the validator call immediately after the pre-copy existence check (from `implementations/done/20260710-154614_deploy_sh_workflow_existence_checks.md`)

**Out:**
- No changes to the validator CLI itself

## Assumptions

1. This depends on `implementations/done/20260710-154614_deploy_sh_workflow_existence_checks.md` (existence check) and `implementations/done/20260710-154648_agent_workflow_validate_cli.md` (validator CLI) both being implemented first — this call is chained directly after the existence check.
2. `PYTHONPATH="${REPO_ROOT}/scripts"` (absolute path, not a bare relative `PYTHONPATH=scripts`) is used so the invocation is correct regardless of the caller's working directory, since `REPO_ROOT` is already resolved via `$(cd "$(dirname "$0")/.." && pwd)`.

## Implementation

### Target file

`deploy/deploy.sh`

### Procedure

1. Locate the pre-copy existence check block (added by the prerequisite implementation doc).
2. Immediately after it, insert:
   ```bash
   # Workflow: content validation (parseable JSON, required fields/stages/retry-policy)
   if ! PYTHONPATH="${REPO_ROOT}/scripts" uv run python -m agent.workflow.validate \
        "${REPO_ROOT}/config/workflows/default.json"; then
     echo "[FATAL] Workflow definition failed validation; aborting deployment." >&2
     exit 1
   fi
   ```
   This must still be before any `mkdir`/`cp`/`rsync` line.
3. Confirm `bash -n deploy/deploy.sh` still parses correctly.

### Method

Direct shell insertion, chained after the prerequisite existence check — no restructuring of the surrounding script.

### Details

- The `if ! <command>; then ... fi` form is used (rather than checking `$?` after the fact) for clarity and to avoid an intervening command resetting `$?` under `set -e`.
- This call intentionally validates the **source** path (`${REPO_ROOT}/config/workflows/default.json`), not the deployed path — validating before copy is strictly earlier/safer, and matches the pattern the requirement's own recommended command used.

## Validation plan

```bash
bash -n deploy/deploy.sh

# Positive test
bash deploy/deploy.sh   # expect success past both the existence check and validation call

# Negative test: corrupt a scratch copy and point a temporary invocation at it
cp config/workflows/default.json /tmp/default_backup.json
python3 -c "import json; d=json.load(open('config/workflows/default.json')); del d['retry_policy']; json.dump(d, open('config/workflows/default.json','w'))"
bash deploy/deploy.sh; echo "exit: $?"   # expect non-zero, [FATAL] message, before any mkdir/cp output
cp /tmp/default_backup.json config/workflows/default.json   # restore immediately

# Confirm no service side effects
ps aux | grep -E "agent|mcp|eventbus" | grep -v grep   # expect no new process from the validator call
```

Expected outcome: deployment proceeds normally with a valid definition; aborts with a `[FATAL]` message and non-zero exit before any `mkdir`/`cp` when the definition is invalid; no agent/MCP/LLM process is started as a side effect.
