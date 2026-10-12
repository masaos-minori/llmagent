## Goal

Create `deploy/build_binaries.sh`, a build script that produces all 11 Nuitka `--onefile` binaries (the agent plus the 10 MCP servers) into `/opt/llm/bin/`, bundling the `sudachipy` package resources and leaving `config/`, the Sudachi dictionary, and `sqlite-vec` external. Implements `REQ-006` / AC-08.

## Scope

Creates one new script `deploy/build_binaries.sh` (new). It runs on the build host only and is not deployed to `/opt/llm`. It is the single artifact for steps 7, 8, and 9 of the plan.

## Assumptions

- The build host has a Python with development headers (`Python.h`) and `patchelf`.
- Low-memory hosts need `--onefile-no-compression`; the output directory must not be a small tmpfs (Plan Assumptions / UNK-06).
- The dictionary file comes from the same `sudachidict-core` version as the build environment's `sudachipy` (a mismatched dictionary fails with `Invalid header version`).
- The 11 real binaries are not yet known to build under Nuitka (UNK-01); the script is written defensively and the Phase 2 gate (step 9) blocks every production-affecting change until the PoC passes.

## Design decisions

- Build each of the 11 entry points with the same Nuitka invocation, parameterized by module path and output binary name, so the 10 MCP servers and the agent share one code path.
- Add `--include-package-data=sudachipy` (and `--include-package=sudachipy` if required) so the Sudachi package resources bundle into the onefile binary; add `--onefile-no-compression` when memory is constrained.
- Output to `/opt/llm/bin/<binary>` for the agent and each MCP server; do not embed `config/`, the dictionary, or `vec0.so` — those stay external under `/opt/llm/`.
- Fail fast: exit non-zero on the first failed build so a broken server is visible immediately rather than silently skipped.

## Alternatives considered

- Building only the agent first: rejected — the plan gates on all 11 building and running; building incrementally (shell, then rag_pipeline, then the rest) is an ordering choice inside the script, not a reason to split it.
- Hard-coding the 11 invocations inline: rejected — a data-driven loop over a module/name table keeps the list in one place and reduces copy errors.

## Implementation

### Target file

`deploy/build_binaries.sh` (new)

### Procedure

Write a bash script that builds all 11 binaries into `/opt/llm/bin/` with shared Nuitka flags and a per-binary loop.

### Method

1. Create `deploy/build_binaries.sh` with `#!/bin/bash`, `set -euo pipefail`, and a configurable `BIN_DIR` (default `/opt/llm/bin`) and `OUTPUT_DIR` (default a non-tmpfs location such as `/opt/llm/dist` for the intermediate onefile outputs).
2. Define a module/name table listing the 11 entry points: the agent (`agent.repl`) and the 10 MCP servers (`mcp_servers.shell.shell_server`, `mcp_servers.git.git_server`, `mcp_servers.web_search.web_search_server`, `mcp_servers.file.delete_server`, `mcp_servers.file.write_server`, `mcp_servers.file.read_server`, `mcp_servers.github.github_server`, `mcp_servers.cicd.cicd_server`, `mcp_servers.rag_pipeline.rag_pipeline_service`, `mcp_servers.mdq.mdq_server`).
3. For each entry point, invoke Nuitka with `--onefile`, `--output-dir "${OUTPUT_DIR}"`, `--include-package-data=sudachipy` (plus `--include-package=sudachipy` if the build requires it), `--include-module` for any lazy imports discovered during the PoC (e.g. `rag.pipeline`), and `--no-strip`; write the resulting binary to `${BIN_DIR}/<binary>`.
4. After each successful build, record elapsed time and the binary size (via `du -h`); accumulate totals.
5. At the end, print the total build time and total size across all 11 binaries for the Plan's Execution Status notes.

### Details

- Keep the Sudachi dictionary and `vec0.so` out of the binary; the agent and RAG server resolve them at runtime via `LLMAGENT_SUDACHI_DICT` and the absolute `sqlite_vec_so` path (unchanged `db/helper.py`).
- Make the interpreter/flags overridable via environment variables (e.g. `NUITKA_EXTRA_FLAGS`) so the PoC can inject flags without editing the script.

## Compatibility considerations

- The script is additive and runs only on the build host; it does not touch `scripts/`, `config/`, or `pyproject.toml`, so the `uv run` path remains intact.

## Security considerations

- N/A: build-time script; it does not execute untrusted input. Ensure the script does not copy world-writable artifacts into `/opt/llm/bin/` (the deploy/start rows enforce the non-group/world-writable directory rule for the CommandValidator).

## Rollback considerations

- N/A: revert the commit; the file is new.

## Validation plan

- Run `deploy/build_binaries.sh` and confirm all 11 builds succeed (step 8).
- Run the AC-08 smoke checks: start the agent binary, query each MCP server's `/health`, run a RAG search using the external dictionary and `vec0.so` (step 9).
- Confirm recorded startup time and total size are captured in the Plan's Execution Status notes.

## Completion criteria

- `deploy/build_binaries.sh` builds all 11 binaries into `/opt/llm/bin/`; the AC-08 smoke checks pass; startup time and total size are recorded.

## Out of scope

- The `cmd` rewrite in `config/agent.toml` (step 10) and the deploy/start rows (step 11) — gated on this script's PoC passing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write `deploy/build_binaries.sh` (step 7) | Pending | — | — | |
| 2 | Build shell, then rag_pipeline, then the rest and the agent (step 8) | Pending | — | — | Record UNK-01 findings |
| 3 | Gate: AC-08 smoke checks (step 9) | Pending | — | — | Stop and amend Plan if it fails |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: deploy/build_binaries.sh
