## Goal
Stop `tests/agent/test_http_lifecycle_env_allowlist_integration.py` from demanding that the subprocess
environment allowlist admit variables that no subprocess server reads, and assert instead that the Event Bus
control-plane credential stays out of the environment an agent child process receives.

## Scope
- Add the configuration classification constants and four helpers to the module.
- Narrow `_config_env_refs` to the configurations an agent subprocess server actually reads, and add a
  whole-`config/` variant for the parent-environment harness.
- Update the coverage test's message so it states the narrowed scope.
- Append one fast test class with three cases: exhaustive classification, non-admission of the other class, and a
  behavioral `filter_env` assertion.
- No change to `scripts/agent/http_lifecycle_command_validator.py`: `_DEFAULT_ALLOWED_ENV_VARS` is not widened.

## Assumptions
- The classification is measured, not assumed: `scripts/agent/http_lifecycle_subprocess_launcher.py` calls the
  filter only for `[mcp_servers.*]` entries with `startup_mode = "subprocess"`; those servers read
  `config/agent.toml` and their own `config/*_mcp_server.toml`; the rag_pipeline server imports
  `scripts/rag/ingestion`, which reads `crawler.toml`, `chunk_splitter.toml`, and `ingester.toml`.
- `config/eventbus.toml` is read only by `eventbus.app` (started by `deploy/setup_services.sh`, not by the agent),
  and `config/documentation_canonical_sources.toml` is read only by `tools/check_*.py`. Neither is a subprocess
  server's configuration.
- `config/agent.toml` defines no Event Bus server section, so today the Event Bus token cannot reach a child
  through this path. `UNK-05` records the case where that changes; if the Event Bus ever becomes a
  `startup_mode = "subprocess"` server this classification must move with it, and the classification test is what
  makes that a visible decision rather than an accident.
- The non-admission case asserts that the other class references at least one variable, so it depends on seq 02
  having shipped the reference in `config/eventbus.toml`. Implement this document after seq 02.
- Widening `_DEFAULT_ALLOWED_ENV_VARS` was measured and rejected: the patterns
  (`MCP_*_AUTH_TOKEN` and friends) apply to every subprocess server, so admitting the Event Bus token would hand a
  control-plane credential to the shell, git, file, github, cicd, rag_pipeline, and mdq children.

## Design decisions
- Classify by configuration file rather than by variable name: a name-based exception list grows every time a
  variable is added, while the question being answered ("does a subprocess server read this file?") has a small,
  checkable answer.
- Keep a whole-`config/` reference set for `_parent_env`: putting every shipped variable into the parent is what
  makes the child-side exclusion assertion bite. If the parent never carried the Event Bus token, an exclusion
  test could pass vacuously.
- Assert the other class is not admitted both statically (`_is_allowed`) and behaviorally (`filter_env` output):
  the static half catches a pattern change, the behavioral half catches a filter change.
- Keep the new class unmarked: it only reads files and calls `filter_env`, so it is not one of the real-subprocess
  startup gates marked `integration`.

## Alternatives considered
- Add `EVENTBUS_AUTH_TOKEN` (new) to `_DEFAULT_ALLOWED_ENV_VARS`: rejected, measured above.
- Skip the Event Bus file by name inside the existing scan while keeping one flat set: rejected; it leaves the
  scan claiming to cover "the shipped config" while silently excluding part of it, which is the drift the module
  docstring says this file exists to prevent.
- Assert only that `config/eventbus.toml` is excluded: rejected; `documentation_canonical_sources.toml` is in the
  same class, and the classification test needs a second member to prove the split is real.
- Move the Event Bus reference test into `tests/deploy/test_load_env_gate.py` (seq 06): rejected; the claim is
  about the agent subprocess boundary, which is this module's subject.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_env_allowlist_integration.py`

### Procedure
1. Add the classification constants after `_LOADER_ENV_VARS`.
2. Add the four helpers, narrow `_config_env_refs`, and add the whole-`config/` variant.
3. Point `_parent_env` at the whole-`config/` variant.
4. Update the coverage test's assertion message.
5. Append the new test class at the end of the module.

### Method
Edit 1 (constants; inserted after the existing `_LOADER_ENV_VARS` line):

