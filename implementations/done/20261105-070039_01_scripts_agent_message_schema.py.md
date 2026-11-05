## Goal

Add the public `unexpected_message_keys` (new) helper to `scripts/agent/message_schema.py`
(REQ-001; AC-1): return the keys of a message that are neither in the role's
`ROLE_KEY_WHITELIST` entry nor an authorized ephemeral key, falling back to
`{"role", "content"}` for an unknown role, derived from `ROLE_KEY_WHITELIST` and
`TRUSTED_SOURCES` with no duplicated key lists. Keep `validate_message` untouched.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `ROLE_KEY_WHITELIST` (role → allowed keys) and `TRUSTED_SOURCES` (source → ephemeral
  keys) are module-level constants in `scripts/agent/message_schema.py`;
  `_ALL_EPHEMERAL_KEYS` is the private `frozenset` derived from `TRUSTED_SOURCES`
  (line 26), so the helper can read it directly without importing a private name from
  another module or duplicating the union derivation.
- History messages carry only `_ephemeral` / `_memory_injected` as ephemeral keys
  (`scripts/shared/types.py` `LLMMessage`); `source` is validation-only metadata kept
  out of stored messages (`scripts/agent/context.py` `append_message`), so the helper
  needs no `source` allowance.
- The helper reads `ROLE_KEY_WHITELIST.get(role, {"role", "content"})`, matching
  `context.py` `_sanitize_message`'s fallback for an unknown role, so the two agree on
  what is allowed.
- Row 03 (`session_persister.py`) imports this helper; the import target is the public
  name declared here.

## Design decisions

- Return `set(msg.keys()) - allowed`, where `allowed = ROLE_KEY_WHITELIST[role] ∪
  _ALL_EPHEMERAL_KEYS` (or `{"role", "content"} ∪ _ALL_EPHEMERAL_KEYS` for an unknown
  role). This derives every allowed set from the schema constants, so it cannot drift
  from `validate_message` or `_sanitize_message` (Risk: helper/`validate_message`
  drift).
- Type the parameter as `dict` to match `validate_message`'s existing signature;
  no `LLMMessage` import needed. The persister's history items are `LLMMessage` (a
  TypedDict; `context.py` `ConversationState.history` is `list[LLMMessage]`), so the
  call site wraps with `dict(m)` and the role lookup uses `msg.get("role") or ""` to
  satisfy mypy (a possibly-`None` key is not assignable to the `str` key type of
  `ROLE_KEY_WHITELIST`). These are the only two deviations from the Procedure code
  block below, both forced by the type checker; the behaviour is identical to the
  stated design.

## Alternatives considered

- Whitelist-only (no ephemeral allowance): rejected; stored `_ephemeral` /
  `_memory_injected` system messages would still log a WARNING with full content at
  session end (Plan Decision 1(a)).
- Reuse `validate_message`: rejected; it requires a trusted `source` for ephemeral keys,
  which history messages lack, so it would reject legitimate stored ephemeral messages
  (Plan Point 4).

## Implementation
### Target file
`scripts/agent/message_schema.py`

### Procedure
Add one public function after `get_allowed_ephemeral_keys` (end of module):
1. `unexpected_message_keys(msg)` (new)

### Method
- Insert, after `get_allowed_ephemeral_keys` (the last function in the module):
  ```python
  def unexpected_message_keys(msg: dict) -> set[str]:
      """Return the keys of *msg* outside the role's allowed keys and the authorized ephemeral keys.

      Uses ROLE_KEY_WHITELIST for the role (falling back to {'role', 'content'} for an
      unknown role) plus the ephemeral keys authorized in TRUSTED_SOURCES, so the result
      never duplicates a key list and stays in sync with validate_message.
      """
      allowed = set(ROLE_KEY_WHITELIST.get(msg.get("role") or "", {"role", "content"}))
      allowed.update(_ALL_EPHEMERAL_KEYS)
      return set(msg.keys()) - allowed
  ```
- The function reads the two module-level constants already defined above it; no new
  import and no change to any existing symbol.

### Details
- `AC-1` cases the helper must satisfy: empty set for user, assistant-with-`tool_calls`,
  tool-with-`tool_call_id`+`name`, system, and messages carrying only authorized
  ephemeral keys; the offending key name otherwise; unknown role falls back to
  `{"role", "content"}`.
- `_ALL_EPHEMERAL_KEYS` is `_`-prefixed and therefore excluded from the generated
  reference document; only the new public `unexpected_message_keys` (new) appears there.
- Stale-reference marks: `unexpected_message_keys` (new) is created here; the constants
  it reads (`ROLE_KEY_WHITELIST`, `_ALL_EPHEMERAL_KEYS`) already exist. the constants it reads already exist.

## Compatibility considerations

- Purely additive: no existing symbol, constant, or `validate_message` behavior changes,
  so no consumer scan is required beyond the generated reference document (Row 05).
- The new public function is listed by `generate_reference_table.py --type agent` once
  the source is regenerated.

## Security considerations

- The helper removes message content from the warning path (Row 03 logs only role + key
  names), reducing the data-exposure risk of logging whole history messages. It exposes
  no new data by itself; it returns only key names, never values.

## Rollback considerations

- Revert the added function.

## Validation plan

- `uv run pytest tests/agent/test_message_schema.py -v` — the new helper tests pass.
- Static: `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/`.
- Confirm `vulture` reports no finding in `scripts/agent/message_schema.py`.

## Completion criteria

- `unexpected_message_keys` (new) returns an empty set for every message shape the schema
  allows and the offending key names otherwise; the allowed sets come from
  `ROLE_KEY_WHITELIST` and `TRUSTED_SOURCES`; `validate_message` is unchanged.
- The new helper test passes; static checks are clean; `vulture` finds nothing.

## Out of Scope

- The persister call site (`scripts/agent/session_persister.py`, Row 03).
- The persister tests (Row 03) and helper tests (Row 04).
- Regenerating the reference document (Row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `unexpected_message_keys` (new) helper per Procedure | Completed | 20261105-104354 | 20261105-104354 | Applied; mypy forced msg.get("role") or "" in schema and dict(m) wrapper at persister call site (history items are LLMMessage TypedDict) |
| 2 | Add helper unit tests per Validation plan (Row 04) | Completed | 20261105-104354 | 20261105-104354 | covered by Row 04 doc |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-104354 | 20261105-104354 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-104354 | 20261105-104354 | referenced by Row 05 |

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
- **Requirement ID**: `REQ-001` (public helper returning off-whitelist keys), `AC-1`
- **Source issue**: issues/done/20261031-180407_memlogleak001_memory-persist-logs-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114342_memlogleak001_memory-persist-logs-messages.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-070039
- **Related target files**: scripts/agent/message_schema.py
