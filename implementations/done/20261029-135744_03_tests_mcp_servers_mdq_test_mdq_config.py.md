## Goal

Add the two missing-config regression tests (Plan T1/T2) pinning that
`_load_auth_token()` returns `""` and `_collect_dependencies()` degrades to the empty
config view when `ConfigLoader.load()` raises `ConfigMissingError` (REQ-004).

## Scope

- New test class `TestConfigErrorDegradation` (new) in `tests/mcp_servers/mdq/test_mdq_config.py`
  with two tests; existing tests untouched.

## Assumptions

- `tests/mcp_servers/mdq/conftest.py` already provides the env the mdq modules need at
  import (existing mdq tests import these modules), so importing `mdq_server` in this
  file is safe.
- Patching `shared.config_loader.ConfigLoader.load` is sufficient: both call sites use
  `ConfigLoader().load(...)` (`scripts/mcp_servers/mdq/mdq_server.py:75`,
  `scripts/mcp_servers/mdq/health_check.py:143`).

## Design decisions

- Raise `ConfigMissingError` (the real `load()` failure mode for a missing file), not
  `FileNotFoundError` — this is the exact mismatch the Plan fixes; the test would fail
  against the pre-fix code.
- Keep tests pure unit: the config error aborts the `try` block before any DB probe, so
  no tmp DB fixture is needed.

## Alternatives considered

- N/A: no alternative for pinning an exception-path contract; a real missing-toml
  fixture would add fixture plumbing without covering `ConfigParseError`/`ConfigReadError`
  any better.

## Implementation
### Target file

`tests/mcp_servers/mdq/test_mdq_config.py`

### Procedure

Add the imports and a new test class at the end of the file.

### Method

```python
from shared.config_errors import ConfigMissingError
from shared.config_loader import ConfigLoader

from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.health_check import _collect_dependencies


class TestConfigErrorDegradation:
    def test_load_auth_token_returns_empty_on_config_missing_error(self) -> None:
        with patch.object(
            ConfigLoader, "load", side_effect=ConfigMissingError("no such toml")
        ):
            assert mdq_server._load_auth_token() == ""

    def test_collect_dependencies_records_config_error(self) -> None:
        with patch.object(
            ConfigLoader, "load", side_effect=ConfigMissingError("no such toml")
        ):
            deps, _details, mdq_cfg, *_rest = _collect_dependencies()
        assert "config" in deps
        assert deps["config"].startswith("check failed:")
        assert mdq_cfg == {}
```

### Details

- `patch.object(ConfigLoader, "load", ...)` (the file already imports `patch`) keeps the
  patch scoped to the `with` block and restores it afterwards, so no other test in the
  suite sees the side effect.
- The second test asserts the AC-3 contract parts it can observe: `deps["config"]`
  recorded with the `check failed:` prefix and an empty `mdq_cfg`; the remaining return
  values are captured with `*_rest` and ignored.

## Compatibility considerations

- Test-only change; existing config-fallback tests (e.g.
  `test_missing_config_file_falls_back_to_defaults`, which exercises `MdqService` with a
  `FileNotFoundError` side effect) stay untouched.

## Security considerations

- N/A: test-only addition; no new runtime surface.

## Rollback considerations

- N/A: revert the commit together with the two source changes.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py -v` — both new tests pass.
- `uv run pytest tests/mcp_servers/mdq` — suite green; the two new tests raise the
  pass count above the Plan's recorded Step 5 baseline (Plan T3).
- `uv run ruff check tests/mcp_servers/mdq`.

## Completion criteria

- T1 proves `_load_auth_token()` returns `""` on `ConfigMissingError` (AC-1).
- T2 proves `_collect_dependencies()` returns without raising with `deps["config"]`
  recorded and `mdq_cfg` empty (AC-3).
- Both tests fail against the pre-fix source (regression lock confirmed at first run).

## Out of Scope

- `scripts/mcp_servers/mdq/mdq_server.py` and `scripts/mcp_servers/mdq/health_check.py`
  (sibling procedure documents).
- `tests/mcp_servers/mdq/test_mdq_authentication.py` — unchanged fail-closed gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestConfigErrorDegradation` (new) with the two regression tests | Completed | — | 20261029-202648 | REQ-004 REQ-004; both tests pass vs fixed source; regression lock confirmed (fail at HEAD) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261029-202654 | REQ-004 REQ-004; ruff/mypy/lint-imports/bandit(-ll) clean; mdq suite 414 passed/1 skipped (baseline +2) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (regression tests for both callers' missing-config paths)
- **Source issue**: issues/20261029-012525_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-075321_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-135744
- **Related target files**: tests/mcp_servers/mdq/test_mdq_config.py