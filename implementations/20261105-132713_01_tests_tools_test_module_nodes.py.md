## Goal
- Add `tests/tools/test_module_nodes.py` so that a break in `measure`, `extract`, or `compare` of `tools/module_nodes.py` fails a test, with at least one negative path per subcommand (`REQ-001`: tests for the three subcommands; `REQ-004`: tests write only inside `tmp_path`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file. No change to `tools/module_nodes.py`; a defect found by a test is filed as a separate issue.
- Plan: `plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md`, Plan step 3 (Phase 3).

## Assumptions
- Tests import the tool as `tools.module_nodes`, like `tests/tools/test_check_module_size.py` (`tests/conftest.py` already puts `tools/` on `sys.path`).
- `compare` has no local-file mode: `_cmd_compare` always runs `git show {old_rev}:{old_src}` with `check=True`. The Plan was corrected for this in Step 3a; the tests fake `subprocess.run` and never run git (verified against `tools/module_nodes.py`, 2026-11-05).
- `extract` errors raise `SystemExit` with an `ERROR:` string, not a return code, so the tests use `pytest.raises(SystemExit)`.
- Plan overlap: `tools/module_nodes.py` is also a target of the `toolcommon001` and `toolwrite001` Plans; both depend on this Plan and are sequenced after it (a sequencing dependency, not a conflict).
- Byte size is the encoded length of the node's lines joined by newlines (Plan UNK-01, non-blocking).

## Design decisions
- Build every fixture from a small source string written to `tmp_path`; call `measure`, `_extract_lines`, and `main([...])` so the real argparse paths run.
- An autouse fixture replaces `tools.module_nodes.subprocess.run` with a function that fails the test, so no test can reach real git unless it installs its own fake.
- Assert exact text and exact numbers (spans, byte counts, moved text), not only exit codes.

## Alternatives considered
- Running `compare` against a real temporary git repository: rejected, it needs a git binary and a repository fixture, and Plan REQ-004 forbids git runs; a faked `subprocess.run` covers the same code.

## Implementation
### Target file
`tests/tools/test_module_nodes.py` (new)

### Procedure
1. Create the module with a docstring, `from __future__ import annotations`, and imports of `json`, `subprocess`, `pathlib.Path`, `pytest`, and `from tools.module_nodes import _extract_lines, main, measure`.
2. Add a module-level `SAMPLE` (new) source string: two import lines, a constant assignment, a function with a non-ASCII character in its docstring, a class with one method, and a second function.
3. Add the autouse fixture that makes any unfaked `subprocess.run` call fail the test.
4. Add the `measure` tests, then the `extract` tests, then the `compare` tests (Method below).

### Method
- `measure`: top-level imports are absent from the rows; the assignment row is named after its node type (`Assign`); `alpha` has the expected `start`, `end`, `span`, and `kind`; `bytes` equals the UTF-8 length of the joined lines and is larger than the character count for the non-ASCII node; `--min N` drops nodes under N bytes and keeps nodes at or above N; `--json` output equals `json.dumps` of `measure(...)` rows; a missing file returns 1 and writes `not found` to stderr; the text report ends with `file total: <bytes>B`.
- `extract`: `--name alpha` creates the destination with exactly that function's original text plus a trailing newline, removes it from the source, and keeps every other line; an existing destination is kept and the moved text is appended after two blank lines; two `--name` options move both in the requested order (`_extract_lines` returns the kept lines and the moved segments); `--range` moves the class method span, and with `--dedent` the span becomes a module-level function (one 4-space level removed) while without it the indent stays; `--dedent` on a span with a line indented by less than 4 spaces raises `SystemExit` with `cannot --dedent`; an unknown name raises `SystemExit` with `not top-level nodes`; no `--name` and no `--range` raises `SystemExit` with `pass at least one`; `--range 5-2` and `--range abc` raise `SystemExit` with `ERROR`; the printed summary line reads `moved N nodes -> <dest>`.
- `compare`: install a fake `subprocess.run` that records its argv and returns `subprocess.CompletedProcess` with the old source as `stdout`. Identical move (a method `_helper(self, x)` becoming a module function `helper(x)`) returns 0 and prints `identical` and `differing: 0`; a changed body returns 1 and prints `DIFFERS` with `old:` and `new:` lines; a name present in neither source returns 1 and prints `MISSING`; the recorded argv is `["git", "show", "HEAD:<old-src>"]`, and `--old-rev abc123` changes it to `abc123:<old-src>`; `--old-class` and `--param` are covered by one case where an injected parameter makes a moved body identical.

### Details
- Use absolute `tmp_path` paths in every `main([...])` call; never a relative path.
- Assert printed output through `capsys`; assert `SystemExit` messages through `excinfo.value.code`.
- Keep each test under about 20 lines by sharing small helper functions for writing the fixture files.
- Do not import or call `module_nodes._cmd_*` directly; go through `main` except for `measure` and `_extract_lines`, which the Plan names as direct targets.

## Compatibility considerations
N/A: new test file; no tool, schema, or public contract changes.

## Security considerations
N/A: tests write only inside `tmp_path` and cannot reach git, the network, or the repository (guarded by the autouse fixture).

## Rollback considerations
N/A: revert the commit; deleting the file loses only the tests.

## Validation plan
- `uv run pytest tests/tools/test_module_nodes.py -q` passes.
- `uv run ruff format tests/tools/test_module_nodes.py` and `uv run ruff check tests/tools/test_module_nodes.py` are clean.
- `uv run python tools/check_mock_patch_targets.py` reports no finding for the patch target.
- Mutation check: temporarily change `size < min_bytes` in `tools/module_nodes.py` to `<=`, confirm a test fails, revert, and confirm `git diff --stat tools/` is empty.
- `uv run pytest tests/tools -q` shows no new failure.

## Completion criteria
- The file exists and covers `measure`, `extract`, and `compare` with at least one negative-path test each.
- No test calls real git, and `git status` shows no change outside the new file after the run.
- The mutation check failed a test and was reverted.

## Out of Scope
- Changes to `tools/module_nodes.py`, including its `compare` design and the `extract` write path.
- Tests for the other untested tools named in the Plan's Out-of-Scope.
- Filing issues for defects the tests reveal.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the fixture, the autouse guard, and the `measure` tests | Pending | — | — | |
| 2 | Add the `extract` tests, including the `SystemExit` negative paths | Pending | — | — | |
| 3 | Add the `compare` tests with the faked `subprocess.run` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (tests for `measure`, `extract`, `compare`), `REQ-004` (tests stay inside `tmp_path`)
- **Source issue**: issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-132713
- **Related target files**: `tests/tools/test_module_nodes.py`
