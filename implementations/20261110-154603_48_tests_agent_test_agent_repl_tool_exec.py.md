## Goal
Replace the empty-root allow-all test in `tests/agent/test_agent_repl_tool_exec.py` with a denial test (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `_make_cfg` here builds a `MagicMock` (line 29), so it is not affected by the config-load rejection; the only test that relies on the empty root is `test_empty_allowed_root_allows_anything` (line 151).
- Measured: 1 test in this file fails under deny-on-empty (that one); the `_classify_risk` tests use `allowed_root=""` through the mock and passed under the experiment, so they are left unchanged.

## Design decisions
- Rename and invert the assertion; keep the helper's default `allowed_root=""` so unrelated tests are untouched.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_agent_repl_tool_exec.py`

### Procedure
- Replace `test_empty_allowed_root_allows_anything` (lines 151-153) with `test_empty_allowed_root_denies_path_arguments` (new): `cfg = _make_cfg(allowed_root="")`; `assert not _check_allowed_root(cfg, "write_file", {"path": str(tmp_path / "a.txt")})`.

### Method
- Update the class or section docstrings in the file header (lines 1-10) only if they state that an empty root disables the check (`rg -n "empty|disabled" tests/agent/test_agent_repl_tool_exec.py`).

### Details
- The assertion depends on row 09 treating an empty root as deny for path-bearing calls; a call with no path argument is unaffected.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_agent_repl_tool_exec.py -v`

## Completion criteria
- No test asserts that an empty `allowed_root` allows a path.
- The file passes against the fail-closed code.

## Out of Scope
- `allowed_tools` cases (the file has none).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_agent_repl_tool_exec.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_agent_repl_tool_exec.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (empty `allowed_root` fails closed), `REQ-002`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_agent_repl_tool_exec.py`
