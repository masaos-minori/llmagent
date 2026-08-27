## Goal

Remove `ToolConfig.tool_cache_ttl` / `tool_cache_max_size` (dead configuration
fields — no code reads them since `ToolExecutor`'s cache was removed) and the
`_v_tool_cms` validator import/call that references `tool_cache_max_size`, per
`plans/20260827-121312_plan.md`'s `REQ-001`.

## Scope

- In scope: `scripts/agent/config_dataclasses.py` — the `validate_tool_cache_max_size
  as _v_tool_cms` import (verified at line 91 as of 2026-08-27), the
  `tool_cache_ttl`/`tool_cache_max_size` field declarations in `ToolConfig`
  (verified at lines 176, 178), and the `_v_tool_cms(self)` call in
  `ToolConfig.__post_init__` (verified at line 235).
- Out of scope: every other field/validator call in `ToolConfig` and every other
  dataclass in this file.

## Assumptions

- `ToolExecutor`'s constructor no longer accepts `cache_ttl`/`cache_max_size` —
  confirmed via `rg -n "cache_ttl|cache_max_size" scripts/agent/factory.py`
  returning no matches (the parallel implementation,
  `plans/done/20260826-120000_plan.md`, already removed the constructor
  arguments).
- `REQ-002` (`config_builders.py`) and `REQ-003` (`config_validators.py`) land in
  the same commit as this step — see Design in the source Plan. Landing this step
  alone would leave `config_builders.py::_build_tool_config` passing
  `tool_cache_ttl=`/`tool_cache_max_size=` keyword arguments that no longer exist
  on `ToolConfig`, breaking construction.

## Design decisions

- Delete the field declarations and their inline comments (the `# LRU eviction
  when exceeded; 0 = unlimited` comment on `tool_cache_max_size`'s line belongs to
  that field and is removed with it).
- Delete the `_v_tool_cms` import statement entirely (it is a single-purpose
  `from ... import X as Y` block with no other name in the same `import` group).
- Delete the `_v_tool_cms(self)` line from `__post_init__`; leave the other five
  validator calls untouched.
- Update the `ToolConfig` docstring ("Tool execution, caching, approval policy,
  and prompt settings.") to drop "caching" since no caching-related field remains
  after this change — re-check at implementation time whether any other cache
  field still exists on `ToolConfig` before removing the word (verify with `rg -n
  "cache" scripts/agent/config_dataclasses.py` around the `ToolConfig` class).

## Alternatives considered

- Keep the fields as inert configuration for forward-compatibility: rejected per
  the Plan's Reason for change — inert fields that look tunable but do nothing are
  a documentation/config-drift hazard, the same class of problem already being
  fixed for `docs/*.md` in the sibling Plan.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Re-run `rg -n "tool_cache_ttl|tool_cache_max_size|_v_tool_cms"
   scripts/agent/config_dataclasses.py` immediately before editing to confirm line
   numbers have not drifted since 2026-08-27.
2. Remove the `validate_tool_cache_max_size as _v_tool_cms` import block (line 91
   and its two `from agent.services.config_validators import (` /
   `)` wrapper lines — verify whether this import already shares a
   parenthesized block with an adjacent import at implementation time; if so,
   remove only the `_v_tool_cms` line and keep the block for the other import).
3. Remove `tool_cache_ttl: float = 300.0` and its trailing comment, and
   `tool_cache_max_size: int = 200` and its trailing comment, from `ToolConfig`
   (lines 176-178).
4. Remove `_v_tool_cms(self)` from `__post_init__` (line 235).
5. Update the `ToolConfig` docstring to remove "caching" if no other cache-related
   field remains (see Design decisions).
6. Run `uv run python tools/check_docs_consistency.py` if this repo's doc-drift
   checker inspects dataclass field lists (verify applicability at implementation
   time).

### Method
Direct text edit (Edit tool) — remove one import, two field declarations, one
`__post_init__` call, and adjust one docstring word.

### Details
Current text (verified 2026-08-27, lines 90-92):
```python
from agent.services.config_validators import (
    validate_tool_cache_max_size as _v_tool_cms,
)
```
Remove this block entirely (confirm at implementation time it is not merged with
an adjacent import in the same parenthesized group).

Current text (verified 2026-08-27, lines 173-178):
```python
@dataclass
class ToolConfig:
    """Tool execution, caching, approval policy, and prompt settings."""

    tool_cache_ttl: float = 300.0
    # LRU eviction when exceeded; 0 = unlimited
    tool_cache_max_size: int = 200
```
Change to:
```python
@dataclass
class ToolConfig:
    """Tool execution, approval policy, and prompt settings."""

```
(followed immediately by the next existing field, currently the
`build_execution_groups()`-related comment/field at line 179 — do not remove
that.)

Current text (verified 2026-08-27, lines 231-236):
```python
    def __post_init__(self) -> None:
        """Validate tool configuration fields after initialization."""
        _v_tool_dm(self)
        _v_tool_cdw(self)
        _v_tool_emc(self)
        _v_tool_cms(self)
        _v_tool_erm(self)
        _v_tool_psw(self)
```
Change to:
```python
    def __post_init__(self) -> None:
        """Validate tool configuration fields after initialization."""
        _v_tool_dm(self)
        _v_tool_cdw(self)
        _v_tool_emc(self)
        _v_tool_erm(self)
        _v_tool_psw(self)
```

## Compatibility considerations

- Public dataclass field removal: any caller constructing `ToolConfig(...)` with
  `tool_cache_ttl=`/`tool_cache_max_size=` keyword arguments will now raise
  `TypeError`. Confirmed no such caller exists outside `config_builders.py`
  (`REQ-002`, landing in the same commit) via `rg -n
  "tool_cache_ttl=|tool_cache_max_size=" scripts/`.
- No schema/config-file migration needed: TOML files may still contain a
  `tool_cache_ttl`/`tool_cache_max_size` key under `[tool]` — `config_builders.py`
  will simply stop reading it (dict lookup, not attribute access), so a stale key
  in an operator's TOML file is silently ignored rather than erroring.

## Security considerations

- N/A: dead-code removal, no security-relevant behavior change.

## Rollback considerations

- Single-file revert via `git diff` / `git checkout -- scripts/agent/config_dataclasses.py`.
- Must be rolled back together with `REQ-002`/`REQ-003` if any of the three is
  reverted, per Design (they land as one commit).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Static | `rg -n "tool_cache_ttl\|tool_cache_max_size\|_v_tool_cms" scripts/agent/config_dataclasses.py` | No matches |
| `scripts/agent/config_dataclasses.py` | Smoke test | `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"` | Succeeds without error |
| `tests/agent/` | Regression | `uv run pytest tests/agent/ -k "config_dataclasses" -v` | No new failures |

## Completion criteria

- `rg -n "tool_cache_ttl|tool_cache_max_size|_v_tool_cms"
  scripts/agent/config_dataclasses.py` returns no matches.
- `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"`
  succeeds.

## Out of scope

- Any other `ToolConfig` field or validator call.
- `config_builders.py` (`REQ-002`, separate implementation procedure) and
  `config_validators.py` (`REQ-003`, separate implementation procedure) — land
  together, documented separately per this workflow's one-target-file convention.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line numbers | Pending | — | — | |
| 2 | Remove `_v_tool_cms` import | Pending | — | — | |
| 3 | Remove `tool_cache_ttl`/`tool_cache_max_size` fields | Pending | — | — | |
| 4 | Remove `_v_tool_cms(self)` call | Pending | — | — | |
| 5 | Update `ToolConfig` docstring | Pending | — | — | |
| 6 | Run validation sequence | Pending | — | — | Coordinate with REQ-002/REQ-003 commits |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/done/20260827_toolexecutor_cache_removal_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260827-121312_plan.md`
- **Source implementation procedure**: supersedes
  `implementations/20260825-224356_09_scripts_agent_services_config_validators_py_config_dataclasses_py.md`,
  `implementations/20260826_03_scripts_agent_config_dataclasses.py.md`,
  `implementations/20260826_05_scripts_agent_config_dataclasses_py.md` (all left
  Pending/Blocked, none executed)
- **Generated at**: 20260827-134500
- **Related target files**: `scripts/agent/config_dataclasses.py`
