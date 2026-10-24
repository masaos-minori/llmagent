## Goal

Restate the turn-lifecycle overview so it shows turn-entry preparation (memory injection, mode
classification, user-message append, history compression) as a once-per-turn step that runs **before**
the workflow engine, and the `execute` stage as the per-attempt LLM/tool execution that a retry
re-runs — removing the now-false claim that these effects live inside the `execute` stage
(`REQ-009`, `AC-9`).

## Scope

- Two passages only in `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`:
  - the turn-lifecycle sequence diagram annotations (`:47`, `:61`, `:83`);
  - the `### MDQ/RAG Mode Classification` passage (`:106`).
- The rest of the overview and the delegation at `:83` to `agent_03_03` stay as written.

## Assumptions

- The reader infers from the Plan which effects move out of the `execute` stage; this document only
  restates the resulting boundary in these two passages.
- Wording must stay consistent with `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
  (Row 4), which restates the same boundary in the stage table.

## Design decisions

- Relabel steps ②③④ in the diagram as the once-per-turn entry step that runs before
  `WorkflowEngine.run()`, and label step ⑤ (LLM Turn Processing) as the `execute` stage — per-attempt,
  retried per the policy.
- Rewrite the MDQ/RAG passage so `classify_and_inject_mode()` is described as part of the
  once-per-turn entry step, not the `execute` stage.

## Alternatives considered

- N/A: documentation-only wording change.

## Implementation

### Target file

`docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

### Procedure

1. Turn-lifecycle sequence — change the annotation on step ② (`:47`) from
   `[Within WorkflowEngine's execute stage]` to mark it as the once-per-turn entry step before the
   engine; add an annotation to step ⑤ (`:61`) identifying it as the `execute` stage (per-attempt,
   retried per policy).
2. Implementation note (`:83`) — correct the claim that all of steps ①–⑥ run as stage callbacks.
3. `### MDQ/RAG Mode Classification` (`:106`) — rewrite the first bullet so `classify_and_inject_mode()`
   is part of the once-per-turn entry step, not the `execute` stage.

### Method

#### Sequence diagram

Step ② (`:47`) before:

```
         ② Memory Injection and Mode Classification          [Within WorkflowEngine's execute stage]
```

After — it is now the once-per-turn entry step, before the engine runs:

```
         ② Memory Injection and Mode Classification          [Once-per-turn entry step, before WorkflowEngine.run()]
```

Step ⑤ (`:61`) before:

```
          ⑤ LLM Turn Processing
```

After — this is the `execute` stage, the only step that is retried per the policy:

```
          ⑤ LLM Turn Processing                    [WorkflowEngine's execute stage — per-attempt, retried per policy]
```

Implementation note (`:83`) before:

```
A workflow definition load failure makes `Orchestrator` construction fail, so `handle_turn()` always
has a definition. Steps ①–⑥ run as the `plan`/`execute`/`verify` stage callbacks; `plan_fn` is
intentionally a no-op. For stage composition, see [agent_03_03_turn-processing-flow-workflow-engine.md](agent_03_03_turn-processing-flow-workflow-engine.md).
```

After — steps ②③④ are the once-per-turn entry step, not stage callbacks:

```
A workflow definition load failure makes `Orchestrator` construction fail, so `handle_turn()` always
has a definition. Steps ②③④ are the once-per-turn entry step and run before the engine; step ⑤ is the
`execute` stage callback (per-attempt, retried per the policy); `plan_fn` and `verify_fn` cover turn
start and end. For stage composition, see [agent_03_03_turn-processing-flow-workflow-engine.md](agent_03_03_turn-processing-flow-workflow-engine.md).
```

#### MDQ/RAG Mode Classification (`:106`)

Before:

```
- `classify_and_inject_mode()` runs in the same `execute` stage as memory injection, before user message addition.
```

After:

```
- `classify_and_inject_mode()` runs in the once-per-turn entry step (with memory injection), before the user message is added and before the engine runs.
```

### Details

- Do not alter the diagram's flow or any other section; only the three annotations/bullets above.
- Wording must stay consistent with `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
  (Row 4), which states the same boundary in the stage table and Retry Mechanism.

## Compatibility considerations

- N/A: documentation-only wording change.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

Both must report no finding (`AC-9`).

## Completion criteria

- The overview labels steps ②③④ as the once-per-turn entry step before the engine and step ⑤ as the
  `execute` stage; the MDQ/RAG passage no longer places `classify_and_inject_mode()` in the `execute`
  stage; both docs checkers report no finding (`AC-9`).

## Out of Scope

- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` — Row 4.
- Any other chapter; `grep` found no other claim that entry effects run inside the `execute` stage.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | relabel :47/:61, fix :83, rewrite :106 |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs checkers below |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this file |

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
- **Requirement ID**: `REQ-009` (the two agent turn-processing chapters describe the new once-per-turn / per-attempt boundary)
- **Source issue**: issues/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-102728_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-083059
- **Related target files**: docs/23_agent/agent_03_01_turn-processing-flow-overview.md
