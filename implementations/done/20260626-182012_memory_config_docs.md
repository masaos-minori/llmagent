# Implementation: memory JSONL config docs correction

Source plan: `plans/20260626-180405_plan.md` — Phase 2

---

## Goal

Replace any `memory_jsonl_path` references in docs with the correct `memory_jsonl_dir`, and add a clear explanation that the full JSONL file path is `{memory_jsonl_dir}/memories.jsonl`.

---

## Scope

**In-Scope**
- `docs/05_agent_08_configuration.md`: replace `memory_jsonl_path` → `memory_jsonl_dir`; add path construction note
- `docs/05_agent_12_memory.md`: same correction; document JSONL dir ownership

**Out-of-Scope**
- Code changes (all code already uses `memory_jsonl_dir`)
- Adding backward compat alias

---

## Assumptions

1. `memory_jsonl_dir` is the only correct key (confirmed: config_dataclasses.py:299, config_builders.py:204, factory.py:285).
2. Full path = `{memory_jsonl_dir}/memories.jsonl` (confirmed: factory.py:285).
3. No operator-facing config currently uses `memory_jsonl_path`; no migration needed.

---

## Implementation

### Target files
- `docs/05_agent_08_configuration.md`
- `docs/05_agent_12_memory.md`

### Procedure
1. Read both docs.
2. Run `grep -n "memory_jsonl" docs/05_agent_08_configuration.md docs/05_agent_12_memory.md` to find all occurrences.
3. Replace `memory_jsonl_path` → `memory_jsonl_dir` throughout.
4. Add documentation note about path construction.

### Details

**Standard replacement note to add near `memory_jsonl_dir` description:**

> `memory_jsonl_dir` — directory path for the memory JSONL archive. The actual file path used at runtime is `{memory_jsonl_dir}/memories.jsonl`. The config key sets the directory; the filename is fixed.
>
> Example: `memory_jsonl_dir = "/opt/llm/memory"` → runtime path `/opt/llm/memory/memories.jsonl`

**In `05_agent_08_configuration.md`:**
- Locate `memory_jsonl_path` (if present) and replace with `memory_jsonl_dir`.
- Locate `memory_jsonl_dir` entry and append path construction note.

**In `05_agent_12_memory.md`:**
- Locate any JSONL path description and ensure it says `memory_jsonl_dir`.
- Add: "The directory is set via `memory_jsonl_dir`; do not configure a full file path — only the directory is accepted."

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Grep check | `grep -rn "memory_jsonl_path" docs/` | 0 hits after fix |
| Read check | Re-read changed sections | Consistent with factory.py:285 |