```python
# Before:
_LOADER_ENV_VARS = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")
# After:
_LOADER_ENV_VARS = ("LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH")

# Configuration files whose `${ENV:...}` references a subprocess server actually reads: the
# servers load agent.toml plus their own *_mcp_server.toml, and the rag_pipeline server imports
# scripts/rag/ingestion, which reads the three ingestion files below.
_SUBPROCESS_REACHABLE_CONFIGS: frozenset[str] = frozenset(
    {"agent.toml", "crawler.toml", "chunk_splitter.toml", "ingester.toml"}
)
_SUBPROCESS_REACHABLE_PATTERNS: tuple[str, ...] = ("*_mcp_server.toml",)

# Configuration files no subprocess server reads: eventbus.toml is read by eventbus.app, which
# deploy/setup_services.sh starts directly, and documentation_canonical_sources.toml is read only
# by tools/. Their references must not widen what a child process is given.
_OTHER_PROCESS_CONFIGS: frozenset[str] = frozenset(
    {"eventbus.toml", "documentation_canonical_sources.toml"}
)
```

Edit 2 (helpers plus the narrowed scan):

```python
# Before:
def _config_env_refs() -> set[str]:
    """Every `${ENV:VAR}` variable name referenced by the shipped config."""
    refs: set[str] = set()
    for path in sorted(_CONFIG_DIR.glob("*.toml")):
        refs.update(_ENV_REF_RE.findall(path.read_text(encoding="utf-8")))
    return refs
# After:
def _shipped_config_files() -> list[Path]:
    """Every shipped configuration file under config/."""
    return sorted(_CONFIG_DIR.glob("*.toml"))


def _is_subprocess_reachable(name: str) -> bool:
    """Whether a configuration file is one an agent subprocess server reads."""
    return name in _SUBPROCESS_REACHABLE_CONFIGS or any(
        fnmatch.fnmatch(name, pattern) for pattern in _SUBPROCESS_REACHABLE_PATTERNS
    )


def _config_files_by_class() -> tuple[list[Path], list[Path]]:
    """Shipped configuration files split into (subprocess-reachable, other-process)."""
    reachable: list[Path] = []
    other: list[Path] = []
    for path in _shipped_config_files():
        if _is_subprocess_reachable(path.name):
            reachable.append(path)
        else:
            other.append(path)
    return reachable, other


def _env_refs_in(paths: list[Path]) -> set[str]:
    """`${ENV:VAR}` variable names referenced by the given files."""
    refs: set[str] = set()
    for path in paths:
        refs.update(_ENV_REF_RE.findall(path.read_text(encoding="utf-8")))
    return refs


def _config_env_refs() -> set[str]:
    """`${ENV:VAR}` names in the configurations an agent subprocess server reads."""
    return _env_refs_in(_config_files_by_class()[0])


def _all_config_env_refs() -> set[str]:
    """`${ENV:VAR}` names in every shipped configuration file."""
    return _env_refs_in(_shipped_config_files())
```

Edit 3 (the harness keeps feeding the parent with everything shipped):

```python
# Before:
        parent.update({name: "integration-test-token" for name in _config_env_refs()})
# After:
        parent.update({name: "integration-test-token" for name in _all_config_env_refs()})
```

