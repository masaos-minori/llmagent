# start_agent.sh fails cryptically when /opt/llm/bin/agent is missing; add a fail-fast pre-flight check

## Priority
High

## Summary
The agent cannot start when the compiled binary `/opt/llm/bin/agent` is absent: `deploy/start_agent.sh` executes it directly and bash reports a terse ENOENT. Add an explicit pre-flight check that verifies the binary (and its Sudachi dict dependency) exists before launch and fails fast with a clear, actionable message.

## Background
- Production runs the agent as a Nuitka `--onefile` binary launched by `deploy/start_agent.sh`. The committed script (HEAD) ends at line 197 with `UV_SYSTEM_CERTS=true /opt/llm/bin/agent`, with no existence or freshness check beforehand.
- On 2026-10-22 a Nuitka build was produced into `/opt/llm/dist/stage/` (build-info records `source_commit` 9e684e0), but it was never swapped into `/opt/llm/bin/`, and `/opt/llm/DEPLOYED_REV` was never written (deploy.sh aborts at the binary gate before it writes the revision record).
- Other services (the Event Bus, and the cicd/shell MCP servers currently running) run from source via `.venv`; only the agent requires the compiled binary.

## Problem
When `/opt/llm/bin/` is empty (never deployed, or cleared), starting the agent produces:
```
deploy/start_agent.sh: 行 197: /opt/llm/bin/agent: このようなファイルやディレクトリはありません
```
This is indistinguishable from any other bash ENOENT and gives the operator no guidance (rebuild the binaries? redeploy? restore a prior set from a worktree?). The agent is therefore completely unstartable, with no fallback to source execution even though the other services run from source.

## Reason for Change
The current failure mode is a silent single point of failure: an empty `bin/` (which occurred in this environment) makes the agent unstartable and the error unactionable. A pre-flight check turns this into an immediate, diagnosable fail-fast. Nuitka is available in this environment (`uv run --group build nuitka`), so once the check points to "rebuild + deploy", the path to recovery is clear.

## Implementation Intent
Add a pre-flight block in `deploy/start_agent.sh` (after the existing pyproject/uv/config/db/workflow checks, before the binary is executed at the launch line) that:
- Verifies `/opt/llm/bin/agent` exists and is executable; if not, prints a concise actionable message (rebuild via `deploy/build_binaries.sh`, restore a prior set via `deploy/build_binaries.sh --rollback`, then `deploy/deploy.sh`) and exits non-zero.
- Optionally warns when the deployed binary is stale relative to HEAD (reuse `tools/manage_binaries.py check` semantics) without hard-failing, unless a flag opts into strictness.
Keep the change shell-only, preserve all existing checks and the existing mdq-token / workflow fail-fast style, and do not alter how the binary is launched.

## Target Files or Areas
- `deploy/start_agent.sh`
- Reference: `deploy/build_binaries.sh`, `deploy/deploy.sh`, `tools/manage_binaries.py`

## Required Changes
- Add an existence/executable check for `/opt/llm/bin/agent` before launch, with a clear actionable error and non-zero exit when missing.
- Print which of the 11 expected binaries (`BINARY_NAMES` in `deploy/deploy.sh`) are missing, mirroring the existing token / workflow fail-fast style.
- Do not change the launch command itself.

## Constraints
- Must remain a pure bash change to `deploy/start_agent.sh`; no Python changes required for the check itself.
- Must not break the production binary-launch contract (the agent still launches as `/opt/llm/bin/agent`).
- The check must not require Nuitka or network access.
- Preserve the existing `.env` load, config/db/workflow validation order.

## Acceptance Criteria
- With `/opt/llm/bin/agent` missing, `deploy/start_agent.sh` exits non-zero with a message naming the missing binary and the recovery steps, instead of the raw bash ENOENT.
- With the binary present, startup proceeds exactly as before (no behavior change).
- The check runs before any attempt to execute the binary.

## Testing Expectations
- Manual: run `deploy/start_agent.sh` with `/opt/llm/bin/` emptied and confirm the new actionable error and non-zero exit; restore the binary and confirm normal startup.
- If the repo has shell tests for deploy scripts, add one asserting the missing-binary path.

## Documentation Impact
- `docs/90_deployment/deployment_01_deployment.md` operational notes: note that an empty `bin/` now fails fast with recovery guidance, and that `/opt/llm/DEPLOYED_REV` is only written after a successful binary-gated deploy. Keep high-level; avoid implementation-detail duplication.

## Out of Scope
- Rebuilding or deploying the actual binaries (an operational action, not code).
- Changing how/whether the agent runs as a binary vs source.
- Fixing the partial/stale staged build in `/opt/llm/dist/stage/`.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether the missing `bin/` and the empty `/opt/llm/dict/` (also empty) resulted from an incomplete deploy vs. deliberate cleanup — needs confirmation against deploy history.
- Whether the pre-flight should also hard-fail on a missing `/opt/llm/dict/system.dic`, or only warn (the dict is a separate deployment artifact).

## AI Implementation Instruction
Edit only `deploy/start_agent.sh`. Add a pre-flight check before the launch line that verifies `/opt/llm/bin/agent` exists and is executable, printing an actionable rebuild/redeploy message and exiting non-zero when absent. Match the script's existing bash fail-fast style. Do not touch launch logic, other scripts, or Python. Keep it dependency-free.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-233829
- **Related target files**: deploy/start_agent.sh
