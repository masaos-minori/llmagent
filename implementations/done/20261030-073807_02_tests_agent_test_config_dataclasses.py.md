## Goal

Add unit tests to `TestAgentConfigValidation` in `tests/agent/test_config_dataclasses.py`
covering the new `agent_memory_max_startup_snippets` positive-bound guard: rejection of 0
and negatives, acceptance of 1 and 5, and the default of 10 (REQ-002).

## Scope

Modify only `tests/agent/test_config_dataclasses.py`: append four tests to the existing
`TestAgentConfigValidation` class. The production guard itself is implemented by the
sibling procedure for `scripts/agent/config_dataclasses.py`.

## Assumptions

- The guard raises `ValueError` with the message `agent_memory_max_startup_snippets must
  be >= 1` (verified in the sibling procedure's Step 3a), so the test matches on the
  field name.
- Construction still runs `_validate_cross_field()` before the new guard, so each new
  test must supply a valid `rag=RAGConfig(embed_url=...)` or the cross-field check raises
  first (verified in Step 3a).
- `pytest` and `RAGConfig` are already imported at the top of the file.

## Design decisions

- Follow the existing `TestAgentConfigValidation` convention of
  `pytest.raises(ValueError, match="<field>")` (e.g. `match="embed_url"`), matching on the
  field name rather than the full message.
- Group the two positive acceptance values (1 and 5) in one looped test; keep the default
  assertion separate, mirroring the explicit per-case style of the rest of the file.

## Alternatives considered

N/A: additive test-only Path A change; adding nothing would leave REQ-002 unverified.

## Implementation
### Target file

`tests/agent/test_config_dataclasses.py`

### Procedure

1. Append four tests to `TestAgentConfigValidation`: zero raises, negative raises,
   positive values (1 and 5) pass, and the default is 10.

### Method

Insert the four methods immediately after `test_default_diagnostics_config` (the last
method of the class, ending at line 244) and before the blank line that precedes the
`DiagnosticsConfig` section header. Each rejection test supplies
`rag=RAGConfig(embed_url="http://localhost:8080")` so the cross-field check passes and the
new guard is reached.

### Details

Append the following block right after `test_default_diagnostics_config` (current line
244):

```python

    def test_agent_config_max_startup_snippets_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            AgentConfig(
                agent_memory_max_startup_snippets=0,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            AgentConfig(
                agent_memory_max_startup_snippets=-1,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_positive_values_pass(self) -> None:
        for value in (1, 5):
            cfg = AgentConfig(
                agent_memory_max_startup_snippets=value,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )
            assert cfg.agent_memory_max_startup_snippets == value

    def test_agent_config_max_startup_snippets_default_is_ten(self) -> None:
        cfg = AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080"))
        assert cfg.agent_memory_max_startup_snippets == 10
```

## Compatibility considerations

The new tests sit in the existing `TestAgentConfigValidation` class and do not touch
`test_defaults_are_valid`, `test_memory_embed_without_embed_url_raises`, or
`test_memory_layer_without_jsonl_dir_raises`; appending methods cannot reorder them.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_config_dataclasses.py::TestAgentConfigValidation` | New rejection/acceptance/default tests pass alongside existing ones | `uv run pytest tests/agent/test_config_dataclasses.py -k "AgentConfig"` | All `TestAgentConfigValidation` tests pass |
| `tests/agent/test_config_dataclasses.py` | Full-suite regression | `uv run pytest tests/agent/test_config_dataclasses.py` | All tests pass |

## Completion criteria

- Four methods exist in `TestAgentConfigValidation`:
  `test_agent_config_max_startup_snippets_zero_raises` (new),
  `test_agent_config_max_startup_snippets_negative_raises` (new),
  `test_agent_config_max_startup_snippets_positive_values_pass` (new),
  `test_agent_config_max_startup_snippets_default_is_ten` (new).
- `AgentConfig(agent_memory_max_startup_snippets=0)` and `-1` raise `ValueError` matching
  the field; `1`, `5`, and the default construct successfully; the default equals 10.
- The full `tests/agent/test_config_dataclasses.py` suite passes.

## Out of Scope

The guard implementation in `scripts/agent/config_dataclasses.py` (sibling procedure);
changing any other `Test*ConfigValidation` class; the prompt-setup regression suite.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tests described in Implementation > Procedure/Method/Details | Completed | 20261030-104309 | 20261030-104309 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-104309 | 20261030-104309 | ruff/mypy/bandit clean; new + existing AgentConfig tests pass; full suite 10441 passed; diff-cover 100% on changed lines |

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
- **Requirement ID**: `REQ-002` (unit test asserting rejection of ≤ 0 and acceptance of ≥ 1, default 10)
- **Source issue**: issues/20261029-220801_memcfg001_max-snippets-range.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-070223_memcfg001_max-snippets-range.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-073807
- **Related target files**: tests/agent/test_config_dataclasses.py