Edit 4 (the coverage gate's scope becomes explicit):

```python
# Before:
    def test_config_env_refs_are_all_allowlisted(self) -> None:
        refs = _config_env_refs()
        assert refs, "no ${ENV:...} reference found in config/*.toml"
# After:
    def test_config_env_refs_are_all_allowlisted(self) -> None:
        refs = _config_env_refs()
        assert refs, "no ${ENV:...} reference found in the config files a subprocess server reads"
```

Edit 5 (appended after the last case of `TestFilteredEnvironmentStartsEveryServer`):

```python
# Before:
        assert "MCP_SHELL_AUTH_TOKEN" in (result.stderr or "")
# After:
        assert "MCP_SHELL_AUTH_TOKEN" in (result.stderr or "")


class TestSubprocessConfigClassification:
    """What the allowlist must cover, and what it must never be asked to cover."""

    def test_every_shipped_config_is_in_exactly_one_class(self) -> None:
        files = _shipped_config_files()
        assert files, "no configuration files found under config/"
        reachable, other = _config_files_by_class()
        assert {path.name for path in reachable}.isdisjoint({path.name for path in other})
        unclassified = sorted(
            path.name
            for path in files
            if not _is_subprocess_reachable(path.name) and path.name not in _OTHER_PROCESS_CONFIGS
        )
        assert not unclassified, (
            "config/*.toml files in neither class; adding a configuration is a decision "
            "about whether a subprocess server reads it: " + ", ".join(unclassified)
        )
        for name in sorted(_SUBPROCESS_REACHABLE_CONFIGS | _OTHER_PROCESS_CONFIGS):
            assert (_CONFIG_DIR / name).is_file(), f"classified configuration does not exist: {name}"

    def test_other_process_references_are_not_allowlisted(self) -> None:
        refs = _env_refs_in(_config_files_by_class()[1])
        assert refs, "the other-process configurations reference no ${ENV:...} variable"
        admitted = sorted(name for name in refs if _is_allowed(name))
        assert not admitted, (
            "the subprocess allowlist admits variables no subprocess server reads: "
            + ", ".join(admitted)
        )

    def test_filter_env_keeps_other_process_tokens_out_of_the_child(self) -> None:
        reachable_refs = _config_env_refs()
        other_refs = _env_refs_in(_config_files_by_class()[1])
        assert reachable_refs and other_refs, "classification produced an empty set"
        with patch.dict(os.environ, _parent_env(with_tokens=True), clear=True):
            filtered = CommandValidator().filter_env({})
        assert filtered is not None
        leaked = sorted(name for name in other_refs if name in filtered)
        assert not leaked, (
            "the filtered child environment carries a credential only another process reads: "
            + ", ".join(leaked)
        )
        missing = sorted(name for name in reachable_refs if name not in filtered)
        assert not missing, (
            "the filtered child environment lost a credential a server reads: " + ", ".join(missing)
        )
```

## Compatibility considerations
- The startup gates keep their behavior: `_parent_env` hands the child a superset (it now also carries the Event
  Bus variable), and the filter is what removes it, so `TestFilteredEnvironmentStartsEveryServer` keeps asserting
  sufficiency rather than necessity.
- `test_config_env_refs_are_all_allowlisted` keeps its contract for the reachable class; only its message and its
  input set narrow. Today the two classes differ by exactly `eventbus.toml`.
- No assertion in this module depends on `/opt/llm`.
- `scripts/agent/http_lifecycle_command_validator.py` and its allowlist stay untouched, so no child gains or loses
  a variable it used to receive.

## Security considerations
- The change tightens the security boundary in the only safe direction: it makes it a test failure for a
  control-plane credential to appear in a subprocess environment, instead of a test failure for the allowlist not
  covering it.
- The parent harness uses the fixed string `integration-test-token` for every name, so no real credential is ever
  in the environment the child sees.
- Keeping the classification exhaustive means a newly added configuration file cannot be silently ignored by the
  coverage gate.

## Rollback considerations
Single-path revert: `git checkout HEAD -- tests/agent/test_http_lifecycle_env_allowlist_integration.py`. The
module only gains helpers and cases; production code is untouched.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Fast cases | `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py -q -p no:randomly -m "not integration"` | all static cases plus the three new cases green |
| Startup gates | `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py -q -m integration` | the real-subprocess gates still start every configured server |
| Revert-and-bite (negative control) | temporarily add `EVENTBUS_AUTH_TOKEN` (new) to `_DEFAULT_ALLOWED_ENV_VARS` in a scratch copy, run the fast cases, then revert | `test_other_process_references_are_not_allowlisted` (new) and the `filter_env` case both fail, proving they bite |
| Static | `uv run mypy tests/agent/test_http_lifecycle_env_allowlist_integration.py` | no findings |
| Stale procedure | `uv run python tools/stale_detector.py implementations/20261020-112551_09_tests_agent_test_http_lifecycle_env_allowlist_integration.py.md` | no findings |

## Completion criteria
- Every file under `config/` with a `.toml` suffix is in exactly one class, and the classification test names both
  members of the other class.
- The three new cases pass, and the negative control shows they fail if the allowlist is widened.
- `_DEFAULT_ALLOWED_ENV_VARS` is unchanged in `git diff`.

## Out of Scope
- `scripts/agent/http_lifecycle_command_validator.py` and the allowlist patterns.
- `config/eventbus.toml` (seq 02) and `tests/deploy/test_load_env_gate.py` (seq 06).
- Making the Event Bus an agent-managed subprocess server (`UNK-05`), which needs its own issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-130356 | 20261020-130356 | after seq 02 five edits applied; all Before anchors matched source; one extra 'assert filtered is not None' line added for mypy (filter_env returns dict|None) and mirrored into this doc's Details |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-130356 | this document is the test target; 3 new cases appended; 6 fast cases green, 2 integration gates green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-130356 | ruff format/check, mypy clean; negative control: temporarily adding the token to _DEFAULT_ALLOWED_ENV_VARS failed both new cases, then git checkout restored the validator (diff empty); stale_detector green post-implementation |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-130356 | no docs row applies to this target; N/A: docs owned by seq 07, 08 |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `tests/agent/test_http_lifecycle_env_allowlist_integration.py`,
  `scripts/agent/http_lifecycle_command_validator.py` (read-only),
  `scripts/agent/http_lifecycle_subprocess_launcher.py` (read-only), `config/eventbus.toml` (seq 02),
  `config/agent.toml` (read-only)