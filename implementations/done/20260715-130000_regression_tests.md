# Implementation Procedure: Add regression coverage for command, config, Memory, and policy cleanup

## Goal

Add regression tests that fail if removed legacy behaviors are reintroduced. Tests cover command metadata/REPL, Memory commands, config keys, tool policy, and Memory core.

## Scope

### Files to modify
- `tests/test_command_registry.py`
- `tests/test_repl.py`
- `tests/test_cmd_memory.py`
- `tests/test_config_memory.py`
- `tests/test_config_reload.py`
- `tests/test_tool_policy.py`
- `tests/test_tool_approval.py`
- `tests/test_memory_status.py`
- `tests/test_memory_retriever.py`

### Out of scope
- Runtime implementation files (except minimal test fixtures if unavoidable)
- Documentation files

## Implementation Steps

### Step 1: Command metadata and REPL tests

#### In `test_command_registry.py`:
1. Test: completion includes all command names from `_COMMANDS`
2. Test: `/exit` appears in completion according to selected design
3. Test: dispatch and help output remain consistent with `_COMMANDS`

#### In `test_repl.py`:
1. Test: Ctrl-C behavior matches selected design
2. Test: Unknown subcommand suggestions work correctly after removing `rebuild` and `import-jsonl`

### Step 2: Memory command tests

#### In `test_cmd_memory.py`:
1. Test: `/memory rebuild` is rejected as unknown subcommand
2. Test: `/memory import-jsonl` is rejected as unknown subcommand
3. Test: `/memory help` does not mention JSONL rebuild
4. Test: `/memory check-consistency` does not mention JSONL
5. Test: `/memory search` requires embedding-backed hybrid retrieval
6. Test: `/memory status` does not show disabled or FTS-only modes

### Step 3: Config tests

#### In `test_config_memory.py`:
1. Test: `use_memory_layer` is rejected by config loader
2. Test: `memory_jsonl_dir` is rejected by config loader
3. Test: `memory_embed_enabled` is rejected by config loader
4. Test: Failed reload does not partially mutate runtime config
5. Test: `ConfigLoadError` includes the original reason

#### In `test_config_reload.py`:
1. Test: GitOps field validation follows selected schema behavior
2. Test: Removed-key validation fires on load

### Step 4: Tool policy tests

#### In `test_tool_policy.py`:
1. Test: GitHub allowlist accepts a listed repository
2. Test: GitHub allowlist rejects an unlisted repository
3. Test: Empty GitHub allowlist denies writes
4. Test: Normalized owner/repo comparison works correctly

#### In `test_tool_approval.py`:
1. Test: `gitops_push_blocked` blocks the intended tools
2. Test: `gitops_force_push_blocked` blocks force push operations
3. Test: `gitops_protected_branches` blocks protected branch operations
4. Test: Denials are auditable (audit decision emitted)

### Step 5: Memory core tests

#### In `test_memory_status.py`:
1. Test: Status never shows `disabled` mode
2. Test: Status never shows `fts-only` mode
3. Test: Status shows correct mode labels: `hybrid`, `degraded`, `unavailable`

#### In `test_memory_retriever.py`:
1. Test: Hybrid retriever does not return FTS-only mode
2. Test: Missing embeddings are reported as degraded or unavailable
3. Test: Vector index unavailability is observable
4. Test: JSONL is not written during ingestion

## Test Design Notes

1. Use mocking where possible — avoid requiring actual LLM/embedding infrastructure
2. Focus on behavioral contracts: what happens when conditions are met, not implementation details
3. Each test should assert one specific contract — no compound assertions
4. Use parametrized tests for allowlist scenarios (empty, single repo, multiple repos)

## Acceptance Criteria Verification

1. Tests fail if removed Memory commands return — verify by temporarily re-adding `rebuild` and `import-jsonl` to dispatch map
2. Tests fail if removed Memory config keys are accepted — verify by temporarily allowing them in config loader
3. Tests fail if FTS-only mode is returned — verify by temporarily restoring FTS-only fallback logic
4. Tests fail if GitHub write policy becomes fail-open — verify by temporarily removing empty allowlist denial
5. Test ownership remains separate from implementation issues — tests only validate behavior, not implementation
