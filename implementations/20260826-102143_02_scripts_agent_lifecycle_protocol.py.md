## Goal

Add `cleanup_server_resources(server_key: str) -> str` to
`LifecycleManagerProtocol` (REQ-001) so the method `config_reload.py` needs to call is
declared on the typed interface, instead of being reached only through
`getattr(lifecycle, "_cleanup_server_resources")`.

## Scope

- In scope: `scripts/agent/lifecycle_protocol.py` — add one new abstract method
  signature to `LifecycleManagerProtocol`.
- Out of scope (per Plan): `HttpLifecycleProtocol` (the other protocol in this file,
  unrelated to this method) and any change to `_ServerLifecycleRouter`'s
  implementation (REQ-002, covered by the sibling `factory.py` document) or
  `config_reload.py`'s call site (REQ-003, covered by the sibling `config_reload.py`
  document).

## Assumptions

- `LifecycleManagerProtocol` is decorated `@runtime_checkable` (`scripts/agent/
  lifecycle_protocol.py:21`) — adding a new method to it does not change this
  decorator's applicability; `runtime_checkable` `Protocol`s only check method
  *presence* at `isinstance()`-check time, not signatures, so this is a compile-time
  (`mypy`) contract addition with no runtime behavior implication for existing
  `isinstance(x, LifecycleManagerProtocol)` call sites (none found via `rg -n
  "isinstance.*LifecycleManagerProtocol" scripts/` — zero matches, so this is moot in
  practice, noted only for completeness).
- `_ServerLifecycleRouter` (`scripts/agent/factory.py`) is confirmed the sole
  production implementer (see the sibling `factory.py` document's Assumptions for the
  `rg` evidence) — adding a new required method to this Protocol will be satisfied by
  that document's REQ-002 addition; the two changes must land together for `mypy` to
  pass (see Compatibility considerations).

## Design decisions

- Match the existing method-declaration style in this Protocol exactly: `async def`
  is used for the other lifecycle-transition methods (`ensure_ready`, `shutdown_all`,
  `restart`, `shutdown_idle`) because they perform I/O, but
  `get_transport_state()` and `get_process_snapshot()` are plain (non-`async`) `def`
  because they are synchronous accessors/delegations. `cleanup_server_resources()`
  belongs in the second group: `HttpServerLifecycleManager._cleanup_server_resources()`
  (`scripts/agent/http_lifecycle.py:239`) is a plain synchronous method (file I/O via
  `fh.close()`, dict pops — no `await`), so the Protocol method is declared as a
  plain `def`, following the same shape as `get_process_snapshot()`
  (`scripts/agent/lifecycle_protocol.py`'s existing last method):
  ```python
  def get_process_snapshot(self, server_key: str) -> dict | None:
      """Return process snapshot dict for a managed subprocess server, or None."""
      ...
  ```
- Return type `str` (not `str | None`), matching
  `HttpServerLifecycleManager._cleanup_server_resources()`'s actual declared return
  type exactly — the Plan's Implementation intent explicitly settles this (previously
  an open question in the source issue) in favor of fidelity to the real
  implementation over speculative `None`-handling for a currently-unused return value.

## Alternatives considered

- Declare the return type as `str | None` to leave room for a future "nothing to
  clean up" case: rejected — `HttpServerLifecycleManager._cleanup_server_resources()`
  always returns a `str` today (it returns `stderr_content`, which defaults to `""`
  when there is nothing to read, never `None` — confirmed at
  `scripts/agent/http_lifecycle.py:239-247`); the Protocol should describe the actual
  contract, not speculative future behavior (Plan's Implementation intent explicitly
  chose `str`).
- Add the method to `HttpLifecycleProtocol` instead of `LifecycleManagerProtocol`:
  rejected — `HttpLifecycleProtocol` is documented in this file's own module
  docstring as "HTTP-only: start_http_subprocess", i.e. scoped to the one HTTP-subprocess
  -specific method; `cleanup_server_resources()` is a general lifecycle-manager
  capability exercised from `config_reload.py` via the general
  `ctx.services_required.lifecycle: LifecycleManagerProtocol` reference, so it belongs
  on the general Protocol, matching REQ-001's own wording.

## Implementation

### Target file

`scripts/agent/lifecycle_protocol.py`

### Procedure

