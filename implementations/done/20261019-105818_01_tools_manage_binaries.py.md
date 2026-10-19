## Goal
Create a standard-library-only tool that holds the binary build-info, freshness, swap, rollback, and revision-record logic so the deploy shell scripts stay thin and the logic is testable (`REQ-001`).

## Scope
- One new file in `tools/` with five subcommands: `write-info`, `check`, `swap`, `rollback`, `record-revision`, and a source-path table.
- No change to Nuitka flags, the entry table, or any production file.

## Assumptions
- Build info is `<binary>.build-info.json` next to the binary; the previous set lives in a sibling `<bin-dir>.prev` directory; the revision record is `<root>/DEPLOYED_REV` (Plan Assumptions).
- Only the standard library is used, and `git` is called by absolute path from `shutil.which`; run with `python3`.

## Design decisions
- The source-path table `BINARY_SOURCES` (new) is the single source of truth for which `scripts/` paths each binary embeds; the skill and documents point to it instead of repeating it.
- Integrity problems (checksum mismatch, not an executable ELF file, writable bin directory) always fail; freshness problems (stale, unknown) warn unless `--strict`.

## Alternatives considered
Implementing the logic in shell was rejected: it is not covered by pytest, ruff, or mypy and has no test harness here. Comparing only the HEAD commit (not per-path) was rejected: every documentation commit would mark all 11 binaries stale.

## Implementation
### Target file
`tools/manage_binaries.py` (new)

### Procedure
1. Define `BINARY_SOURCES` (new) mapping each of the 11 binary names to the repository path prefixes it embeds, plus `pyproject.toml` and `uv.lock` for all.
2. Implement `write_info` (new), `check`, `swap`, `rollback`, `record_revision` (new) and a `main` with argparse subcommands.
3. Add the git helpers `_git` (new) and `_changed_paths` (new), and the structural check `_structural_problems` (new).
4. Keep the module docstring in the style of `tools/check_db_separation.py` (purpose, usage, exit codes).

### Method
- Path table rows: `agent` embeds `scripts/agent/`, `scripts/db/`, `scripts/shared/`, `scripts/mcp_servers/`; mcp_mdq embeds `scripts/mcp_servers/mdq/`, the direct `.py` children of `scripts/mcp_servers/`, `scripts/db/`, `scripts/shared/`; mcp_rag_pipeline the same with `scripts/mcp_servers/rag_pipeline/` plus `scripts/rag/`; mcp_file_read, mcp_file_write, mcp_file_delete embed `scripts/mcp_servers/file/`; mcp_shell, mcp_git, mcp_web_search, mcp_github, mcp_cicd embed their own `scripts/mcp_servers/<name>/`; every MCP row also embeds the direct `.py` children of `scripts/mcp_servers/` and `scripts/shared/`.
- Matching rule: an entry ending in `/` matches by path prefix; an entry ending in `.py` with a `*` matches only direct children of its directory.
- `write-info --binary PATH --module NAME [--repo ROOT]`: write `PATH.build-info.json` with `name`, `sha256`, `source_commit` (new) (git HEAD), `source_dirty` (new) (porcelain status is non-empty), `built_at` (new) (UTC ISO 8601).
- `check --bin-dir DIR --rev REV|auto [--repo ROOT] [--names a,b] [--strict] [--list-stale]`: per binary report `ok`, `stale`, `unknown`, `mismatch`, or `invalid`; stale when the recorded commit differs from the revision and `git diff --name-only` between them touches a path of the binary's row, or the build was dirty, or the recorded commit is not in the repository; `--list-stale` prints the space-separated names that are stale or unknown (for `BUILD_ONLY`).
- `swap --stage-dir DIR --bin-dir DIR [--prev-dir DIR] [--names a,b]`: verify every staged binary first (structural check, and checksum against its build info when present); copy the current binaries and their info files to the previous directory; copy each staged binary to a temporary name in the bin directory and `os.replace` it into place; on any failure restore from the previous directory and exit non-zero.
- `rollback --bin-dir DIR [--prev-dir DIR] [--names a,b]`: restore the saved set the same way.
- `record-revision --root DIR --rev REV|auto [--repo ROOT]`: write `DEPLOYED_REV` (new) as JSON (`commit`, `dirty`, `deployed_at` (new), and each binary's `sha256` and recorded `source_commit` (new)) through a temporary file and `os.replace`.

### Details
- Exit codes: 0 success; 1 integrity failure, strict freshness failure, or any swap, rollback, or write failure; 2 usage error.
- Structural check: owner-executable regular file, non-empty, first four bytes `\x7fELF`, and the bin directory not group or world writable (mirrors the rule that the CommandValidator rejects binaries under a writable directory).
- Use list-form `subprocess.run` with the resolved git path and `# nosec B603 — fixed git executable, list arguments, no shell`; write English-only comments and log output.

## Compatibility considerations
New file; the scripts that call it are separate procedures. Default `check` behavior warns on stale or unknown so existing flows keep working.

## Security considerations
No network and no shell. Paths come from command-line arguments of operators and scripts; the tool refuses a bin directory that is group or world writable and writes the revision record atomically.

## Rollback considerations
N/A: revert the commit (the file is new and called only by the other procedures' scripts).

## Validation plan
- `uv run ruff format tools/manage_binaries.py && uv run ruff check tools/manage_binaries.py`
- `uv run mypy tools/manage_binaries.py`
- `uv run bandit tools/manage_binaries.py`
- `uv run pytest tests/tools/test_manage_binaries.py -q`
- A smoke run on real repository data: `python3 tools/manage_binaries.py check --bin-dir <a temporary directory with a fake binary> --rev auto`

## Completion criteria
- All five subcommands behave as specified and the tool is clean under ruff, mypy, and bandit.
- The tests in the sibling procedure pass against it.

## Out of scope
- Calling the tool from the scripts (separate procedures)
- A runtime smoke mode for the binaries (Plan UNK-01)
- Reading or writing anything under `/opt/llm` during development

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the module with the path table and the five subcommands | Completed | 20261019-112524 | 20261019-112524 |  |
| 2 | Add or update tests (separate procedure) | Completed | 20261019-112524 | 20261019-112524 |  |
| 3 | Run the `routing.md` tool validation sequence and a smoke run | Completed | 20261019-112524 | 20261019-112524 | ruff, mypy, bandit clean (B404/B103 nosec justified); smoke on real data: check against /opt/llm/bin reports all 11 unknown (no build info yet), strict exits 1, --list-stale prints all names |
| 4 | Update `tools/TOOL_DESCRIPTIONS.md` (separate procedure) | Completed | 20261019-112524 | 20261019-112524 |  |

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
- **Requirement ID**: `REQ-001` (build info, freshness, swap, rollback, revision record)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: tools/manage_binaries.py