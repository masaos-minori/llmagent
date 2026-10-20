## Goal
Add regression coverage to `tests/eventbus/test_eventbus_config.py` for environment-reference resolution in
`load_config`: a set variable yields its value, an unset variable raises `ValueError` naming the variable, a
variable set to an empty string still reaches the existing non-empty error, per-role tokens behave the same, and
literal token configuration keeps working.

## Scope
- Append six test functions to the end of `tests/eventbus/test_eventbus_config.py`.
- No change to the twenty-plus existing cases and no change to any fixture other than pytest's `monkeypatch`.
- No new imports: `Path`, `pytest`, `EventBusConfig`, and `load_config` are already imported at lines 7-10.

## Assumptions
- `load_config` requires the `auth_token` key to be present in the TOML, so every new fixture keeps the key with
  either a literal value or a reference.
- The variable names used by the new cases are the names seq 02 ships (`EVENTBUS_AUTH_TOKEN` (new)) and one per-role
  name for the monitoring case; they are supplied only through `monkeypatch`, never through a file under `config/`.
- `tests/conftest.py` line 160 points `EVENTBUS_CONFIG_PATH` at the isolated copy of the repository config; every
  new case passes an explicit `tmp_path` file to `load_config`, so no case reads that copy.

## Design decisions
- Use the `monkeypatch` fixture rather than `os.environ` patching: it restores the variable even when the case
  raises, which keeps the suite order-independent under `-p no:randomly`.
- Assert the unset case with `pytest.raises(ValueError, match=...)` on the variable name, matching the resolver's
  message shape, instead of asserting an exact full string; the name is the contract `AC-2` cares about.
- Give the empty-string case a distinct `match` (`must not be empty`) so a future change that turns an empty
  variable into a resolver error is detected as a behavior change rather than passing either way.
- Keep each case's TOML inline in the same style as the existing cases (no shared helper), so a reader can see
  the whole configuration in one place.

## Alternatives considered
- Parametrize the six cases into one: rejected; the three failure modes assert different messages, and the
  per-role case asserts a different dataclass field.
- Add a case that reads the shipped `config/eventbus.toml` through `get_config_path()`: rejected; it would make
  the suite depend on `EVENTBUS_AUTH_TOKEN` (new) being set in the developer environment, and the isolated copy is
  already covered by the static checks in seq 02.
- Assert the resolved value only for `auth_token`: rejected; `REQ-002` covers all six token keys, and the
  per-role case is the one that proves the loop is not scoped to the shared token.

## Implementation
### Target file
`tests/eventbus/test_eventbus_config.py`

### Procedure
1. Append the shared-token cases: resolved, unset, set-but-empty.
2. Append the per-role cases: resolved, unset.
3. Append the mixed literal-plus-reference case that keeps literal configuration supported.

### Method
- Every new case writes its own TOML with `tmp_path / "eventbus.toml"`, the same shape as
  `test_monitoring_only_deployment_succeeds` at the end of the file.
- Reference values are written as the TOML-escaped reference string, e.g. `'auth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"\n'`.
- `monkeypatch.delenv("EVENTBUS_AUTH_TOKEN", raising=False)` is called first in the unset case so a developer's
  own environment cannot make the case pass vacuously.

### Details
Append after the last case in the file:

```python
# Before:
    cfg = load_config(config_file)
    assert cfg.monitoring_token == "test-monitoring-token"
    assert cfg.auth_token == "test-auth-token"
# After:
    cfg = load_config(config_file)
    assert cfg.monitoring_token == "test-monitoring-token"
    assert cfg.auth_token == "test-auth-token"


def test_load_config_resolves_shared_token_env_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-002: a "${ENV:...}" auth_token resolves to the variable's value."""
    monkeypatch.setenv("EVENTBUS_AUTH_TOKEN", "resolved-shared-token")
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text('...\nauth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"\n')
    cfg = load_config(config_file)
    assert cfg.auth_token == "resolved-shared-token"
    assert "${ENV:" not in cfg.auth_token
```

(The `...` above stands for the seven required key lines every existing case writes: `port`, `db_path`,
`storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry`, `host`.)

The remaining five cases follow the same shape:

| Case | Setup | Assertion |
|---|---|---|
| `test_load_config_shared_token_env_reference_unset_names_the_variable` (new) | `monkeypatch.delenv(..., raising=False)` | `pytest.raises(ValueError, match="EVENTBUS_AUTH_TOKEN")` |
| `test_load_config_shared_token_env_reference_empty_hits_non_empty_check` (new) | `monkeypatch.setenv("EVENTBUS_AUTH_TOKEN", "")` | `pytest.raises(ValueError, match="must not be empty")` |
| `test_load_config_resolves_per_role_token_env_reference` (new) | sets the monitoring variable | `cfg.monitoring_token` equals the value |
| `test_load_config_per_role_token_env_reference_unset_names_the_variable` (new) | deletes the monitoring variable | `pytest.raises(ValueError, match="EVENTBUS_MONITORING_TOKEN")` |
| `test_load_config_keeps_literal_tokens_supported_beside_references` (new) | literal shared token plus a resolved monitoring reference | both fields keep their values |

## Compatibility considerations
- Literal-token configuration remains supported, which is what keeps the existing cases green.
- The only new exception path is the resolver's `ValueError`; no existing message is reworded.
- The new cases depend on seq 01 being implemented: run them after it, and use the revert-and-bite check in the
  Plan's Validation plan to confirm they fail without it.

## Security considerations
- The unset case is the regression guard for the fail-closed contract: a placeholder must never load successfully.
- No case writes a real credential to disk; the values are obviously fake test strings, and no case reads a file
  under `config/`.

## Rollback considerations
Single-path revert: `git checkout HEAD -- tests/eventbus/test_eventbus_config.py`. The file only gains cases, so
removing them cannot affect production behavior.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Targeted | `uv run pytest tests/eventbus/test_eventbus_config.py -q -p no:randomly` | all cases green, six of them new |
| Revert-and-bite | `git checkout HEAD -- scripts/eventbus/config.py`, re-run, then restore | the reference cases fail, proving the new cases bite |
| Order independence | `uv run pytest tests/eventbus -q` twice | same result both runs, no variable leakage between cases |

## Completion criteria
- Six new cases exist with the names above.
- Both the unset cases assert that the message names the variable.
- `uv run pytest tests/eventbus -q` is green.

## Out of Scope
- `scripts/eventbus/config.py` (seq 01) and `config/eventbus.toml` (seq 02).
- `tests/deploy/test_load_env_gate.py` (seq 06) and the allowlist test module (seq 09).
- Any test that starts the Event Bus process or reads `/opt/llm`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-131830 | 20261020-131830 | six cases appended after test_monitoring_only_deployment_succeeds; Before anchor matched the file end |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-131830 | this document is the test target this document is the test target: 37 green (31 existing + 6 new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-131830 | ruff format/check and mypy clean; revert-and-bite for seq 01: config.py reverted to e683a8814 -> all 6 new cases failed, restored -> 37 green; note appended to seq 01 Step 2 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-131830 | docs are owned by seq 07, 08 N/A: docs owned by seq 07, 08 |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `tests/eventbus/test_eventbus_config.py`, `scripts/eventbus/config.py` (seq 01),
  `config/eventbus.toml` (seq 02), `tests/conftest.py` (read-only)