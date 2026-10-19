## Goal
Make the build stage binaries, record build info, swap the whole requested set into place only after every binary passes, keep the previous set, and offer a rollback option (`REQ-004`).

## Scope
- `build_one` and the main loop of this script, plus a rollback option at the top; Nuitka flags, `ENTRIES`, launchers, and the candidate-name search stay as they are.

## Assumptions
- `tools/manage_binaries.py` exists (sibling procedure) and is run with `python3` from the repository checkout.
- `BUILD_ONLY`, `BIN_DIR`, and `OUTPUT_DIR` keep their meaning; the end state of a successful build is unchanged (binaries in `BIN_DIR`).

## Design decisions
- Build into `STAGE_DIR` (new) under `OUTPUT_DIR`, then call `swap` once after the loop, so a failure part-way leaves `BIN_DIR` unchanged.
- Handle `--rollback` before the Nuitka pre-checks so it works without a toolchain.

## Alternatives considered
Swapping each binary immediately was rejected: a failure part-way would leave a mixed set.

## Implementation
### Target file
`deploy/build_binaries.sh`

### Procedure
1. Define `STAGE_DIR` (new) as `${OUTPUT_DIR}/stage`, and clear it at the start of a build.
2. At the top, after `BIN_DIR`, `OUTPUT_DIR`, and `REPO_ROOT` are known, handle `--rollback` by running the tool's `rollback` for `BIN_DIR` and exiting.
3. In `build_one`, replace the final `mv` into `BIN_DIR` with a move into `STAGE_DIR` (new) followed by `write-info`; record the built names in an array.
4. After the loop, run `swap --stage-dir "${STAGE_DIR}" --bin-dir "${BIN_DIR}" --names <built names>`; exit non-zero if it fails.
5. Adjust the size summary to read the swapped binaries from `BIN_DIR` after the swap.

### Method
- Edit the existing `mv "${produced}" "${BIN_DIR}/${final_name}"` and the `chmod` and size lines after it; keep the `cleanup_launchers` trap and add stage cleanup only for failed runs.
- The tool is called as `python3 "${REPO_ROOT}/tools/manage_binaries.py" ...`; `write-info` gets `--binary`, `--module`, and `--repo "${REPO_ROOT}"`.

### Details
- The previous set is saved by the tool to `${BIN_DIR}.prev`; document this in the script header comment.
- Do not change `NUTKA_*` variables, `BASE_NUTKA_ARGS`, or `LAZY_IMPORTS`.
- Plan Gap (not in scope here): the real build on 2026-10-19 needed `UV_SYSTEM_CERTS=true` for `uv` to fetch nuitka; this procedure does not change it.

## Compatibility considerations
Behavior on success is unchanged; on failure `BIN_DIR` is now left untouched. A new `${BIN_DIR}.prev` directory appears after the first swap. `BUILD_ONLY`, `BIN_DIR`, and `OUTPUT_DIR` keep working.

## Security considerations
`BIN_DIR` must stay non-group/world-writable; the tool refuses otherwise and the previous directory is created with the same mode.

## Rollback considerations
N/A: revert the commit; a real swap is undone with the new `--rollback` option.

## Validation plan
- `bash -n deploy/build_binaries.sh`
- `uv run pytest tests/tools/test_manage_binaries.py -q` (shell parse and rollback tests)
- A real `BUILD_ONLY="agent"` build into a temporary `OUTPUT_DIR` and `BIN_DIR` on the build host is optional and needs the operator's approval

## Completion criteria
- The script parses, `--rollback` restores a prepared previous set without Nuitka, and the build path writes build info and swaps once after the loop.

## Out of scope
- Nuitka flags and entry table
- Reading or writing `/opt/llm` during development
- Certificate handling for `uv` (Plan Gap)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `STAGE_DIR` (new), the rollback option, and the staged move with `write-info` | Completed | 20261019-112524 | 20261019-112524 |  |
| 2 | Add the post-loop `swap` and update the summary | Completed | 20261019-112524 | 20261019-112524 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the changed script and tests | Completed | 20261019-112524 | 20261019-112524 | bash -n passed; rollback option tested without Nuitka; a real staged build was not run (needs the operator); Plan Gap: the 2026-10-19 production build needed UV_SYSTEM_CERTS=true, not changed here |

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
- **Requirement ID**: `REQ-004` (staged build, build info, swap, rollback)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: deploy/build_binaries.sh