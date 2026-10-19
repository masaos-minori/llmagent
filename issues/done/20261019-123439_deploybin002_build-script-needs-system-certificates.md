# build_binaries.sh fails to resolve nuitka on hosts that need the system certificate store

## Priority
Medium

## Summary
Make `deploy/build_binaries.sh` use the system certificate store for `uv` by default (overridable), as the other deploy scripts and the project's `uv` commands already do, so the binary build no longer fails at the nuitka resolution step on a host whose certificates are not in the default bundle.

## Background
- Plan Gap recorded while implementing `plans/done/20261019-104249_plan.md` (deploybin001): the owner asked on 2026-10-19 to add this as a requirement. The original plan and its procedures are already completed and archived, so it is filed as a follow-up.
- The project runs `uv` with the system certificate store: `AGENTS.md` documents `uv sync --dev --system-certs`, and `deploy/deploy.sh`, `deploy/start_agent.sh`, `deploy/init_db.sh`, and `deploy/setup_services.sh` set `UV_SYSTEM_CERTS=true` inline for their `uv run` calls.
- `deploy/build_binaries.sh` sets `UV_NO_DEV` but not `UV_SYSTEM_CERTS`.

## Problem
- Observed on 2026-10-19 on the build host (Explicit evidence from the session): `BUILD_ONLY="agent" NUTKA_JOBS=2 bash deploy/build_binaries.sh` failed immediately with `nuitka not available`. The fallback `uv run --with nuitka[onefile]==4.2.2 nuitka` reported `Failed to fetch: https://pypi.org/simple/nuitka/ ... invalid peer certificate: UnknownIssuer`.
- The same command succeeded with `UV_SYSTEM_CERTS=true` (agent build 383 s; later a full 11-binary build of 2561 s), so the certificate store is the only difference.
- Nothing in the skill or the deployment document tells the operator to set it; the failure message points to nuitka, not to certificates.

## Reason for Change
- Operational reliability: the build host cannot build without a variable the operator must know to set, and the failure surfaces as a misleading nuitka error.
- Consistency: every other deploy script already requests the system certificate store.

## Implementation Intent
- Export `UV_SYSTEM_CERTS` in `build_binaries.sh` with a default of `true`, keeping any value the operator already set (the same pattern as `UV_NO_DEV`), before the first `uv` call.
- Say in the script's header comment and in the deploy skill's Phase 1b prerequisites why it is set and how to override it.
- Keep the change minimal: no other `uv` or Nuitka behavior changes.

## Target Files or Areas
- `deploy/build_binaries.sh`
- `skills/deploy/workflow.md` (Phase 1b prerequisites)
- `tests/tools/test_manage_binaries.py` (a static check that the script exports the variable with an overridable default)

## Required Changes
- Add `export UV_SYSTEM_CERTS="${UV_SYSTEM_CERTS:-true}"` next to the existing `UV_NO_DEV` export, before any `uv` invocation, with a comment.
- Add one sentence to the Phase 1b text in the deploy workflow about the default and the override.
- Add a test that fails if the script no longer exports `UV_SYSTEM_CERTS` before its first `uv` call.

## Constraints
- An explicit `UV_SYSTEM_CERTS` set by the operator must win (for example `false` on a host that does not use the system store).
- Do not change Nuitka flags, the entry table, or any other script.
- No production action: the change is to the repository script; the next real build uses it.

## Acceptance Criteria
- `bash -n deploy/build_binaries.sh` passes and the script exports `UV_SYSTEM_CERTS` with a `true` default before the first `uv` command.
- The new test passes and fails when the export is removed.
- The deploy workflow's Phase 1b mentions the default and the override.
- Documentation checkers for the edited skill file pass.

## Testing Expectations
- The new static test in `tests/tools/test_manage_binaries.py`.
- `bash -n deploy/build_binaries.sh`; `uv run python tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py`.
- A real build on the build host is optional and needs the operator.

## Documentation Impact
Yes, small: the deploy workflow (Phase 1b prerequisites). The deployment document needs no change unless it lists build prerequisites (to confirm).

## Out of Scope
- Certificate handling for any other tool or script.
- Fixing the host's certificate bundle itself.
- Changing how the other deploy scripts set `UV_SYSTEM_CERTS`.

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Context: the staged build flow it modifies was added by `plans/done/20261019-104249_plan.md`.

## Unresolved Questions
- Whether `docs/90_deployment/deployment_01_deployment.md` lists the build host prerequisites and should mention this (to confirm during planning).

## AI Implementation Instruction
- Keep the diff to the lines named above; do not touch other scripts or Nuitka settings.
- Preserve an operator-supplied `UV_SYSTEM_CERTS`.
- Do not run a build against `/opt/llm`; validate with `bash -n` and the test.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261019-104249_plan.md
- **Source implementation procedure**: implementations/done/20261019-105818_04_deploy_build_binaries.sh.md
- **Generated at**: 20261019-123439
- **Related target files**: `deploy/build_binaries.sh`, `skills/deploy/workflow.md`, `tests/tools/test_manage_binaries.py`
