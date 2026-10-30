## Goal
Add a fail-fast pre-flight check to `deploy/start_agent.sh` that verifies the compiled
agent binary `/opt/llm/bin/agent` exists and is executable before launch, replacing the
terse bash ENOENT with a clear, actionable rebuild/redeploy message.

## Priority
High

## Scope
- **In-Scope**:
  - A pre-flight block in `deploy/start_agent.sh` (after the existing pyproject/uv/config/db/workflow checks, before the binary launch at line 197) that verifies `/opt/llm/bin/agent` exists and is executable and exits non-zero with an actionable message when it does not.
  - Optional stale-binary warning relative to HEAD (REQ-002), reusing `tools/manage_binaries.py check` semantics, gated by a strictness flag.
  - Optional missing-dict warning for `/opt/llm/dict/system.dic` (REQ-003), warn-only.
  - A pytest under `tests/deploy/` asserting the missing-binary fail-fast path (REQ-004).
  - An operational note in the deployment doc (REQ-001).
- **Out-of-Scope**: rebuilding or deploying the actual binaries; changing how/whether the agent runs as a binary vs source; fixing the partial/stale staged build in `/opt/llm/dist/stage/`; altering the launch command itself.
- **Dependencies**: N/A: none.

## Background
Production runs the agent as a Nuitka `--onefile` binary launched by `deploy/start_agent.sh`. The committed script (HEAD) ends at line 197 with `UV_SYSTEM_CERTS=true /opt/llm/bin/agent`, with no existence or freshness check beforehand. On 2026-10-22 a Nuitka build was produced into `/opt/llm/dist/stage/` (build-info records `source_commit` 9e684e0), but it was never swapped into `/opt/llm/bin/`, and `/opt/llm/DEPLOYED_REV` was never written (deploy.sh aborts at the binary gate before it writes the revision record). Other services (the Event Bus, and the cicd/shell MCP servers currently running) run from source via `.venv`; only the agent requires the compiled binary.

## Problem
When `/opt/llm/bin/` is empty (never deployed, or cleared), starting the agent produces a terse bash ENOENT (`行 197: /opt/llm/bin/agent: このようなファイルやディレクトリはありません`). This is indistinguishable from any other bash ENOENT and gives the operator no guidance (rebuild the binaries? redeploy? restore a prior set from a worktree?). The agent is therefore completely unstartable, with no fallback to source execution even though the other services run from source.

## Reason for Change
The current failure mode is a silent single point of failure: an empty `bin/` makes the agent unstartable and the error unactionable. A pre-flight check turns this into an immediate, diagnosable fail-fast. Nuitka is available in this environment (`uv run --group build nuitka`), so once the check points to "rebuild + deploy", the path to recovery is clear.

## Implementation Intent
Add a pre-flight block in `deploy/start_agent.sh` (after the existing pyproject/uv/config/db/workflow checks, before the binary is executed at the launch line) that:
- Verifies `/opt/llm/bin/agent` exists and is executable; if not, prints a concise actionable message (rebuild via `deploy/build_binaries.sh`, restore a prior set via `deploy/build_binaries.sh --rollback`, then `deploy/deploy.sh`) and exits non-zero.
- Optionally warns when the deployed binary is stale relative to HEAD (reuse `tools/manage_binaries.py check` semantics) without hard-failing, unless a flag opts into strictness.
- Optionally warns when `/opt/llm/dict/system.dic` is missing, without hard-failing.
Keep the change shell-only, preserve all existing checks and the existing mdq-token / workflow fail-fast style, and do not alter how the binary is launched.

## Requirements
- `REQ-001`: Before launching, verify `/opt/llm/bin/agent` exists and is executable; if not, print a concise actionable message (rebuild via `deploy/build_binaries.sh`, restore a prior set via `deploy/build_binaries.sh --rollback`, then `deploy/deploy.sh`) and exit non-zero.
- `REQ-002`: When the deployed binary is stale relative to HEAD, warn (do not hard-fail) unless a strictness flag opts in; reuse `tools/manage_binaries.py check` semantics.
- `REQ-003`: When `/opt/llm/dict/system.dic` is missing, warn only (do not hard-fail), because it is a separate deployment artifact.
- `REQ-004`: Provide a test asserting the missing-binary fail-fast path (REQ-001), and optionally the stale-warn (REQ-002) and dict-warn (REQ-003) behaviors.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `deploy/start_agent.sh` | Modify | Add a pre-flight existence/executable check for `/opt/llm/bin/agent` before the launch line, with an actionable error and non-zero exit when absent; optional stale/dict warnings | REQ-001, REQ-002, REQ-003 | File exists, 197 lines; line 197 is `UV_SYSTEM_CERTS=true /opt/llm/bin/agent` with no existence check; existing fail-fast style at lines 120-137 (checked in Step 2) | `tests/deploy/test_start_agent_preflight.py` | Verified |
| `tests/deploy/test_start_agent_preflight.py` | Create | Assert the missing-binary pre-flight prints the actionable message and exits non-zero | REQ-001, REQ-004 | `tests/deploy/` already shells out to real deploy scripts (`test_load_env_gate.py`, `test_init_db_eventbus_schema.py`, `test_setup_services_eventbus.py`); pattern is source-a-driver-and-check-returncode (checked in Step 2) | `deploy/start_agent.sh` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Operational note: an empty `bin/` now fails fast with recovery guidance; `/opt/llm/DEPLOYED_REV` is only written after a successful binary-gated deploy | REQ-001 | File exists (25861 bytes) (checked in Step 2) | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `deploy/deploy.sh` | Defines `BINARY_NAMES` (11 binaries) and the binary freshness gate plus `DEPLOY_STRICT_BINARIES` flag referenced by REQ-002; copies `start_agent.sh` at deploy (line 203) | `deploy/start_agent.sh` |
| `deploy/build_binaries.sh` | `--rollback` restore and Nuitka rebuild commands referenced in the recovery message (REQ-001) | `deploy/start_agent.sh` |
| `tools/manage_binaries.py` | `check` subcommand semantics (ok/stale/unknown/mismatch/invalid, `--strict`) reused for REQ-002 | `deploy/start_agent.sh` |

