# Deploy cannot tell whether the compiled binaries match the source, and has no rebuild step or rollback

## Priority
High

## Summary
Add a binary rebuild step to the deploy procedure, make binary freshness detectable (build info recorded at build time and checked at deploy time, plus a record of the deployed revision), and make binary replacement safe and reversible (build to a staging directory, smoke test, swap atomically, keep the previous set). Fix the deploy skill and deployment documentation so they describe the binary-based production runtime.

## Background
- Review of the deploy scripts and the deploy skill on 2026-10-19, prompted by the redeploy of the session sqlite-vec fix (see `plans/done/20261019-094625_plan.md`). The owner chose all three improvement groups: A (documentation and skill), B (freshness detection and deployed-revision record), C (staged build, smoke test, swap, rollback).
- Production runs the agent and the 10 MCP servers as Nuitka `--onefile` binaries under `/opt/llm/bin/`; the agent is launched by `deploy/start_agent.sh` as a compiled binary, and each subprocess MCP server's `cmd` in `config/agent.toml` points to a binary.
- `deploy/deploy.sh` synchronizes `scripts/`, `config/`, `tests/`, `docs/`, then places the 11 binaries from `BUILD_OUTPUT_DIR`, which defaults to `/opt/llm/bin`. By default the source and destination are the same file, so the step only checks that each binary exists.
- Other components run from the deployed `scripts/` source, not from binaries: the Event Bus (`setup_services.sh` starts it with `python -m eventbus.app`), the ingestion pipeline, the workflow validation in `start_agent.sh`, and `init_db.sh`.

## Problem
- Following the deploy skill exactly leaves production running old code while every step reports success. A change under `scripts/agent/` or `scripts/db/` reaches the agent only after the `agent` binary is rebuilt, but no step in the skill or in `deploy.sh` rebuilds it.
- Binaries carry no record of the commit they were built from, so staleness cannot be detected, and nothing records which commit is deployed.
- `build_binaries.sh` writes each finished binary directly into `/opt/llm/bin/` (`mv` over the existing file) with no backup and no smoke test; a failure part-way through a multi-binary build leaves a mixture of new and old binaries, and there is no fast rollback.
- The skill's rollback note ("check out the previous commit and re-run from Phase 2") does not restore binaries, and its note that reverting `agent.toml` `cmd` entries to `uv run` restores the launch path applies only to MCP servers, because `start_agent.sh` launches `/opt/llm/bin/agent` directly.
- The skill's restart criteria (Step 3a) are written in terms of source files, with no mapping from changed source to affected binary or to the Event Bus process, and the skill describes `setup_services.sh` as starting services while it only checks the remote LLM health and starts the Event Bus (a re-run can start a second Event Bus).
- Confirmed (Explicit in code): `deploy/deploy.sh` binary block, `deploy/build_binaries.sh` `build_one` (`mv "${produced}" "${BIN_DIR}/${final_name}"`), `deploy/start_agent.sh` last line, `deploy/setup_services.sh` Event Bus start, `skills/deploy/workflow.md` Phases 1 to 4 and `skills/deploy/SKILL.md` Scope notes. Not observed: the live state of `/opt/llm` (a production read was not permitted in the session that produced this issue).

## Reason for Change
- Production reliability: a successful deploy that does not deliver the change is a silent failure, and the first instance (the Memory vector fix) was caught only by reading the scripts.
- Recovery: with no retained previous binary set, rollback needs a rebuild of up to 11 binaries.
- Documentation and code mismatch: the skill and the deployment document describe a source-based flow for a binary-based runtime.

## Implementation Intent
- Treat the three groups as one change because they share `build_binaries.sh`, `deploy.sh`, and the skill, and must be tested together.
- A. Documentation: add an explicit "rebuild affected binaries" phase to the skill with a mapping from changed source to the binaries and processes it affects; correct the rollback and restart notes; state in the deployment document which components run from binaries and which from deployed source.
- B. Freshness: record build info (source commit, dirty flag, build time) next to each binary at build time; make deploy compare it to the commit being deployed and warn, or fail in a strict mode; write a deployed-revision record at deploy time.
- C. Safe replacement: build into a staging directory, run a smoke test per binary, swap into place only after all requested binaries pass, and keep the previous set for a fast rollback command.
- Keep existing environment variables and defaults working (`BUILD_ONLY`, `BUILD_OUTPUT_DIR`, `BIN_DIR`, `OUTPUT_DIR`), and keep the current behavior as the default unless a new strict option is set.

## Target Files or Areas
- `deploy/build_binaries.sh`
- `deploy/deploy.sh`
- `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`
- `docs/90_deployment/deployment_01_deployment.md`
- `rules/env.md` (only if it restates the deploy flow; to confirm)
- A small checker or test location for the build-info comparison and the shell scripts: Unknown (no existing tests reference `deploy.sh` or `build_binaries.sh`)

