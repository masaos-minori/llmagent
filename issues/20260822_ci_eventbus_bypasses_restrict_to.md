# Known Issue: ADR-002 Decision #9 — EventBus bypasses ConfigLoader.restrict_to()

## Metadata

- **ID**: CI-001
- **Status**: Open
- **Severity**: Medium
- **Area**: Config isolation / EventBus
- **Related ADR**: ADR-002 (Config Isolation)
- **Created**: 2026-08-22

## Conflicting Source

- **ADR text**: Decision #9 — "すべてのプロセスはConfigLoader.restrict_to()経由でのみ設定を読み込む"
- **Expected design**: All processes MUST load config through ConfigLoader.restrict_to() to enforce process-level config ownership boundaries
- **Observed implementation**: EventBus broker.py loads its own config via tomllib directly, bypassing ConfigLoader.restrict_to() entirely

## Expected Design

ADR-002 Decision #9 specifies that every process must use ConfigLoader.restrict_to() before loading configuration. This ensures:
1. Process-level config ownership boundaries are enforced
2. Unauthorized config access across process boundaries is prevented
3. Config validation and schema checking apply uniformly

## Observed Implementation

In `scripts/eventbus/broker.py`, the EventBus loads its configuration using tomllib directly:

```python
with open(config_path, 'rb') as f:
    data = tomllib.load(f)
```

This bypasses ConfigLoader.restrict_to() which would:
- Validate the config file against the process's declared scope
- Prevent reading configs belonging to other processes
- Apply consistent validation rules

The same pattern appears in multiple RAG pipeline modules that call ConfigLoader().load_all() without restrict_to().

Additionally, `scripts/db/config.py` calls ConfigLoader().load("agent.toml") WITHOUT calling restrict_to() first.

## Impact

- Config isolation invariant violated for EventBus
- EventBus could potentially read/write configs belonging to other processes
- No validation of config scope boundaries for EventBus
- Inconsistent with the design principle that all processes must go through ConfigLoader

## Recommended Action

1. Replace tomllib direct loading in EventBus broker.py with ConfigLoader.restrict_to() call
2. Audit all other processes that bypass ConfigLoader.restrict_to()
3. Add integration test verifying config isolation between processes
4. Update ADR-002 Known Deviations section if this gap persists

## Owner

Agent team

## Resolution Target

Before ADR-002 moves from Proposed to Accepted status
