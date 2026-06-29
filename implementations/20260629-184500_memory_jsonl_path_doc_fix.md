# Implementation: memory_jsonl_path → memory_jsonl_dir doc correction

## Goal

Replace the stale `memory_jsonl_path` reference in `docs/05_agent_12_memory.md` with the correct `memory_jsonl_dir` config key, clarifying that the full JSONL path is `{memory_jsonl_dir}/memories.jsonl`.

## Scope

- **In-Scope**:
  - Replace `memory_jsonl_path` with `memory_jsonl_dir` in `docs/05_agent_12_memory.md` JSONL Format section (line 222)
  - Add one-line note clarifying the full path is `{memory_jsonl_dir}/memories.jsonl`
  - Verify no other stale occurrences remain in `docs/`

- **Out-of-Scope**:
  - Any code changes (runtime already uses `memory_jsonl_dir`)
  - Config file changes (already use `memory_jsonl_dir`)
  - Test additions

## Assumptions

- The canonical model is **directory-based**: `memory_jsonl_dir` holds the directory; the filename `memories.jsonl` is hardcoded in `agent/factory.py:286`
- No backward-compat alias for `memory_jsonl_path` is needed because the key never existed in any config file or public API

## Implementation Steps

1. **Phase 1: Preparation**
   - [ ] Confirm exact line containing `memory_jsonl_path`: `grep -n "memory_jsonl_path" docs/05_agent_12_memory.md` → line 222

2. **Phase 2: Core Doc Update**
   - [ ] In `docs/05_agent_12_memory.md`, JSONL Format section, replace:
     ```
     - File path controlled by `memory_jsonl_path` config
     ```
     with:
     ```
     - File path is `{memory_jsonl_dir}/memories.jsonl`; `memory_jsonl_dir` is set in `config/memory.toml` (default: `/opt/llm/memory`)
     ```

3. **Phase 3: Verification**
   - [ ] Run `grep -rn "memory_jsonl_path" docs/` — must return 0 hits
   - [ ] Run `grep -n "memory_jsonl" docs/05_agent_12_memory.md` — must show only `memory_jsonl_dir` occurrences

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_12_memory.md` | Grep check | `grep -rn "memory_jsonl_path" docs/` | 0 hits |
| `docs/05_agent_12_memory.md` | Grep check | `grep -n "memory_jsonl" docs/05_agent_12_memory.md` | Only `memory_jsonl_dir` matches |

## Risks & Mitigations

- **Risk**: Other archived docs (`implementations/done/`, `plans/done/`) contain `memory_jsonl_path` → **Mitigation**: These are historical artifacts, not operator-facing; no update needed. The grep scope for the verification step is `docs/` only.
