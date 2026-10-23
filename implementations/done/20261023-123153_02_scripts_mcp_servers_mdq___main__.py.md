## Goal
Stop `python -m mcp_servers.mdq` from starting the server at import time and correct the docstring's module path (`REQ-003`).

## Scope
- Rewrite the 8-line module: add the `if __name__ == "__main__":` guard and fix the docstring text.

## Assumptions
- `tools/check_docstrings_baseline.txt` grandfathers this file as "missing separator"; the docstring format must stay as it is (no ` — ` separator) or the baseline entry turns stale and fails.
- `scripts/mcp_launcher.py` already skips `__main__` modules during discovery, so the guard does not change discovery.

## Design decisions
- Call `MdqMCPServer().run_http()` only under the guard; the gate now lives in `run_http()` (server row), so no gate call is needed here.

## Alternatives considered
- Delete the file: rejected, `python -m mcp_servers.mdq` is a documented entry point.

## Implementation
### Target file
`scripts/mcp_servers/mdq/__main__.py`

### Procedure
1. Change the docstring line `Entry point: python -m mcp_servers.mdq.server` to `Entry point: python -m mcp_servers.mdq`, keeping the existing two-line format.
2. Replace the module-level `server = MdqMCPServer()` / `server.run_http()` with an `if __name__ == "__main__":` block calling `MdqMCPServer().run_http()`.

### Method
- Keep the import `from mcp_servers.mdq.mdq_server import MdqMCPServer` at module level.

### Details
- Evidence: `mdq/__main__.py` lines 1-8 (server started at import; docstring names a non-existent module).

## Compatibility considerations
- Importing the module no longer starts a server; running it with `-m` behaves as before (now gated).

## Security considerations
- Removes an ungated start path.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_posture_gate_start_path.py` (import does not start a server; `runpy` run goes through the gated path), `uv run python tools/check_docstrings.py` (baseline must stay clean), `uv run ruff check`, `uv run mypy`.

## Completion criteria
- Importing the module starts nothing, `-m` starts the gated server, docstring names `python -m mcp_servers.mdq`, docstring gate passes.

## Out of Scope
- Editing `tools/check_docstrings_baseline.txt`
- Any change to `mdq_server.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the guard and docstring text per Implementation > Procedure | Completed | 20261023-125624 | 20261023-125624 | implemented; targeted tests passed (tests/mcp_servers, startup, binaries: 2516 passed); full suite run at the end of the batch |
| 2 | Add or update tests per Validation plan (tracked in `tests/mcp_servers/test_posture_gate_start_path.py`) | Completed | 20261023-125624 | 20261023-125624 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-125624 | 20261023-125624 |  |

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
- **Requirement ID**: `REQ-003` (guard and docstring)
- **Source issue**: issues/20261023-114021_mcpstart002_posture-gate-bypassed-by-launchers-and-mdq-main.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123153
- **Related target files**: scripts/mcp_servers/mdq/__main__.py