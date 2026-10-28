## Goal

Apply a named, process-wide default concurrency ceiling to every configured MCP
server that has no explicit positive `tool_concurrency_limits` entry, so the
invocation path always has backpressure, while preserving the documented "explicit
`0`/negative = unlimited" opt-out and the existing behavior of configured positive
limits (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`).

## Scope

Modifies only `scripts/shared/tool_transport_invoker.py`: adds the module-level
constant `DEFAULT_PER_SERVER_CONCURRENCY` (new), restructures `_ensure_semaphores()` to
build a semaphore for every key in `self._server_configs`, and updates the
`_ensure_semaphores()` and `ToolTransportInvoker.__init__` docstrings. No other
file, signature, state, or configuration change.

## Assumptions

- The shared `httpx.AsyncClient` used by the invocation path carries no `limits=`
  override anywhere in `scripts/` (verified: `factory.py:95` builds it with
  `timeout` only; every other `httpx.AsyncClient(...)` in `scripts/` passes
  `timeout` only). httpx's default pool (100 connections) therefore still applies,
  which is the basis of the `8` sizing (`REQ-001`).
- `git` and `mdq` are ordinary server keys present in `server_configs`
  (`[mcp_servers.git]` and `[mcp_servers.mdq]` in `config/agent.toml`), so capping
  them is a normal per-server semaphore, not a special case.
- Overlap with the sibling `mcpcompat001` Plan on this file is **Compatible**, not a
  conflict: `mcpcompat001` splits the health-type import block (lines 15-21) to
  `shared.mcp_health`; this Plan edits the constant (module scope),
  `_ensure_semaphores()` (lines 90-114), and the two docstrings. Different lines and
  responsibilities; whichever Plan lands later rebases. Recorded bidirectionally in
  `mcpcompat001`'s Assumptions.
- `_maybe_semaphore(None)` keeps its `contextlib.nullcontext()` contract, so the
  explicit-unlimited and unknown-key paths stay unchanged (`REQ-003`).

## Design decisions

- **Value `8`**: sized from repository facts, not convention — the highest
  configured production limit is `4` (`config/agent.toml`, 8 entries) and 10
  configured servers × 8 = 80 stays under the shared client's default pool ceiling
  of 100. The constant is documented with that arithmetic so a future change is a
  deliberate edit, not a magic number.
- **Build over `self._server_configs`, not the limits map**: this is what closes
  the omitted-key gap. An empty or absent map still produces a cap per known server.
  `_maybe_semaphore(None)` remains the unlimited path for explicit opt-outs.

## Alternatives considered

- **Global cross-server cap**: rejected — it would over-restrict a fan-out spread
  across servers, and the Issue prefers per-server semaphores under the shared
  `httpx.AsyncClient`.
- **New config key or constructor parameter**: rejected — a new
  tool_concurrency_default key or a default_concurrency param would widen the
  config loader, `ToolConfig`, and public signatures for a value already tunable
  per server through the existing `tool_concurrency_limits` map.

## Implementation
### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. Add the module-level constant after the `logger` setup (lines 24-25) and before
   the `ToolTransportInvoker` class definition (line 28):

   ```python
   # Process-wide default per-server concurrency ceiling. Sized from repo facts:
   # the highest configured production limit is 4 (config/agent.toml) and 10
   # configured servers x 8 = 80 stays under the shared httpx.AsyncClient default
   # pool ceiling of 100 connections (factory.py builds that client with timeout
   # only; no limits= override exists anywhere in scripts/).
   DEFAULT_PER_SERVER_CONCURRENCY: int = 8
   ```

2. Replace the body of `_ensure_semaphores()` (currently lines 90-114) with a
   version that guards on `self._semaphores is None` alone (drop the
   `and self._concurrency_limits` clause) and resolves the effective limit per
   `self._server_configs` key:

   ```python
       def _ensure_semaphores(self) -> None:
           """Lazily create one concurrency semaphore per configured server.

           Every key in ``self._server_configs`` gets a semaphore capped at its
           effective limit: the configured positive value when present, otherwise
           the process-wide DEFAULT_PER_SERVER_CONCURRENCY ceiling. An
           explicit ``0`` or negative limit opts out of the default and stays
           unlimited (no semaphore entry); such a known key is warned about once
           per process so the chosen meaning is visible instead of a silent drop.
           """
           if self._semaphores is None:
               semaphores: dict[str, asyncio.Semaphore] = {}
               for key in self._server_configs:
                   configured = self._concurrency_limits.get(key)
                   if configured is not None and configured <= 0:
                       logger.warning(
                           "tool_concurrency_limits: %r is %d; treated as unlimited "
                           "(no semaphore created).",
                           key,
                           configured,
                       )
                       continue
                   limit = (
                       configured
                       if configured is not None
                       else DEFAULT_PER_SERVER_CONCURRENCY
                   )
                   semaphores[key] = asyncio.Semaphore(limit)
               self._semaphores = semaphores
   ```

3. Expand `ToolTransportInvoker.__init__`'s one-line docstring (currently line 38)
   to state the default ceiling and the opt-out:

   ```python
       """Initialize with HTTP client, server configs, and optional concurrency limits.

       Each configured server is capped at its configured positive limit, or at
       DEFAULT_PER_SERVER_CONCURRENCY when no positive limit is set; an explicit
       0/negative limit opts out (unlimited)."""
   ```

### Method

The three edits are confined to `tool_transport_invoker.py`. Step 1 introduces the
new `(new)` constant; Step 2 rewrites the only semaphore-construction site so it no
longer requires a non-empty `_concurrency_limits` and instead caps every known
server; Step 3 makes the docstrings describe the new default. The live disabled
guard in `_run_precall_gates()` (lines 248-302) is untouched.

### Details

- **Constant** (Step 1) — insert between the `logger` setup and the class. The
  rationale comment names the httpx-pool dependency so a future `limits=` change is
  noticed where the constant is defined (`REQ-001`).
- **`_ensure_semaphores()`** (Step 2) — the guard changes from
  `if self._semaphores is None and self._concurrency_limits:` to
  `if self._semaphores is None:`, so an unconfigured invoker still builds caps. The
  loop now iterates `self._server_configs`; a configured `0`/negative value warns
  once per process and skips (preserving the documented opt-out, `REQ-003`); any
  other key uses its configured value or the `(new)` default. Unknown keys (in the
  limits map but not in `server_configs`) are not iterated and are reported in
  `__init__`.
- **`__init__` docstring** (Step 3) — states the bounded default and the preserved
  opt-out (`REQ-004`).
- **Preserved unchanged** (`REQ-003`): the unknown-key warning in `__init__`
  (lines 47-53), the `_maybe_semaphore(None)` → `contextlib.nullcontext()` path
  (lines 116-126), and configured-positive-limit behavior.

## Compatibility considerations

- Existing semaphore tests assert configured-limit behavior only and remain valid:
  `test_semaphore_applied_with_concurrency_limit` (`tests/shared/test_tool_transport_invoker.py`),
  `test_zero_limit_is_unlimited_and_warns`, and `test_positive_limit_bounds_semaphore`
  (`TestConcurrencyLimitZeroSemantics`).
- `test_tool_executor_order.py` assigns `executor._semaphores = None` directly and
  stays valid with the restructured lazy builder.
- `mcpcompat001`'s import split on this file is Compatible; the second Plan to land
  rebases onto it.

## Security considerations

N/A: no safety-boundary change. The per-server ceiling is a backpressure guardrail,
not an access control; adding it widens protection (caps previously uncapped
`git`/`mdq` servers) and never relaxes an existing limit.

## Rollback considerations

Revert the commit to `scripts/shared/tool_transport_invoker.py`; the change is
confined to one new constant, one method body, and one docstring.

## Validation plan

- Unit (new behavior): `uv run pytest tests/shared/test_tool_transport_invoker.py`.
- Static + contract: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`,
  `PYTHONPATH=scripts uv run lint-imports`.
- Regression: `uv run pytest tests/shared/test_tool_executor*.py`.
- Full suite: `uv run pytest tests/`.

## Completion criteria

- `DEFAULT_PER_SERVER_CONCURRENCY` (new) exists at module level and the default-cap test
  references it rather than a duplicated literal (`REQ-001`).
- `_ensure_semaphores()` builds a semaphore for every `self._server_configs` key,
  using the configured positive value or the default, and creates no entry for an
  explicit `0`/negative key (`REQ-002`).
- Configured-positive, unknown-key, `0`/negative-warning, and `_maybe_semaphore(None)`
  behaviors are unchanged (`REQ-003`).
- Both docstrings state the bounded default and the preserved opt-out (`REQ-004`).
- No currently-capped server is re-capped; `config/agent.toml` is unchanged
  (`REQ-006`).

## Out of Scope

- Any change to `tool_executor.py` (the `concurrency_limits` docstring there is
  covered by a separate row).
- New configuration keys or constructor parameters.
- Restructuring the pre-call gate chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261028-102436 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-102436 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-102436 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-102436 |  |

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
- **Requirement ID**: `REQ-001` (module-level `DEFAULT_PER_SERVER_CONCURRENCY` (new) with sizing rationale), `REQ-002`
  (`_ensure_semaphores()` caps every known server), `REQ-003` (configured-positive / unknown-key / `0`/negative / nullcontext unchanged), `REQ-004`
  (docstrings state the default ceiling and opt-out), `REQ-006` (uncapped `git`/`mdq` newly capped; no re-cap of capped servers)
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004831
- **Related target files**: scripts/shared/tool_transport_invoker.py