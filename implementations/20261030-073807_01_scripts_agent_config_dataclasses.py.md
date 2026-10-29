## Goal

Add a strict-positive lower-bound guard to `AgentConfig.agent_memory_max_startup_snippets`
so values `<= 0` raise `ValueError` at construction, keeping the default at 10 (REQ-001).

## Scope

Modify only `scripts/agent/config_dataclasses.py`: add a `ValueError` guard for
`agent_memory_max_startup_snippets <= 0` to `AgentConfig`'s construction-time
validation, invoked from `__post_init__`. No other file (the test lives in the sibling
procedure for `tests/agent/test_config_dataclasses.py`).

## Assumptions

- `AgentConfig` is a stdlib `@dataclass` (`from dataclasses import dataclass, field`,
  no pydantic), so validation belongs in a `__post_init__`-called method, not a
  `pydantic.Field(gt=0)` constraint (verified in Step 3a).
- The field is owned directly by `AgentConfig` (line 400); there is no
  AgentMemoryConfig (verified in Step 3a).
- Every existing usage is positive (default 10; `config_builders.py` defaults to 10;
  existing tests set 10), so the guard cannot break an existing construction.
- The guard is enforced at construction only; `startup_prompt_setup.py` is not clamped
  at the call site.

## Design decisions

- Add a dedicated `_validate_memory_max_startup_snippets()` method called from
  `__post_init__`, rather than inside `_validate_cross_field`: the check bounds a
  single scalar field, not a cross-field dependency, so it does not belong among the
  two sub-config-boundary validators. This is purely additive and cannot reorder or
  interfere with `_validate_memory_jsonl_dir` / `_validate_memory_embed_url`.
- Name the field in the `ValueError` message, matching the existing
  `_validate_memory_jsonl_dir` / `_validate_memory_embed_url` convention so the test's
  `match="<field>"` assertion reads naturally.

## Alternatives considered

N/A: single-guard Path A change; putting it inside `_validate_cross_field` risks
reordering the two existing cross-field checks and mislabels a scalar bound as a
cross-field dependency.

## Implementation
### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. In `AgentConfig.__post_init__`, call the new validator after the existing
   `_validate_cross_field()` call.
2. Define `_validate_memory_max_startup_snippets()` on `AgentConfig`, raising
   `ValueError` when the field is `<= 0`.

### Method

Edit `__post_init__` (current lines 402-404) to append one delegation line. Append the
new method at the end of the file, after `_validate_memory_embed_url` (the last method
in the class; the file is 423 lines).

### Details

Change `__post_init__` (current lines 402-404):

```python
    def __post_init__(self) -> None:
        """Validate cross-field dependencies between sub-configs."""
        self._validate_cross_field()
```

to:

```python
    def __post_init__(self) -> None:
        """Validate cross-field dependencies between sub-configs."""
        self._validate_cross_field()
        self._validate_memory_max_startup_snippets()
```

Append the new method at the end of the file (after `_validate_memory_embed_url`,
which currently ends the file at line 423):

```python

    def _validate_memory_max_startup_snippets(self) -> None:
        """Raise ValueError when agent_memory_max_startup_snippets is not positive."""
        if self.agent_memory_max_startup_snippets <= 0:
            raise ValueError(
                "agent_memory_max_startup_snippets must be >= 1",
            )
```

## Compatibility considerations

`TestAgentConfigValidation::test_defaults_are_valid` constructs
`AgentConfig(rag=RAGConfig(embed_url=...))` with the default value 10 (> 0), so the new
guard does not affect it. All other existing constructions pass a positive value.

## Security considerations

N/A: no auth, secret, or credential-handling change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy (Unit) | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py::AgentConfig` (construction) | Positive: `AgentConfig(agent_memory_max_startup_snippets=0)` and `-1` raise `ValueError`; `1`, `5`, and the default construct successfully | `uv run pytest tests/agent/test_config_dataclasses.py -k "AgentConfig"` | New + existing `TestAgentConfigValidation` tests pass |

## Completion criteria

- Constructing `AgentConfig` with `agent_memory_max_startup_snippets <= 0` raises
  `ValueError` whose message names the field.
- Constructing `AgentConfig` with `agent_memory_max_startup_snippets >= 1` succeeds,
  and the default remains 10.
- Existing `TestAgentConfigValidation` tests still pass (notably `test_defaults_are_valid`).

## Out of Scope

The unit test for the rejection/acceptance cases (sibling procedure); changing the
slice semantics in `startup_prompt_setup.py`; clamping at the call site; changing the
default value or any other `AgentConfig` field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (reject `agent_memory_max_startup_snippets <= 0` at construction, keep default 10)
- **Source issue**: issues/20261029-220801_memcfg001_max-snippets-range.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-070223_memcfg001_max-snippets-range.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-073807
- **Related target files**: scripts/agent/config_dataclasses.py
