# Implementation Procedure: scripts/shared/http_transport.py

## Goal

Replace the random-UUID idempotency-key fallback in `HttpTransport.call` with a
deterministic derived key so an identical logical call re-derives the same key across
retries, processes, and restarts (REQ-001 deterministic key derivation; REQ-010 preserved
caller-supplied-key behavior).

## Scope

**In scope:**
- `scripts/shared/http_transport.py`: add a module-level `derive_idempotency_key` (new) (new)
  function and use it at the fallback site `idempotency_key = str(uuid.uuid4())`
  (`:173`, inside `call` at `:163`).

**Out of scope:**
- Durable dedup store (row 02), dispatcher policy (row 04).

## Assumptions

- Needs Confirmation: the plan text (REQ-001) names build_auth_context (no such
  function exists at HEAD; verified grep) as the fallback
  site; no such function exists in this module. The verified site is `HttpTransport.call`
  at `:173` (comment `:171-172`, key line `:173`). This document proceeds on the verified
  site.
- Needs Confirmation: the plan cites the house key pattern `^[A-Za-z0-9_-]{1,64}$` at
  `scripts/shared/auth_base.py:315`; that file does not exist at HEAD and the pattern is
  not found in `scripts/`. The key shape constraint is kept as a design rule (SHA-256 hex,
  64 chars) but the pattern anchor must be confirmed against the receiving validator
  during implementation.
- Per UNK-01 (resolved by the plan at Phase 2): hash inputs are fixed as
  `method + tool_name + canonical-JSON(args) + uid`. `method` is the transport's fixed
  RPC name (`"call_tool"`); `uid` is derived from the transport's own identity
  (`_session_id`, falling back to the auth token hash when absent) — Needs Confirmation
  of the final uid source (the plan leaves per-user dedup open at UNK-01).

## Design decisions

- Extract derivation into `derive_idempotency_key` (new) (new):
  `sha256(f"{method}\n{tool_name}\n{canonical_json(args)}\n{uid}").hexdigest()` —
  canonical JSON via `json.dumps(args, sort_keys=True, separators=(",", ":"))` so equal
  args always hash equal; hex digest fits `[A-Za-z0-9_-]{1,64}`.
- The derived key is still generated once per logical call and reused across the retry
  loop (existing REQ-005 comment at `:171-172` and the retry-loop comment `:183-188` stay
  valid); only the value source changes.
- `uuid` import removal: drop `uuid` only if no other use remains in the module.

## Alternatives considered

- Hashing inside the retry loop per HTTP attempt — rejected: keys must be invariant
  across attempts of one logical call (existing contract).
- Reusing `uuid5` with a namespace — rejected: does not bind args + uid, so content
  changes would silently reuse a key.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
1. Add `derive_idempotency_key` (new) (new) module-level function next to the other helpers.
2. Replace the `str(uuid.uuid4())` fallback at `:173` with
   `derive_idempotency_key("call_tool", name, args, uid)` where `uid` is taken per the
   Assumptions bullet.
3. Update the `:171-172` comment to state deterministic derivation + same-key retry reuse.

### Method
Pure function; no signature change to `call`, no config change, no new imports beyond
`hashlib`/`json` (already imported per module header `:10`).

### Details
- Same input → same key across processes (REQ-010 cross-process determinism).
- Different args with the same tool → different key (dispatcher's
  `idempotency_key_reused` rejection path in `scripts/mcp_servers/dispatch.py` must stay
  unreachable for honest clients).

## Compatibility considerations

- Keys seen by MCP servers change shape (UUID4 → 64-hex); UNK-03 (servers that log or
  compare keys internally) is closed by the plan's Phase 2 per-server grep, not by this
  change. Keys are opaque passthrough today.
- Tests asserting UUID4 shape must be adapted (rows 15, 16).

## Security considerations

- Key is a content hash, not a secret; do not log full `args` — log `name` and the key
  only, as today.

## Rollback considerations

- Revert the commit: fallback returns to UUID4; the durable store degrades to
  never-matching keys (no false completed-hits), so partial rollforward is safe.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor_routing.py`
  (rows 15, 16 carry the new/updated assertions, written test-first).
- `uv run mypy --no-namespace-packages scripts/ tests/shared`; `lint-imports` (shared-layer
  module, no new cross-layer imports).

## Completion criteria

- Two transports in separate processes derive byte-identical keys for identical
  (tool_name, args, uid); the key matches `^[A-Za-z0-9_-]{1,64}$`; retry attempts within
  one `call` reuse one key; the full targeted suite passes.

## Out of Scope

- Dispatcher-side dedup store and replay policy (rows 02-04).
- Per-server key auditing (plan Phase 2 step, not a file row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `derive_idempotency_key` (new) + fallback-site swap | Pending | — | — | |
| 2 | Land row 15/16 test updates (test-first) before or with this row | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update `docs/22_mcp/mcp_03_03_*` (row 11) after landing | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (deterministic key fallback), `REQ-010` (preserved behavior)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/shared/http_transport.py
