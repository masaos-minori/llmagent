## Goal

Create one shared resolver `resolve_memory_jsonl_dir()` (REQ-001) that returns the JSONL archive directory from the flat `memory_jsonl_dir` config key using the builder's default, so the three change-event writers stop reading the non-existent nested `cfg["memory"]["memory_jsonl_dir"]` shape and `/memory delete`, `/memory pin`, `/memory unpin`, and `/memory prune` can append their change events instead of raising `KeyError('memory')`.

## Scope

- New file `scripts/agent/memory/config_path.py` (new) containing exactly one public function `resolve_memory_jsonl_dir()`.
- Consumed by `write_ops._emit_delete_event`, `pin_ops._emit_event`, and `memory_data_ops._emit_prune_event` once they are rerouted through the resolver (separate rows).
- No other symbols, no module-level state, no public API beyond the one resolver.

## Assumptions

- The resolver belongs in the `agent.memory` package and imports `ConfigLoader` from `shared`; this respects the enforced `agent → shared` boundary (lint-imports reports 6/6 KEPT, 0 broken).
- `ConfigLoader().load("agent.toml")` returns the raw flat TOML dict where `memory_jsonl_dir` is a top-level key (Reference Files: `config_loader.py`). The nested `memory` mapping exists only on the built `ctx.cfg.memory` dataclass, never on the loaded dict.
- An unset `memory_jsonl_dir` must resolve to the same path as the built `MemoryConfig.memory_jsonl_dir` (the builder default `/opt/llm/memory`).

## Design decisions

- **Reproduce the builder's accessor policy.** Load the flat config and read `memory_jsonl_dir` through the same `_get_str_or_default` helper that `config_section_builders._build_memory_config` uses (line 229), passing the same default literal. This makes the accessor identical by construction rather than re-implementing a subtly different fallback.
- **Local imports inside the function.** Match the existing writer pattern (each emit helper imports `ConfigLoader`/`JsonlMemoryStore` lazily) to avoid import-time coupling and keep the new module cheap to import in tests.

## Alternatives considered

- **Inline `.get()` fallback** (`cfg.get("memory_jsonl_dir", DEFAULT)`) — shorter but duplicates the str-coercion/default logic the builder already owns; rejected in favor of reusing `_get_str_or_default`.
- **Extract a shared named default constant** into `config_section_builders.py` and reference it from both the builder and the resolver — gives a true single source of truth for the *value*, but adds a second modification target. Per UNK-01 this requires amending the frozen `Implementation Target Files` table; it is out of the frozen scope for this row. Implement the bounded version below; if the shared-constant approach is preferred, stop and report `Blocked: additional target file discovered — config_section_builders.py` so the Plan can be amended (workflow.md Step 3).

## Implementation

### Target file
`scripts/agent/memory/config_path.py` (new)

### Procedure
1. Create `scripts/agent/memory/config_path.py` (new). Add a module docstring describing the shared resolver and its single responsibility.
2. Define `def resolve_memory_jsonl_dir() -> str:` (new). Inside the function:
   - `from shared.config_loader import ConfigLoader` (new import).
   - `cfg = ConfigLoader().load("agent.toml")`.
   - `from agent.config_section_builders import _get_str_or_default` (new import).
   - `return _get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")`.
3. Keep the file to the docstring plus this single function — no extra helpers, constants, or `__all__`.

### Method
Flat-config read + builder-default fallback, returning only a path string. SQLite-first ordering is preserved by construction: this resolver returns a string only; callers still append after the SQLite commit and re-raise real append failures (M-07) unchanged.

### Details
- Signature: `def resolve_memory_jsonl_dir() -> str:`.
- The default literal `/opt/llm/memory` is currently duplicated between this resolver and `config_section_builders._build_memory_config` (line 229). Reusing `_get_str_or_default` centralizes the *accessor*; the literal itself stays duplicated unless the frozen table is amended (UNK-01).
- Do not thread `AgentContext`/`ctx.cfg` through the emit helpers. The minimal fix keeps each writer's local `ConfigLoader().load("agent.toml")` and only corrects the key access (Plan Assumptions).
- Reference access pattern for parity: `factory.py` line 264 resolves the same path as `ctx.cfg.memory.memory_jsonl_dir`; the resolver's output must equal that value for the same input.

## Compatibility considerations
N/A: the resolver is a brand-new module with no callers yet in this row; the three writers consume it in later rows. No existing import edge changes here.

## Security considerations
N/A: no new privilege, file-permission, or injection surface; the resolver only reads a config path string.

## Rollback considerations
Delete the new file `scripts/agent/memory/config_path.py`.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `resolve_memory_jsonl_dir()` | Unit: returns the flat-key path under the isolated temp root; equals the builder default for unset input | `uv run pytest tests/agent/memory/` | returns `{root}/memory`; no `KeyError` |

## Completion criteria

- `scripts/agent/memory/config_path.py` (new) exists, exposes `resolve_memory_jsonl_dir() -> str`, and returns the flat `memory_jsonl_dir` value with the builder default.
- The returned path equals `ctx.cfg.memory.memory_jsonl_dir` for the same input config.
- `uv run ruff check` and `uv run mypy` are clean on the new file.

## Out of Scope

- Rerouting the three writers (separate rows).
- Changing the JSONL format or archive filename.
- Extracting a shared default constant into `config_section_builders.py` (would amend the frozen table; see Alternatives).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/agent/memory/config_path.py` (new) with `resolve_memory_jsonl_dir()` (REQ-001) | Completed | 20261020-070158 | 20261020-070158 | Reproduce builder accessor via `_get_str_or_default`; see UNK-01 for default sourcing |
| 2 | Add unit test asserting the resolver returns the flat-key path under the isolated temp root | Completed | 20261020-070158 | 20261020-070158 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-070158 | 20261020-070158 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-070158 | 20261020-070158 | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-205032_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-225902
- **Related target files**: `scripts/agent/memory/config_path.py`