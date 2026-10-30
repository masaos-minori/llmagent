# Implementation Procedure: `scripts/eventbus/config.py` (EBAUTHGEN001 Phase 1)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-001, REQ-005; Design `:167`, `:171`)

## Goal
Add the authorization baseline-hash helper and the TTL bounds configuration fields to
the frozen `EventBusConfig`.

## Scope
- `EventBusConfig` frozen dataclass `:71-109`; `consumer_authorization` `:99-101`,
  `topic_authorization` `:102` (values `set[str]`).
- `__post_init__` `:111-188` (per-key + cross-field validation pattern).
- `_KNOWN_CONFIG_KEYS` `:191-216`; `_REQUIRED_CONFIG_KEYS` `:219-228`;
  `_CONFIG_KEY_TYPES` `:232-253`; `load_config` builds the dataclass `:333-356` and
  rejects unknown keys `:288-293`.

## Assumptions
- Recorded open items (Needs Confirmation):
  - `authz_max_ttl_seconds: int = 86400` (new) — UNK-01 plan default (Needs Confirmation
  - `authz_sweep_interval_seconds: float = 60.0` (new) — UNK-02 plan default (Needs
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `authorization_baseline_hash(config) -> str` (new): SHA-256 hex over the canonical
  union of `(consumer_id, topic)` pairs derived from both mappings, canonically sorted
  (plan Risk `:207`: permutation-invariant; test asserts equality across orderings).
  Covers only authorization pair sets, never the whole config (Assumption `:140`).
- TTL bounds fields (optional keys with defaults):
  - `authz_max_ttl_seconds: int = 86400` (new) — UNK-01 plan default (Needs Confirmation
    before production enablement).
  - `authz_sweep_interval_seconds: float = 60.0` (new) — UNK-02 plan default (Needs
    Confirmation).
  Key names are proposals consistent with existing unprefixed keys (`sse_heartbeat_interval`);
  Needs Confirmation.
- Validation in `__post_init__`: `authz_max_ttl_seconds >= 1`,
  `authz_sweep_interval_seconds >= 1.0` — same ValueError style as existing checks.
- Add both keys to `_KNOWN_CONFIG_KEYS` and `_CONFIG_KEY_TYPES` (`int` / `float`); NOT to
  `_REQUIRED_CONFIG_KEYS`; wire through `load_config` with `data.get(...)` defaults.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add the two fields after `backlog_health_threshold` (`:109`).
2. Add the two validation clauses in `__post_init__` after the `publish_rate` check (`:140-141`).
3. Add helper `authorization_baseline_hash` at module level (after `_validate_deployment_mode` `:60-68`).
4. Extend `_KNOWN_CONFIG_KEYS` `:191-216`, `_CONFIG_KEY_TYPES` `:232-253`, and the
   `EventBusConfig(...)` construction in `load_config` `:333-356`.

## Compatibility considerations
**Dependencies**:
- Upstream: none (same Phase 1 commit group as doc 01)
**Blocks**: `scripts/eventbus/auth.py` baseline hash use (doc 01), TTL bounds consumers

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py` (baseline-hash
  permutation-invariance, TTL bounds validation rejection).
- Existing config regression: `uv run pytest tests/eventbus/test_eventbus_config.py`.

## Completion criteria
- Unknown-key rejection still holds for anything outside the extended known set;
  baseline hash stable across pair-set permutations; defaults match UNK-01/UNK-02 plan
  values.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | `authz_max_ttl_seconds: int = 86400` (new) — UNK-01 plan default (Needs Confirmation | No | — |
| 2 | `authz_sweep_interval_seconds: float = 60.0` (new) — UNK-02 plan default (Needs | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `authorization_baseline_hash`, `authz_max_ttl_seconds`,
  `authz_sweep_interval_seconds` (all in "Contract after change").

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 02
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/config.py`
