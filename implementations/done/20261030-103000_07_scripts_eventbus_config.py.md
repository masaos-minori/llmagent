# Implementation Procedure: config.py outbox retry knobs

## Goal

Add validated outbox retry configuration fields to `scripts/eventbus/config.py` so the retry
policy is config, not hardcoded (REQ-005; plan AC-4).

## Scope

**In scope:**
- Three dataclass fields with `__post_init__` validation: `outbox_max_attempts` (new) (default 5),
  `outbox_backoff_base_seconds` (new) (default 30), `outbox_backoff_max_seconds` (new) (default 900).
- Their entries in `_KNOWN_CONFIG_KEYS` (optional group), `_CONFIG_KEY_TYPES`, and the
  `load_config` construction block.

**Out of scope:**
- Where the values are consumed (row 03), TOML defaults (row 08).

## Assumptions
- Verified at HEAD `124e340b4`: field pattern at `config.py:74-107` (optional fields carry
  dataclass defaults, e.g. `replay_batch_size: int = 1000`); threshold validation in
  `__post_init__` (`max_retry` check at `:115-116`); known-keys tuple at `:224-236`;
  `_CONFIG_KEY_TYPES` at `:232+`; construction from parsed data at `:337+`
  (`max_retry=data["max_retry"]`).
- Defaults 5 / 30s / 900s implement the plan Assumption (bounded attempts, exponential backoff
  clamped); exact numbers stay tunable per UNK-02.

## Design decisions
- Optional keys with dataclass defaults (not required keys): an existing deployed
  `config/eventbus.toml` without the new keys must keep loading unchanged (config-boundary
  rule; mirrors `replay_batch_size`'s pattern).
- Validation rules in `__post_init__`: `outbox_max_attempts >= 1`,
  `outbox_backoff_base_seconds >= 1`, `outbox_backoff_max_seconds >= outbox_backoff_base_seconds`
  — same `ValueError(f"... got {value}")` message style as `max_retry`.
- Type entries `int` in `_CONFIG_KEY_TYPES` so TOML type checking rejects strings/floats at
  load time like every other int key.

## Alternatives considered
- Hardcoding retry policy in `dlq.py`: rejected by the plan (project rule: retry policy is config).

## Implementation
### Target file
`scripts/eventbus/config.py`

### Procedure
1. Append the three fields after `backlog_health_threshold` with a short comment naming the
   outbox.
2. Add the three validation checks in `__post_init__`.
3. Register the keys in `_KNOWN_CONFIG_KEYS`, `_CONFIG_KEY_TYPES`, and pass them through in
   the `EventBusConfig(...)` construction (via the optional-key lookup path the other
   defaulted keys use).

### Method
Additive fields following the existing optional-field pattern end to end.

### Details
- `load_config` supplies missing optional keys with the dataclass default — confirm the
  existing optional-key mechanism (`data.get(key, default)`) rather than duplicating default
  literals; if the current code only forwards present keys, rely on dataclass defaults.

## Compatibility considerations
- Deployed configs untouched keep today's behavior (defaults). `frozen=True` dataclass gains
  fields only — construction sites using keyword arguments (tests) are unaffected.

## Security considerations
- Values are static operator config; no secrets.

## Rollback considerations
- Row 03 references these attributes; revert rows 03/06/07/08 together.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_config.py` — existing suite plus new cases:
  defaults when keys absent; each invalid value class rejected (`attempts=0`, negative base,
  cap < base, wrong types). (test_eventbus_config.py is a disclosed non-target test file,
  plan UNK-04.)

## Completion criteria
- Retry knobs load, validate, and reach `process_outbox` (new) through `cfg`.

## Out of Scope
- TOML shipping defaults (row 08), worker use (row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add fields, validation, key registries | Completed | 20261031-074813 | 20261031-074813 | 3 outbox knobs added with validation |
| 2 | Add config test cases | Completed | 20261031-074813 | 20261031-074813 | Disclosed non-target test file (UNK-04) 7 new tests + deploy tests green (75 passed) |
| 3 | Run `uv run pytest tests/eventbus/test_eventbus_config.py` | Completed | 20261031-074813 | 20261031-074813 | ruff+mypy green |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/config.py`