## Acceptance Criteria
- `AC-001` (REQ-001): With `/opt/llm/bin/agent` missing, `deploy/start_agent.sh` exits non-zero with a message naming the missing binary and the recovery steps, instead of the raw bash ENOENT.
- `AC-002` (REQ-001): With the binary present and executable, startup proceeds exactly as before (no behavior change beyond the check).
- `AC-003` (REQ-002): With a stale binary and no strict flag, startup proceeds with a warning; with the strict flag set, startup fails.
- `AC-004` (REQ-003): With `/opt/llm/dict/system.dic` missing, the script warns but still launches (does not hard-fail).
- `AC-005` (REQ-004): The new test asserts the missing-binary path returns non-zero with the actionable message.

## Tests
- Add `tests/deploy/test_start_agent_preflight.py` mirroring the `tests/deploy/` convention (subprocess driver that sources the real script/library, captures returncode/stderr/stdout). Assert the missing-binary pre-flight prints the actionable message and exits non-zero (`AC-001`, REQ-001). Optionally assert the stale-warn (REQ-002) and dict-warn (REQ-003) behaviors.
- Run `uv run pytest tests/deploy/test_start_agent_preflight.py -v`.

## Documentation Impact
`REQ-001` drives an operational note in the deployment doc (locate via `docs/00_index.md` "Document References by Task"): an empty `/opt/llm/bin/` now fails fast with recovery guidance, and `/opt/llm/DEPLOYED_REV` is only written after a successful binary-gated deploy. Keep high-level; avoid implementation-detail duplication.

## Assumptions
- The pre-flight targets `/opt/llm/bin/agent` as the issue specifies; in dev the same path is used once deployed, and the check does not require Nuitka or network access.
- The strictness flag for REQ-002 follows the existing `DEPLOY_STRICT_BINARIES=1` convention in `deploy.sh`, expressed as a consistent agent-scoped env var.
- The recovery message references `deploy/build_binaries.sh` and `deploy/deploy.sh`, both present in the repo.
- The hard-fail trigger is the agent binary (the launch target); listing all 11 `BINARY_NAMES` is informational only, if included at all.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the pre-flight should hard-fail on a missing `/opt/llm/dict/system.dic`, or only warn (the dict is a separate deployment artifact) | Issue lists this as unresolved; no deploy-history evidence consulted | Issue Implementation Intent already leans warn-only; confirm with owner during plan-to-implementation-procedure | False |
| UNK-02 | Whether the missing `bin/` and the empty `/opt/llm/dict/` resulted from an incomplete deploy vs. deliberate cleanup | No deploy-history check performed | Check deploy history / `DEPLOYED_REV`; informational, out of scope per issue | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `deploy/start_agent.sh` | Modify | Medium | N/A | N/A | not applicable (existing cp line at L203 copies it each deploy) |
| `tests/deploy/test_start_agent_preflight.py` | Create | Low | N/A | N/A | not applicable (not a deploy artifact) |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (affects ≤ 3 files, no public/runtime interface change, no database schema change).

- **Parameterized pre-flight function.** Implement the check as a shell function
  `check_agent_binary("<path>")` that returns non-zero with the actionable message when
  the binary is missing or non-executable. Parameterizing the path lets a subprocess test
  drive the function against a controlled directory, mirroring the `tests/deploy/`
  source-a-driver pattern, without depending on the hardcoded `/opt/llm` upstream checks.
- **Testability vs. execution model.** `deploy/start_agent.sh` runs top-to-bottom and is
  not currently sourceable. Because the upstream deployed-files checks (lines 151-171) hardcode
  `/opt/llm` paths, a full end-to-end run in a test is impractical without touching production
  paths. The test therefore targets the pre-flight function in isolation. If the implementation
  makes the script sourceable (a minimal `[[ "${BASH_SOURCE[0]}" == "${0}" ]]` guard around the
  body), the guard MUST NOT change the direct-launch path behavior.
