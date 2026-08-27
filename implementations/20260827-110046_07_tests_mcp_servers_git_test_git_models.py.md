## Goal

Extend `tests/mcp_servers/git/test_git_models.py` with a case that loads
`config/git_mcp_server.toml` via `GitConfig.load()` and asserts
`protected_branches == ["main", "master", "release"]` (REQ-006 test half), per
`plans/20260826-113056_plan.md`.

## Scope

- In scope: one new test method in `TestGitConfigFromDict` (or a new small test
  class) covering the shipped-config load path.
- Out of scope: any other test in this file; any change to `GitConfig` itself
  (already parses `protected_branches`, verified 2026-08-27).

## Assumptions

- `config/git_mcp_server.toml` will contain `protected_branches = ["main", "master",
  "release"]` once the REQ-006 config item (separate target file, this same pass)
  lands — this test's assertion depends on that value; do not implement this test
  before or independently of that config change landing, or the assertion will fail
  against the current (`[]`-default) shipped config.
- `GitConfig.load()` (`git_models.py:60-63`) calls
  `ConfigLoader().load("git_mcp_server.toml")` with no path argument — it resolves
  the file via the project's standard config-loading convention (same one used by
  the existing config tests in this repository); re-verify `ConfigLoader`'s
  resolution path if this test cannot locate the file when run.

## Design decisions

- Add the new test as a plain function-style assertion against `GitConfig.load()`,
  matching this file's existing pattern of one assertion-focused test method per
  behavior, rather than a broader integration test class.
- Do not duplicate the full `GitConfig.from_dict()` fixture already used by
  `TestGitConfigFromDict` — call `GitConfig.load()` directly since this test's whole
  point is exercising the real file-loading path, not the `from_dict()` parsing
  logic already covered by that class.

## Alternatives considered

- Mocking `ConfigLoader().load()` to return a hand-built dict was considered and
  rejected — this Plan's REQ-006 explicitly requires demonstrating the assertion
  "when the service is constructed from the shipped config file (not only from the
  test's own hand-built fixture)"; mocking would defeat that purpose.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_models.py`

### Procedure
1. Add a new test method (e.g. `test_load_reads_protected_branches_from_shipped_config`)
   calling `GitConfig.load()` and asserting the `protected_branches` field.
2. Run `uv run pytest tests/mcp_servers/git/test_git_models.py -v`.

### Method
Direct file edit (Edit tool) adding one test method; no changes to existing tests.

### Details
Current file structure (verified 2026-08-27): `TestGitConfigFromDict` class with
methods like `test_valid_dict_populates_all_fields`,
`test_missing_optional_fields_use_defaults`, each constructing a `GitConfig` via
`GitConfig.from_dict({...})` with an inline dict literal. Add a new method (either in
this class or a new `TestGitConfigLoad` class, whichever keeps the file's existing
class-per-concern structure most consistent — verify current file organization
before deciding) with body equivalent to:
```python
def test_load_reads_protected_branches_from_shipped_config(self) -> None:
    cfg = GitConfig.load()
    assert cfg.protected_branches == ["main", "master", "release"]
```
This exercises `GitConfig.load()` (`git_models.py:60-63`), not `from_dict()` directly
— it depends on the actual `config/git_mcp_server.toml` file content, so it will only
pass once the REQ-006 config item lands.

## Compatibility considerations

- Test-only change; no production code path is affected.
- This test creates a dependency on `config/git_mcp_server.toml`'s exact
  `protected_branches` value — if that value changes in the future for unrelated
  reasons, this test will need updating too; this is an accepted characterization-test
  tradeoff (this test file's own docstring already states its purpose is to "lock the
  exact validation behavior").

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Single-method revert via `git diff`/`git checkout -- <path>`; no other test depends
  on this new method.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/git/test_git_models.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | New test passes once REQ-006's config change has landed; all existing tests in this file remain green |

## Completion criteria

- A test in this file loads `config/git_mcp_server.toml` via `GitConfig.load()` and
  asserts `protected_branches == ["main", "master", "release"]`.
- The test passes only after the REQ-006 config item (`config/git_mcp_server.toml`)
  has landed — if implemented first, note in the Blocker Log that this test will
  fail (`Not implemented` ordering caveat) until that config change is applied.

## Out of scope

- Any other test method in this file.
- Any change to `GitConfig`, `ConfigLoader`, or `config/git_mcp_server.toml` itself
  (separate target file in this pass).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_load_reads_protected_branches_from_shipped_config` | Pending | — | — | Depends on `config/git_mcp_server.toml`'s `protected_branches` key landing first |
| 2 | Run `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | This test's assertion is only valid after `config/git_mcp_server.toml` sets `protected_branches`; implement the config item first or in the same commit | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `tests/mcp_servers/git/test_git_models.py`
