# Implementation: Document EventBus loopback bind requirement in deploy operations doc

Steps covered: Plan 20260626-094714 — All steps (docs-only, optional app.py)

---

## Goal

Document that the EventBus server must bind to loopback (`127.0.0.1`) in production, not `0.0.0.0`, to prevent unintended external exposure. Add deployment note and optionally harden the default in `app.py`.

---

## Scope

- **In scope**: `docs/06_eventbus_05_configuration_deploy_and_operations.md` — loopback bind requirement
- **Optionally in scope**: `scripts/eventbus/app.py` (or equivalent) — change default bind address if currently `0.0.0.0`

---

## Assumptions

- EventBus is a FastAPI/Starlette app served via uvicorn.
- The app currently binds to `0.0.0.0` by default (external exposure).
- Production deployment should bind to `127.0.0.1` (loopback only), with a reverse proxy or the agent process as the only client.

---

## Implementation

### Target file (primary)
`docs/06_eventbus_05_configuration_deploy_and_operations.md`

### Procedure
1. Find the deployment section.
2. Add "Bind Address" warning:
   ```
   ### Bind Address

   The EventBus server should bind to `127.0.0.1` (loopback) in production, not
   `0.0.0.0`. Binding to `0.0.0.0` exposes the EventBus API to the local network,
   which is a security risk (no authentication layer on the EventBus HTTP endpoints).

   ```toml
   # config/eventbus.toml
   host = "127.0.0.1"
   port = 8765
   ```

   If remote access is required, use a reverse proxy with authentication.
   ```

### Optional: app.py default
If `app.py` has `host = "0.0.0.0"` as default, change to `host = "127.0.0.1"`.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "127.0.0.1\|loopback\|bind" docs/06_eventbus_05_configuration_deploy_and_operations.md` shows the section.
