Refactor the current Python codebase according to the following high-priority plan.

Follow these instructions strictly.

## Overall goals
- Remove all backward-compatibility layers.
- Standardize on the current structured APIs only.
- Do not preserve legacy flat access.
- Simplify the LLM execution flow by removing duplicated error handling.
- Delete obsolete or compatibility-only modules.
- Split persistence logic by domain.

## Required API rules
- Use only:
  - `cfg.llm`, `cfg.rag`, `cfg.tool`, `cfg.memory`, `cfg.mcp`, `cfg.approval`, `cfg.obs`
  - `ctx.conv`, `ctx.turn`, `ctx.stats`, `ctx.services`, `ctx.cfg`, `ctx.session`
- Do not keep any flat compatibility access such as `cfg.llm_url` or legacy flat attributes on `AgentContext`.

## File-specific instructions

### config.py
- Remove the backward-compatibility flat field access layer.
- Do not preserve `__getattr__` / `__setattr__` compatibility for flat config fields.
- Allow only nested structured config access.
- Split `AgentConfig` and `DbConfig` into separate modules.

### context.py
- Remove backward-compatible flat attribute access.
- Keep `ConversationState`, `TurnState`, `RuntimeStats`, and `AppServices` as the only valid structure.
- Require all callers to use `ctx.conv`, `ctx.turn`, `ctx.stats`, and `ctx.services`.
- Do not preserve any legacy shortcut attributes on `AgentContext`.

### orchestrator.py
- Eliminate duplicated LLM transport error handling.
- Keep `Orchestrator` focused on turn-boundary coordination only:
  - turn start
  - turn end
  - audit logging
  - memory injection
  - history compression
  - appending the user message
- Move inner LLM-loop-specific failure behavior out of this layer.
- Replace `TurnResult` with a dataclass or another explicit typed result object.

### llm_turn_runner.py
- Remove the dynamic import of `ErrorInjectionService`.
- Inject it explicitly through the constructor or another clear dependency path.
- Unify LLM failure handling with `orchestrator.py`.
- Define one consistent policy for:
  - partial completions
  - mid-turn transport failures
  - synthetic tool-error injection

### session.py
- Split the repositories into separate files.
- Move session/message persistence, note persistence, and document persistence into separate modules.
- Reduce the scope of `AgentSession`.
- Do not keep one broad facade for sessions, messages, notes, and documents.
- Clarify database boundaries for document operations.

### factory.py
- Move dependency wiring closer to its final form.
- Build more of the runtime graph in the factory layer.
- Remove the global `_audit_logger_instance`.
- Construct loggers from runtime configuration inside the assembly flow.

### repl_health.py
- Remove outdated `agent.toml` wording.
- Update terminology to match the current structured configuration model.

### cli_view.py
- Fix the mismatch between generic progress methods and RAG-specific output.
- Either make progress rendering generic or rename it to reflect a truly RAG-specific responsibility.
- Do not keep generic method names with hardcoded `[rag]` output.

### repl_debug.py
- Delete this file.
- It is only a split-notice compatibility stub.

### context_detection.py
- Delete this file unless you find a confirmed live execution path that still depends on it.
- Treat it as obsolete two-stage-fetch logic by default.

### rag_debug.py
- Delete this file as well if it is not connected to the current debug flow.

## Backward-compatibility removals
Remove all features that exist only for backward compatibility, including:
- flat config compatibility in `config.py`
- flat runtime-context compatibility in `context.py`
- the compatibility stub in `repl_debug.py`
- the obsolete two-stage context helper in `context_detection.py`
- old RAG debug helpers if they are no longer used

## Priority order
Execute the work in this order:

1. Remove compatibility access from `config.py`.
2. Remove compatibility access from `context.py`.
3. Unify LLM error handling across `orchestrator.py` and `llm_turn_runner.py`.
4. Split repositories in `session.py`.
5. Delete `repl_debug.py` and `context_detection.py`.
6. Delete `rag_debug.py` if unused.

## Implementation constraints
- Make incremental changes.
- Keep behavior changes intentional and explicit.
- If a behavior-affecting change is unavoidable, explain it clearly.
- Prefer structural simplification over compatibility preservation.
- Do not keep dead code for historical reasons.

## Output requirements
For each modified file, report:
- what changed
- why it changed
- which backward-compatibility layer or obsolete feature was removed
- any behavior change or migration note
