# Implementation: `deploy.sh` metadata/checksum printing and mismatch abort

## Goal

Print workflow definition metadata (name, version, stage IDs) and SHA256 checksums of both the source and deployed `default.json` during `deploy/deploy.sh`, and abort deployment if the source and deployed checksums differ.

## Scope

**In:**
- `deploy/deploy.sh`: two new blocks — a pre-copy metadata/source-checksum block, and a post-copy deployed-checksum + comparison block

**Out:**
- No changes to `scripts/agent/workflow/validate.py` beyond what `implementations/20260710-155320_validate_py_print_metadata_flag.md` already adds
- No `jq` dependency — checksum computed via `sha256sum`, metadata via the Python CLI's `--print-metadata` flag

## Assumptions

1. Depends on `implementations/done/20260710-154614_deploy_sh_workflow_existence_checks.md`, `implementations/done/20260710-154712_deploy_sh_workflow_validation_wiring.md`, and `implementations/20260710-155320_validate_py_print_metadata_flag.md` all being implemented first — this plan's blocks are inserted relative to the checks/copy those add.
2. `sha256sum` is available in the deploy environment (confirmed).
3. `deploy.sh` runs as a single non-subshelled script body, so a shell variable (`SOURCE_SHA256`) set in the pre-copy block remains in scope at the post-copy block without a temp file or `export`.

## Implementation

### Target file

`deploy/deploy.sh`

### Procedure

1. Immediately after the existing pre-copy validation call (from `implementations/done/20260710-154712_deploy_sh_workflow_validation_wiring.md`), before any `mkdir`/`cp`, insert:
   ```bash
   echo "Workflow definition:"
   echo "Source   : config/workflows/default.json"
   echo "Deployed : /opt/llm/config/workflows/default.json"
   PYTHONPATH="${REPO_ROOT}/scripts" uv run python -m agent.workflow.validate \
     --print-metadata "${REPO_ROOT}/config/workflows/default.json"
   SOURCE_SHA256=$(sha256sum "${REPO_ROOT}/config/workflows/default.json" | awk '{print $1}')
   echo "SHA256 (source)   : ${SOURCE_SHA256}"
   ```
2. Immediately after the existing workflow-files copy command (`cp -r "${REPO_ROOT}/config/workflows/." "${DEPLOY_CONFIG}/workflows/"`), insert:
   ```bash
   DEPLOYED_SHA256=$(sha256sum "${DEPLOY_CONFIG}/workflows/default.json" | awk '{print $1}')
   echo "SHA256 (deployed) : ${DEPLOYED_SHA256}"
   if [ "${SOURCE_SHA256}" != "${DEPLOYED_SHA256}" ]; then
     echo "[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted." >&2
     exit 1
   fi
   ```
3. Confirm `bash -n deploy/deploy.sh` still parses correctly.

### Method

Two direct shell insertions at fixed points relative to already-existing (or sibling-plan-added) checks — no restructuring of the surrounding script.

### Details

- The pre-copy block calls the validator a second time with `--print-metadata` (in addition to the plain validation call already added by the wiring plan); this is an accepted, deliberate double-invocation of a fast, side-effect-free CLI so the plain validation-abort path and the metadata-printing path stay independently readable — not merged into one call with conditional output logic.
- `SOURCE_SHA256`/`DEPLOYED_SHA256` are the two lines' sole purpose: enabling the equality check. No other consumer needs these variables.

## Validation plan

```bash
bash -n deploy/deploy.sh

# Positive test
bash deploy/deploy.sh
# expect: Source/Deployed paths, Name, Version, Stages, SHA256 (source), SHA256 (deployed) all printed;
# both checksums match; script completes normally

# Negative test: simulate post-copy corruption (test harness only)
# temporarily insert `cp /some/other/file.json "${DEPLOY_CONFIG}/workflows/default.json"` right after
# the real copy step, run once, then remove the temporary line
bash deploy/deploy.sh; echo "exit: $?"
# expect: non-zero exit, "[FATAL] Deployed workflow definition checksum does not match source" message
```

Expected outcome: every `deploy.sh` run prints a full metadata/checksum audit trail; checksums match in the normal case; any post-copy corruption (however unlikely from a plain local `cp -r`) is caught and aborts the deployment with a clear message.