## Required Changes
- Skill: add a rebuild phase and the source-to-binary mapping (agent: `scripts/agent/`, `scripts/db/`, `scripts/shared/` and other packages the agent entry imports; each `mcp_<server>`: its `scripts/mcp_servers/<server>/` package plus shared imports; Event Bus and ingestion: no binary, restart the process); correct Scope notes (rollback, `uv run` claim), the `setup_services.sh` description, and the Event Bus restart and duplicate-start caveat.
- `build_binaries.sh`: write a build-info file for each binary; build into a staging directory; smoke test each binary (the exact check is Unknown, see Unresolved Questions); swap into `BIN_DIR` only when every requested binary passed; keep the previous binaries (for example in a `.prev` directory); provide a rollback command or option.
- `deploy.sh`: compare each binary's build info with the revision being deployed (warn by default, fail with a strict option); record the deployed revision (commit, time) in a file under `/opt/llm/`.
- Documentation: update the deployment document's compiled-artifacts section with the build, freshness check, record, and rollback behavior, and the component-to-runtime table.
- Make `deploy/deploy.sh` consistent with the other scripts' executable bit or document that it is run with `bash` (low priority, may be dropped).
- Add tests or a dry-run mode that exercise the build-info comparison and the swap and rollback logic without running Nuitka.

## Constraints
- Do not change the Nuitka build flags, the entry table, or binary names (the `build_binaries.sh` entries and `deploy.sh` `BINARY_NAMES` must stay in sync; the skill's Phase 1 diff keeps verifying that).
- `/opt/llm/bin/` must stay non-group/world-writable; the staging and `.prev` directories must not weaken that (the CommandValidator rejects binaries under a writable directory).
- Production changes are outside this issue's implementation scope; it changes scripts and documents only, and a deploy remains a separate, approved action.
- Shell scripts are not covered by the Python toolchain; validation uses `bash -n`, shellcheck if installed, and the new tests.

## Acceptance Criteria
- The deploy skill contains a rebuild phase with the source-to-binary mapping, and no step tells the operator that `deploy.sh` alone delivers a code change to the agent or MCP servers.
- After a build, every built binary has a build-info file recording the source commit and dirty flag.
- `deploy.sh` reports a binary whose build commit differs from the deployed commit; in strict mode it exits non-zero.
- `deploy.sh` writes a deployed-revision record readable without running any component.
- A failed or partial multi-binary build leaves `/opt/llm/bin/` unchanged; a successful build leaves the previous set available and a documented command restores it.
- The skill's rollback and restart notes and the deployment document agree with the scripts, and the documentation checkers pass.

## Testing Expectations
- Unit or script-level tests for build-info writing and comparison, swap on success, no change on failure, and rollback, using fake binaries and a temporary directory.
- `bash -n deploy/*.sh` and shellcheck (if installed) on the changed scripts.
- Documentation checkers from `routing.md` for the edited `docs/` and `skills/` files, including `tools/check_skills_references.py` and `tools/check_docs_consistency.py --domain deployment`.
- Manual verification on the build host of one real `BUILD_ONLY="agent"` build into the staging directory, with the swap not applied to production, is optional and requires separate approval.

## Documentation Impact
Yes. Update `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, and the deployment document (intent, boundaries, failure behavior, operational notes, rollback). The deployment document is written in English. Any item that cannot be confirmed without a production read is recorded as a Needs Confirmation item only if it affects the documented behavior.

## Out of Scope
- Rebuilding or redeploying anything in production, or reading production state.
- Changing Nuitka flags, adding or removing binaries, or changing the MCP server launch design.
- Replacing the binary distribution with another packaging method, or moving the Event Bus into a binary.
- Container or orchestration tooling.
- The `tests/` copy in `deploy.sh` (whether production needs it is a separate question).

## Dependencies
- N/A: none. No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.
- Context: the session sqlite-vec change (`plans/done/20261019-094625_plan.md`) is not yet in the production `agent` binary and is the first change to benefit from this work.

## Unresolved Questions
- Smoke test for a binary: does the agent or any MCP binary support a non-interactive check (for example `--version` or `--help`) that exits 0 without starting a server or REPL? Unknown; needs checking against the launcher in `build_binaries.sh` and `agent.repl`.
- Where to store build info and the deployed-revision record, and in what format (assumption: a small text or JSON file next to each binary, and one file under `/opt/llm/`).
- Whether the source-to-binary mapping should be hand-written in the skill or generated from imports (assumption: hand-written first, with a follow-up to generate it).
- Whether a retained previous binary set (about 270 MB) is acceptable on the production disk (unmeasured).
- Whether `/opt/llm/tests` is used in production (Needs confirmation; not part of this issue's scope).

## AI Implementation Instruction
- Keep the diff minimal and limited to the target files; do not change Nuitka flags or the entry table.
- Preserve existing defaults and environment variables; new behavior (strict freshness check, staged swap) must be opt-in or backward compatible unless the owner approves a change of default.
- Do not run `build_binaries.sh` against `/opt/llm`, run `deploy.sh`, or read `/opt/llm`; test with fake binaries in a temporary directory.
- Write documentation in English and follow the documentation checkers; keep Japanese only in chat.
- Stop and report if the smoke-test question cannot be answered from the repository.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-103807
- **Related target files**: `deploy/build_binaries.sh`, `deploy/deploy.sh`, `skills/deploy/SKILL.md`, `skills/deploy/workflow.md`, `docs/90_deployment/deployment_01_deployment.md`
