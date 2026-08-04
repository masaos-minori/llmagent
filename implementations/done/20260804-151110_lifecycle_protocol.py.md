# Implementation Procedure: scripts/agent/lifecycle_protocol.py

## Goal
Widen `LifecycleManagerProtocol.start_http_subprocess()`'s signature to accept the new optional
`shutdown_event` parameter, so the Protocol definition stays structurally truthful to its sole
production implementer (`_ServerLifecycleRouter` in `factory.py`).

## Scope
- In scope: `LifecycleManagerProtocol.start_http_subprocess()` (current lines 48-52).
- Out of scope: every other method on `LifecycleManagerProtocol` (`ensure_ready`,
  `shutdown_all`, `restart`, `shutdown_idle`, `get_transport_state`, `get_process_snapshot`) —
  none of these gain a `shutdown_event` parameter, matching the corresponding
  `_ServerLifecycleRouter` methods which are also left unchanged.

## Assumptions
- `_ServerLifecycleRouter` (`factory.py`) is the sole production implementer of
  `LifecycleManagerProtocol` — confirmed via the source plan's UNK-02
  (`rg -l "LifecycleManagerProtocol" scripts/ tests/` returns only `factory.py` and this file).
  Widening the Protocol here is safe once `implementations/20260804-151109_factory.py.md`
  (companion, this same batch) is applied to keep the two in sync.
- Test files use `MagicMock()`/`AsyncMock()` stand-ins, not concrete `Protocol`-conforming
  classes, so no test fixture needs updating for this signature change alone.

## Design decisions
- Add `shutdown_event: asyncio.Event | None = None` to the Protocol method's signature,
  mirroring `_ServerLifecycleRouter.start_http_subprocess()`'s new parameter exactly (same name,
  same type, same default) — `Protocol` structural typing requires call-signature
  compatibility, and matching the default value keeps callers that only reference the Protocol
  type (if any arise later) able to omit the argument.

## Alternatives considered
- Leave the Protocol unchanged and let the widened `_ServerLifecycleRouter` method be a
  compatible superset (structural subtyping generally tolerates additional optional parameters
  on the concrete implementation): rejected — `mypy`'s `Protocol` conformance checking is
  stricter about call-site compatibility when call sites are typed against the Protocol itself;
  keeping the two declarations in lockstep avoids a latent type-check gap and documents the
  parameter for any future second implementer.

## Implementation

### Target file
`scripts/agent/lifecycle_protocol.py`

### Procedure
1. Add `import asyncio` to the top-level imports (current lines 10-17) — not currently imported
   in this file (only `subprocess`, `typing.Protocol`/`runtime_checkable`,
   `shared.mcp_config.McpServerConfig`, `agent.lifecycle.LifecycleState` are imported per the
   full file read).
2. In `start_http_subprocess()` (current lines 48-52), change:
   ```python
   async def start_http_subprocess(
       self, server_key: str, cfg: McpServerConfig
   ) -> subprocess.Popen[bytes] | None:
   ```
   to:
   ```python
   async def start_http_subprocess(
       self, server_key: str, cfg: McpServerConfig, shutdown_event: asyncio.Event | None = None
   ) -> subprocess.Popen[bytes] | None:
   ```

### Method
- Read the full file (56 lines total) directly — small enough that a targeted grep plus a full
  read was more efficient than a line-range extraction. Confirmed via `grep -n "class
  LifecycleManagerProtocol\|def start_http_subprocess\|def restart\|def shutdown_all"
  scripts/agent/lifecycle_protocol.py` that `start_http_subprocess()` is the only method
  requiring an edit for this plan.

### Details
- No other change to the file — docstring, `...` body (Protocol methods have no implementation),
  and all other method signatures remain unchanged.

## Compatibility considerations
- Adding an optional, default-`None` parameter to a `Protocol` method is additive — any existing
  code that calls `start_http_subprocess(key, cfg)` without the new argument remains valid
  against the widened signature.
- `@runtime_checkable` decoration (current line 20) is unaffected — `isinstance()` checks against
  a `runtime_checkable` `Protocol` only inspect method *names*, not signatures, so this change
  cannot affect any existing `isinstance(x, LifecycleManagerProtocol)` check in the codebase
  (none found via `rg` per the source plan's UNK-02).

## Security considerations
- N/A — Protocol/type-definition-only file, no runtime behavior, no external input.

## Rollback considerations
- Two-line change (one new import, one widened signature); revertable via `git revert` with no
  migration implications.
- Should be applied together with `implementations/20260804-151109_factory.py.md` — reverting
  one without the other leaves the Protocol and its implementer's signatures diverging, which
  `mypy` would flag under strict Protocol-conformance checks.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Type check | `uv run mypy scripts/agent/lifecycle_protocol.py scripts/agent/factory.py scripts/agent/http_lifecycle.py` | No new errors vs. baseline; Protocol and implementer signatures match structurally |
| Format/lint | `uv run ruff format scripts/agent/lifecycle_protocol.py && uv run ruff check scripts/agent/lifecycle_protocol.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | No new broken contracts |
| Full suite | `uv run pytest` | No new failures |
| Final gate | `uv run pre-commit run --all-files` | Passes |

## Out of scope
- Every other `LifecycleManagerProtocol` method — unchanged.
- `deploy/deploy.sh` — no file added/removed.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-142044_plan.md
- Source implementation procedure: N/A
- Generated at: 20260804-151110
- Related target files: scripts/agent/lifecycle_protocol.py
