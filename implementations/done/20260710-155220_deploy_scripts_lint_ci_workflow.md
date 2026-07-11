# Implementation: `deploy/*.sh` CI lint workflow (bash -n + shellcheck)

## Goal

Add a new GitHub Actions workflow that runs `bash -n` and `shellcheck` against `deploy/*.sh` on every push/PR touching those scripts, so future shell syntax/quoting regressions are caught automatically. No defects were found in the current scripts (see plan Assumptions) — this is purely a regression safety net.

## Scope

**In:**
- New file `.github/workflows/deploy-scripts-lint.yml`

**Out:**
- No changes to `deploy/deploy.sh`, `deploy/setup_services.sh`, `deploy/init_db.sh`, `deploy/build_sqlite_vec.sh` — no defects to fix (confirmed by direct investigation in the plan)

## Assumptions

1. `bash -n` currently exits 0 for all `deploy/*.sh` scripts (confirmed at planning time).
2. `shellcheck` is not installed locally; `ludeeus/action-shellcheck@v2` runs it in the CI runner instead of relying on local/manual installation.
3. Modeled on the existing `.github/workflows/backward-compat-check.yml` structure (trigger shape, `concurrency` block).

## Implementation

### Target file

`.github/workflows/deploy-scripts-lint.yml` (new file)

### Procedure

1. Create the file with the following content:
   ```yaml
   name: Deploy Scripts Lint

   on:
     push:
       paths:
         - "deploy/*.sh"
     pull_request:
       paths:
         - "deploy/*.sh"

   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true

   jobs:
     lint:
       name: Shell Syntax and Shellcheck
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4

         - name: bash -n syntax check
           run: |
             set -euo pipefail
             for f in deploy/*.sh; do
               echo "Checking: $f"
               bash -n "$f"
             done

         - name: shellcheck
           uses: ludeeus/action-shellcheck@v2
           with:
             scandir: "./deploy"
   ```
2. Validate YAML well-formedness.

### Method

Direct new-file creation — no changes to any existing workflow or shell script.

### Details

- `deploy/*.sh` glob incidentally also lints `init_db.sh` and `build_sqlite_vec.sh`, a strict improvement with no added risk (only `deploy.sh` and `setup_services.sh` were named in the requirement's scope).
- `ludeeus/action-shellcheck` is used instead of a manual `apt-get install shellcheck` step to avoid depending on the runner image's package availability/version.
- If `shellcheck` (once actually run in CI) surfaces findings on intentional patterns (e.g. the deliberately-unquoted `cp -n "${REPO_ROOT}/plugins/"*.py` glob-expansion at `deploy.sh:54`), those are triaged as accepted exceptions (e.g. inline `# shellcheck disable=SCxxxx` with a justification comment) rather than "fixed" into broken quoting — this triage happens at implementation time if/when it occurs, not preemptively in this design.

## Validation plan

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-scripts-lint.yml'))"
bash -n deploy/deploy.sh deploy/setup_services.sh deploy/init_db.sh deploy/build_sqlite_vec.sh
```

Expected outcome: YAML parses without error; all four scripts pass `bash -n` locally (already true today). CI confirmation (the new `Deploy Scripts Lint` check appearing and passing on a PR touching `deploy/*.sh`) happens naturally once this workflow file is committed and any of the sibling plans' `deploy/*.sh` edits are pushed — no separate action needed here.
