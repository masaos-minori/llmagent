# Implementation: `deploy.sh` mandatory workflow definition existence checks

## Goal

Add a pre-copy existence check for `config/workflows/default.json` (aborting before any side effect if missing) and a post-copy existence check for the deployed copy, to `deploy/deploy.sh`.

## Scope

**In:**
- `deploy/deploy.sh`: two new `[[ ! -f ... ]]` guards — one immediately after `REPO_ROOT` is resolved (before any `mkdir`/`cp`), one immediately after the existing workflow-files `cp -r` block

**Out:**
- No validation of `default.json`'s contents (handled by `implementations/done/20260710-154*_deploy_sh_workflow_validation_cli_call.md`-equivalent from the sibling plan, not this one)
- No changes to `init_db.sh` or `setup_services.sh`

## Assumptions

1. `config/workflows/default.json` exists in this repo today; the pre-check is forward-looking protection, not a fix for a currently-broken state.
2. `deploy.sh` already has `set -euo pipefail` at the top — the new checks add explicit, actionable failure messages rather than relying on an incidental downstream `cp` failure.
3. The post-copy check must test the specific `default.json` path, not just the copy command's exit status, since `cp -r "${REPO_ROOT}/config/workflows/." "${DEPLOY_CONFIG}/workflows/"` could succeed even if `default.json` were absent from the source directory.

## Implementation

### Target file

`deploy/deploy.sh`

### Procedure

1. Locate the line `REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"` (currently line 12).
2. Immediately after it, insert:
   ```bash
   # Workflow: mandatory-artifact existence check (source). Scoped to default.json only,
   # not the config/workflows/ directory as a whole.
   if [[ ! -f "${REPO_ROOT}/config/workflows/default.json" ]]; then
     echo "[FATAL] Missing required workflow definition: config/workflows/default.json" >&2
     echo "This agent requires a valid workflow definition and does not support workflow-disabled mode." >&2
     exit 1
   fi
   ```
   This must come before the `echo "=== deploy.sh: デプロイ開始 ==="` banner and before any `mkdir`/`cp`/`rsync` line.
3. Locate the existing workflow-files copy line: `cp -r "${REPO_ROOT}/config/workflows/." "${DEPLOY_CONFIG}/workflows/"`.
4. Immediately after it, insert:
   ```bash
   # Workflow: mandatory-artifact existence check (deployed copy). Scoped to default.json only.
   if [[ ! -f "${DEPLOY_CONFIG}/workflows/default.json" ]]; then
     echo "[FATAL] Deployed workflow definition missing after copy: ${DEPLOY_CONFIG}/workflows/default.json" >&2
     exit 1
   fi
   ```

### Method

Direct insertion of two `bash` conditional guards at precise, pre-identified line anchors — no refactor of surrounding script structure.

### Details

- `[[ ! -f ... ]]` (not `[ ! -f ... ]`) is used for consistency with bash's preferred conditional syntax; `deploy.sh` is a `#!/bin/bash` script (not POSIX `sh`), so `[[ ]]` is safe and idiomatic here.
- Both messages go to stderr (`>&2`) to distinguish fatal errors from the script's normal stdout progress `echo` lines, and both `exit 1` immediately — no cleanup is needed since nothing has been written yet at the pre-copy check's point, and the post-copy check only detects an already-failed state.

## Validation plan

```bash
bash -n deploy/deploy.sh   # syntax check
shellcheck deploy/deploy.sh   # if available in this environment

# Negative test — simulate missing source
mv config/workflows/default.json /tmp/default.json.bak
bash deploy/deploy.sh; echo "exit code: $?"   # expect non-zero, [FATAL] message, before any mkdir/cp
mv /tmp/default.json.bak config/workflows/default.json   # restore

# Positive test
bash deploy/deploy.sh   # expect success past both new checks
```

Expected outcome: the pre-copy check fires immediately (before any `mkdir`/`cp` output) when `default.json` is absent; both checks pass silently when it is present; `bash -n` and `shellcheck` report no new issues.
