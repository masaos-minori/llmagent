## Goal

Add a commented example of the `consumer_authorization` / `topic_authorization` mapping shape to `config/eventbus.toml` so operators see how the mappings that `load_config()` now carries through (`REQ-001`, `REQ-002`) are structured. Documentation only; no new keys, no secrets.

## Scope

- Modify `config/eventbus.toml` only: append a commented block illustrating both mapping shapes after the per-role token block (lines 25-29) and before the SSE section (line 31).
- Comment-only: introduce no new TOML keys, so parsing and runtime behavior are unchanged.

## Assumptions

- The example is illustrative only; real values come from the environment and real topic/consumer-id strings. No secret values are written.

## Design decisions

- **Comment-only, keyed to the loader.** The example mirrors the exact types `load_config()` produces (`topic_authorization` → `dict[str, set[str]]`, `consumer_authorization` → `dict[str, list[str]]`) so it matches what the code expects, but stays inside a `#` comment so it is never parsed as a key.

## Alternatives considered

- Adding the mappings as active (uncommented) keys: rejected — the shipped file intentionally sets no authorization table (deny-all), and adding active keys would change startup behavior and require values.

## Implementation

### Target file

`config/eventbus.toml`

### Procedure

Insert a commented example block between the per-role token block (ends line 29) and the SSE section comment (line 31):

```toml
# Authorization mappings (optional, documentation example only — not active keys).
# consumer_token above requires consumer_authorization when set. Shape:
#   consumer_authorization = { "<consumer_id>" = [ "<topic>", ... ] }
#   topic_authorization      = { "<topic>" = [ "<consumer_id>", ... ] }
# Example (replace placeholders; do not commit real values):
# consumer_authorization = { "svc-checkout" = [ "orders/*", "inventory/*" ] }
# topic_authorization      = { "orders/*"   = [ "svc-checkout", "svc-frontend" ] }
```

### Details

- The block is entirely comments; TOML never sees these lines, so no key is added and `_KNOWN_CONFIG_KEYS` filtering is unaffected.
- The shapes shown match the normalized types: `topic_authorization` consumers are conceptually a set (order irrelevant), `consumer_authorization` topics are a list.

## Compatibility considerations

- N/A: comment-only addition introduces no new keys and cannot change parsing or runtime behavior.

## Security considerations

- N/A: no secrets, no new keys, no change to the fail-closed load path.

## Rollback considerations

- Revert the commit (single commented block).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/eventbus.toml` | Documentation: file still parses; example block is comment-only; no new keys | `uv run python tools/check_workitem_structure.py --file config/eventbus.toml` (structure) + confirm the file still loads via `load_config()` in the EventBus test suite | no new keys; example present as comments |

## Completion criteria

- The commented example appears after the per-role token block and before the SSE section.
- No new TOML key is introduced; the file remains parseable by `load_config()`.

## Out of Scope

- Documenting the token-uniqueness invariant and missing-vs-empty semantics in ADR-013 — handled by the sibling procedure for `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (`REQ-003`, `REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add commented authorization-mapping example to `config/eventbus.toml` | Completed | 20261025 | 20261025 | Applied 20261026 during verification (was unapplied); comment-only, no new keys |
| 2 | Run documentation checkers (`rules/toolchain.md`) | Completed | 20261026 | 20261026 | `tomllib` parse OK; `load_config()` unchanged; `test_eventbus_config.py`: 38 passed |

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
- **Requirement ID**: supports `REQ-001`, `REQ-002` (illustrates the carried-through mappings)
- **Source issue**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-101136_eventbus002_config-authorization-token-roles.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-140926
- **Related target files**: `config/eventbus.toml`