- **Strictness flag (REQ-002).** Reuse `manage_binaries.py check` semantics; gate stale/unknown
  on an env var consistent with `deploy.sh`'s `DEPLOY_STRICT_BINARIES=1`. The call is
  best-effort: it degrades to a warning and skips gracefully when invoked outside the repo or
  when rev/context is unavailable, and never hard-fails without the strict flag.
- **Scope of the hard fail.** The agent binary `/opt/llm/bin/agent` is the launch target and the
  hard-fail trigger (per the issue's AI Implementation Instruction, the most specific statement).
  Listing all 11 `BINARY_NAMES` is optional and informational only.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Presence/executable pre-flight (REQ-001)** — `deploy/start_agent.sh`
    - [ ] Add a `check_agent_binary("<path>")` function that exits non-zero with an actionable rebuild/redeploy/restore message when the binary is missing or non-executable, matching the existing `[FATAL]` fail-fast style.
    - [ ] Invoke `check_agent_binary "/opt/llm/bin/agent"` before the launch block (after the workflow-validation check, before line 197); propagate the non-zero exit.
2. **Phase 2: Optional stale + dict warnings (REQ-002, REQ-003)** — `deploy/start_agent.sh`
    - [ ] Add a best-effort stale-binary warning reusing `tools/manage_binaries.py check`, gated by a strictness env var; never hard-fail without the flag.
    - [ ] Add a warn-only notice when `/opt/llm/dict/system.dic` is missing.
3. **Phase 3: Tests, docs & verification (REQ-001, REQ-004)** — `tests/deploy/test_start_agent_preflight.py`, `deploy/start_agent.sh`, `docs/90_deployment/deployment_01_deployment.md`
    - [ ] Add a pytest asserting the missing-binary fail-fast path (`AC-005`), mirroring `tests/deploy/` conventions.
    - [ ] Add the high-level operational note to the deployment doc.
    - [ ] Run the new test and the deploy-script validation gates; hand off to `skills/deploy/SKILL.md` (deploy is the user's decision, gated on a prior commit+push).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `deploy/start_agent.sh` | Unit: drive `check_agent_binary` against a temp dir with/without the binary; integration: shellcheck syntax | `uv run pytest tests/deploy/test_start_agent_preflight.py -v`; `bash -n deploy/start_agent.sh` | Non-zero exit + actionable message when missing; clean syntax; no behavior change when present |
| `tests/deploy/test_start_agent_preflight.py` | Unit | `uv run pytest tests/deploy/test_start_agent_preflight.py -v` | Test passes |
| `docs/90_deployment/deployment_01_deployment.md` | Doc quality | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_content_policy.py` | No findings |

## Risks
- **Risk**: The hardcoded `/opt/llm` upstream checks make automated end-to-end testing of the pre-flight impractical without touching production paths. → **Mitigation**: implement the pre-flight as a parameterized, isolatable function and test it in isolation via a subprocess driver mirroring `tests/deploy/` conventions; keep any source-guard minimal and behavior-preserving.
- **Risk**: Making `deploy/start_agent.sh` sourceable to enable testing changes its execution model beyond "add a check". → **Mitigation**: prefer testing the function in isolation; if a source-guard is added, verify the direct-launch path is unchanged (`bash -n` + a present-binary smoke run).
- **Risk**: The stale-warn (REQ-002) calls into `manage_binaries.py`, which needs repo/rev context; running it at startup could add latency or fail outside the repo. → **Mitigation**: wrap the call in a best-effort guard that degrades to a warning and skips when context is unavailable, and never hard-fails without the strict flag.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Presence/executable pre-flight (REQ-001) | In Progress | — | — | `deploy/start_agent.sh` |
| 2 | Optional stale + dict warnings (REQ-002, REQ-003) | In Progress | — | — | `deploy/start_agent.sh` |
| 3 | Tests, docs & verification (REQ-001, REQ-004) | In Progress | — | — | `tests/deploy/test_start_agent_preflight.py`, `docs/90_deployment/deployment_01_deployment.md` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261030-125450_01_deploy_start_agent.sh.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261030-125450_02_tests_deploy_test_start_agent_preflight.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261030-125450_03_docs_90_deployment_deployment_01_deployment.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-233829_deploy001_missing-binary-precheck.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-114844
- **Related target files**: `deploy/start_agent.sh`, `tests/deploy/test_start_agent_preflight.py`, `docs/90_deployment/deployment_01_deployment.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Implementation Intent; Required Changes | `deploy/start_agent.sh` | Step 1 | AC-001, AC-002 | `tests/deploy/test_start_agent_preflight.py` (AC-005) | Confirmed by repository evidence |
| REQ-002 | Implementation Intent (optional stale warning) | `deploy/start_agent.sh` | Step 2 | AC-003 | Optional test assertion | Explicit in issue |
| REQ-003 | Implementation Intent (optional dict warning) | `deploy/start_agent.sh` | Step 2 | AC-004 | Optional test assertion | Explicit in issue |
| REQ-004 | Testing Expectations | `tests/deploy/test_start_agent_preflight.py` | Step 3 | AC-005 | `uv run pytest tests/deploy/test_start_agent_preflight.py -v` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-125450 -->