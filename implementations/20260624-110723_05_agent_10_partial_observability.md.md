# Implementation: Operator Observability for Partial Completion and Truncation

## Goal

Add log-key and metric guidance to 3 agent docs so operators know what to watch for partial completions and context truncations.

## Scope

**In:**
- `docs/05_agent_10_operations_and_deployment.md` — add operator observability section
- `docs/05_agent_15_performance_and_tuning.md` — add truncation metric references
- `docs/05_agent_17_troubleshooting_and_diagnostics.md` — add partial/truncation diagnostic steps

**Out:** No code changes.

## Assumptions

1. Log keys exist: `partial_completion`, `turn_truncated`, `max_turns_reached` (to confirm from code).
2. Metrics: `agent.partial_completions`, `agent.max_turns_reached`, `agent.context_truncations`.
3. References canonical model from plan req 29 (`05_agent_03` §Partial-Completion Model).

## Implementation

### Target file

`docs/05_agent_10_operations_and_deployment.md`, `docs/05_agent_15_performance_and_tuning.md`, `docs/05_agent_17_troubleshooting_and_diagnostics.md`

### Procedure

1. Confirm log keys:
   ```bash
   grep -rn "partial_completion\|turn_truncated\|max_turns_reached" agent/ --include="*.py" | head -10
   ```
2. Add operator observability table to `05_agent_10`.
3. Add truncation metric section to `05_agent_15`.
4. Add partial/truncation diagnostic steps to `05_agent_17`.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Observability table for `05_agent_10`:**

```markdown
## Partial Completion and Truncation Monitoring

| Condition | Log Key | Level | Metric |
|---|---|---|---|
| Partial completion (SIGTERM) | `partial_completion trigger=sigterm` | WARNING | `agent.partial_completions` |
| Max turns exhausted | `max_turns_reached turns=N` | WARNING | `agent.max_turns_reached` |
| Context window truncated | `turn_truncated tokens_before=N tokens_after=M` | INFO | `agent.context_truncations` |
| Tool sequence interrupted | `tool_sequence_interrupted tool=X at=N` | WARNING | — |

For the partial-completion state model, see `05_agent_03` §Partial-Completion Model.
```

**Truncation section for `05_agent_15`:**
```markdown
## Context Truncation Metrics

Monitor `agent.context_truncations` to detect when context is being compressed.
High truncation rate with `use_rrf = true` may indicate excessive reranking context.
Tune `compression_threshold` (default 80%) to reduce truncation frequency.
```

**Diagnostic steps for `05_agent_17`:**
```markdown
### Diagnosing Partial Completions

1. Search agent logs: `grep "partial_completion" agent.log`
2. Note the `trigger` field: `sigterm` | `max_turns` | `llm_refusal` | `tool_error`
3. For `sigterm`: check process manager / systemd logs for unexpected shutdown.
4. For `max_turns`: increase `max_turns` in `agent.toml` or review turn efficiency.
5. For `llm_refusal`: check LLM logs for safety filter triggers.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Observability table | `grep -n "partial_completion.*trigger\|Partial Completion.*Monitor" docs/05_agent_10_operations_and_deployment.md` | found |
| Truncation metrics | `grep -n "context_truncations\|truncation.*metric" docs/05_agent_15_performance_and_tuning.md` | found |
| No code changes | `git diff agent/` | empty |
