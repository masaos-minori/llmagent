# Implementation: agent/repl_health.py — comment update

## Goal

Update a docstring/comment in `repl_health.py` that references `ServerLifecycleManager.restart()` to reflect the new direct wiring.

## Scope

- `scripts/agent/repl_health.py` line 184: docstring/comment update.
- No functional changes — the actual `ctx.services.lifecycle.restart()` call is polymorphic and works with any `LifecycleManagerProtocol` implementation.

## Assumptions

- `ctx.services.lifecycle` type will be `LifecycleManagerProtocol` after previous changes, but the runtime call is the same.
- `ServerLifecycleManager` is no longer a relevant name for the comment.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Find line 184 containing `ServerLifecycleManager.restart()` in the docstring/comment.
2. Replace with `LifecycleManagerProtocol.restart()` or simply `ctx.services.lifecycle.restart()`.

### Method

Comment-only update.

## Validation plan

1. `rg "ServerLifecycleManager" scripts/agent/repl_health.py` — 0 matches.
2. `uv run ruff check scripts/agent/repl_health.py` — no errors.