1. Add a new method signature `cleanup_server_resources(self, server_key: str) ->
   str: ...` to `LifecycleManagerProtocol`, placed after `get_process_snapshot()`
   (the Protocol's current last method) to mirror the placement of the concrete
   implementation in the sibling `factory.py` document.
2. No import changes needed — `str` and `server_key: str` require no new imports
   beyond what this file already has.

### Method

Single new abstract method signature; no changes to any existing signature.

### Details

Current end of `LifecycleManagerProtocol` (verified at
`scripts/agent/lifecycle_protocol.py`, full file — this is the whole class body):

```python
    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        ...
```

Target state (new method appended):

```python
    def get_process_snapshot(self, server_key: str) -> dict | None:
        """Return process snapshot dict for a managed subprocess server, or None."""
        ...

    def cleanup_server_resources(self, server_key: str) -> str:
        """Release tracking resources for a removed server; return its stderr tail."""
        ...
```

## Compatibility considerations

- `LifecycleManagerProtocol` is a structural (`Protocol`) type — adding a required
  method means any class that is type-checked against this Protocol (via an
  annotation, not `isinstance()`) must now implement it for `mypy` to accept it.
  Confirmed only one such class exists in production code
  (`_ServerLifecycleRouter`), and the sibling `factory.py` document (seq 01) adds the
  matching implementation. **These two changes are not independently valid under
  `mypy`** — landing this document's change alone (before or without the
  `factory.py` implementation) will produce a new `mypy` structural-typing error at
  `scripts/agent/factory.py:307` (`lifecycle: LifecycleManagerProtocol =
  _ServerLifecycleRouter(...)`), since `_ServerLifecycleRouter` would no longer
  satisfy the Protocol. Both documents (seq 01 and seq 02) must be applied together
  before running `mypy scripts/agent/` for a green result.
- No runtime `isinstance()` check sites exist for this Protocol (confirmed above), so
  there is no runtime compatibility risk, only the `mypy`-time coupling above.

## Security considerations

- N/A: adding a typed method signature to a `Protocol` has no runtime behavior and no
  security implication by itself.

## Rollback considerations

- Single-file, single-method-signature addition. Revert via `git revert` of the
  implementing commit — but only together with the sibling `factory.py` document's
  change (see Compatibility considerations); reverting this file alone while
  `_ServerLifecycleRouter.cleanup_server_resources()` and `config_reload.py`'s direct
  call remain in place would not break anything at runtime (the Protocol is only
  checked statically), but would silently remove the type-safety guarantee this Plan
  exists to add. Revert all three documents' changes together if reverting.

## Validation plan

- `uv run mypy scripts/agent/` — no new errors (Plan AC-01); must be run only after
  the sibling `factory.py` document's `cleanup_server_resources()` implementation is
  also in place (see Compatibility considerations).
- `uv run pytest` (full suite) — no new failures (a `Protocol` signature addition has
  no runtime test surface of its own).

## Completion criteria

- `LifecycleManagerProtocol` in `scripts/agent/lifecycle_protocol.py` declares
  `def cleanup_server_resources(self, server_key: str) -> str: ...`.
- `uv run mypy scripts/agent/` passes with no new errors once this change and the
  sibling `factory.py` implementation are both applied.

## Out of scope

- `_ServerLifecycleRouter`'s implementation (REQ-002) — covered by
  `implementations/20260826-102143_01_scripts_agent_factory.py.md`.
- `config_reload.py`'s call-site replacement (REQ-003) — covered by
  `implementations/20260826-102143_04_scripts_agent_services_config_reload.py.md`.
- `HttpLifecycleProtocol` and any other method on `LifecycleManagerProtocol` (per
  Plan Scope — untouched).
- `deploy/deploy.sh` changes — none needed (no file added, removed, or moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `cleanup_server_resources()` signature to `LifecycleManagerProtocol` (REQ-001) | Pending | — | — | |
| 2 | Run `uv run mypy scripts/agent/` jointly with the `factory.py` implementation (seq 01) | Pending | — | — | Must not be run in isolation — see Compatibility considerations |

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
- **Requirement ID**: REQ-001 (add `cleanup_server_resources()` to `LifecycleManagerProtocol`)
- **Source issue**: `issues/20260825_cfgreload_lifecycle_cleanup_getattr_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-141919_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-102143
- **Related target files**: `scripts/agent/lifecycle_protocol.py`
