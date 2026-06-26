# Implementation: agent docs — current behavior vs discrepancy annotation

Source plan: `plans/20260626-180407_plan.md`

---

## Goal

Add "Current behavior" and "Known discrepancy" sections to five agent docs, mark unresolved design points as `Needs confirmation`, and ensure each doc accurately describes today's implementation rather than mixing current state with future design.

---

## Scope

**In-Scope**
- `docs/05_agent_04_state-and-persistence.md`
- `docs/05_agent_09_data-layer.md`
- `docs/05_agent_08_configuration.md`
- `docs/05_agent_10_operations-and-observability.md`
- `docs/05_agent_12_memory.md`

**Out-of-Scope**
- Runtime behavior changes
- Renumbering or restructuring docs
- Describing fixes from issues 01–06 as already implemented

---

## Assumptions

1. "Current behavior" = what the code does today (verified by reading source).
2. "Known discrepancy" = difference between docs and code, or between two doc sections.
3. "Needs confirmation" = design decision not yet made (e.g., compressed history persistence model).
4. All doc edits are additive (new sections/callouts) — existing text is corrected, not deleted wholesale.

---

## Implementation

### Target files (read all before editing)
- `docs/05_agent_04_state-and-persistence.md`
- `docs/05_agent_09_data-layer.md`
- `docs/05_agent_08_configuration.md`
- `docs/05_agent_10_operations-and-observability.md`
- `docs/05_agent_12_memory.md`

### Procedure
1. Read each file.
2. Identify conflicting language via grep: `grep -n "memory_jsonl_path\|role.*diagnostic\|compressed.*session\|workflow.*required" docs/05_agent_*.md`
3. Apply per-doc corrections below.

### Details

**`05_agent_04_state-and-persistence.md`** additions:
```markdown
> **Current behavior:** Compressed history lives in memory only. The `messages` table retains all original messages. On `/session load`, the full uncompressed message set is restored.
> **Known discrepancy:** In-memory compressed history diverges from DB state after compression fires.
> **Needs confirmation:** Canonical persistence model for compressed history (pending implementation plan 20260626-180401).
```

**`05_agent_09_data-layer.md`** corrections:
- Remove or annotate any `role="diagnostic"` language in `messages` table description.
- Add: "Diagnostic records (transport errors, partial completions, loop guard hints, serialization events) are stored in `session_diagnostics`, not in `messages`. Session restore excludes diagnostics."

**`05_agent_08_configuration.md`** corrections:
- Replace `memory_jsonl_path` → `memory_jsonl_dir` throughout.
- Add note: "Production default `workflow_mode = required` means the agent fails at startup if `config/workflows/default.json` is absent. Local/test default is `auto`. Ensure the workflow definition is deployed before starting in production."

**`05_agent_10_operations-and-observability.md`** additions:
```markdown
## Startup validation checklist

When `workflow_mode = required`:
1. Confirm `config/workflows/default.json` exists and is valid JSON.
2. Run `python -c "from agent.workflow.workflow_loader import WorkflowLoader; WorkflowLoader().load()"` to pre-validate before service start.
3. If the file is missing, the agent will raise RuntimeError at startup with the expected file path.
```

**`05_agent_12_memory.md`** additions:
- Under `branch` field description: "The `branch` field is used as an active scoring boost (+0.15) during retrieval when the query context includes a branch. Global memories (empty `branch`) are not excluded — they receive no branch boost."
- Under JSONL config: "Configured via `memory_jsonl_dir` (directory path). The runtime file path is `{memory_jsonl_dir}/memories.jsonl`."

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Grep check | `grep -rn "memory_jsonl_path" docs/` | 0 hits |
| Grep check | `grep -rn "role.*diagnostic" docs/05_agent_0[34]*.md` | 0 hits (or only in code blocks showing old behavior) |
| Manual review | Read each changed section | No contradictions |
