# Implementation: Create `scripts/mcp_launcher.py` unified standalone launcher (Phase 2)

## Goal

Provide a single, package-external launcher script that can start any individual MCP server by key from the command line, with automatic server discovery and a port-collision guard, so developers can debug one server in isolation without hand-editing `sys.path` or memorizing each server's entry-point module path.

## Scope

**In:**
- New file `scripts/mcp_launcher.py`, placed at `scripts/` top level (outside the `mcp_servers` package)
- Automatic server discovery: `pkgutil.walk_packages` + `inspect` over `mcp_servers.*` to collect `MCPServer` subclasses, keyed by `server_key` (falling back to `server_name` with its `-mcp` suffix stripped)
- CLI interface: `<server_key>` positional arg to launch one server, `--list` to print all discovered server keys, `--force` to bypass the port-collision guard
- Port-collision guard: before calling `run_http()`, attempt a short-timeout `GET /health` against the target port; if it responds, print a warning and abort (unless `--force`)
- Per-module import isolation during discovery: a server module that raises on import must not abort discovery of the other servers

**Out:**
- No process-lock or PID-file exclusion mechanism — the port-collision guard is a best-effort, TOCTOU-tolerant check only (explicitly out of scope per the plan)
- No changes to `MCPServer` base class or any individual `server.py`'s `run_http()` implementation

## Assumptions

1. This document depends on Phase 1 (`scripts/mcp_servers/mcp_servers_package_rename.md`) having already renamed the package — `mcp_launcher.py` imports `mcp_servers.*`, not `mcp.*`.
2. Every server module's top-level code (executed at import time by `pkgutil.walk_packages`) does not perform network I/O or require environment variables to be set just to import successfully — per the plan's UNK-02, this must be verified per-module at implementation time; any module that fails must be caught and skipped (not raised) during discovery, per the Method below.
3. `MCPServer.server_key` is optional (`getattr(self, "server_key", type(self).__name__)` pattern already used elsewhere in `scripts/mcp/server.py`); the launcher's discovery logic should use the same fallback convention — `server_key` attribute if declared on the class, else derive from `server_name` by stripping a trailing `-mcp` suffix.
4. All 10 server modules expose a `run_http()` instance method (confirmed base-class contract in `scripts/mcp/server.py:193` at planning time, pre-rename path).

## Implementation

### Target file

`scripts/mcp_launcher.py` (new file)

### Procedure

1. Implement discovery:
   ```python
   import pkgutil
   import inspect
   import importlib
   from mcp_servers.server import MCPServer  # base class, post-rename import path

   def discover_servers() -> dict[str, type[MCPServer]]:
       registry: dict[str, type[MCPServer]] = {}
       import mcp_servers
       for _, modname, _ in pkgutil.walk_packages(mcp_servers.__path__, prefix="mcp_servers."):
           try:
               module = importlib.import_module(modname)
           except Exception as exc:  # noqa: BLE001 — discovery must not abort on one bad module
               print(f"warning: could not import {modname}: {exc}", file=sys.stderr)
               continue
           for _, obj in inspect.getmembers(module, inspect.isclass):
               if issubclass(obj, MCPServer) and obj is not MCPServer:
                   key = getattr(obj, "server_key", None) or obj.server_name.removesuffix("-mcp")
                   registry[key] = obj
       return registry
   ```
2. Implement the port-collision guard as an async or sync short-timeout HTTP GET (reuse the existing `httpx` dependency already used elsewhere in this project, per `rules/coding.md`'s "use httpx, not requests" convention):
   ```python
   import httpx

   def port_is_responding(port: int, timeout: float = 0.5) -> bool:
       try:
           resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout)
           return resp.status_code < 500  # any response at all indicates something is listening
       except httpx.HTTPError:
           return False
   ```
3. Implement `argparse`-based CLI:
   ```python
   def main() -> None:
       parser = argparse.ArgumentParser()
       parser.add_argument("server_key", nargs="?")
       parser.add_argument("--list", action="store_true")
       parser.add_argument("--force", action="store_true")
       args = parser.parse_args()

       registry = discover_servers()
       if args.list or not args.server_key:
           for key in sorted(registry):
               print(key)
           return
       server_cls = registry.get(args.server_key)
       if server_cls is None:
           print(f"unknown server_key: {args.server_key!r}. Use --list to see available keys.", file=sys.stderr)
           sys.exit(1)
       instance = server_cls()
       port = instance.http_port
       if not args.force and port_is_responding(port):
           print(
               f"port {port} is already responding — {args.server_key} may be running under the agent. "
               "Use --force to start anyway.",
               file=sys.stderr,
           )
           sys.exit(1)
       instance.run_http()
   ```
4. Run `uv run ruff format scripts/mcp_launcher.py` and `uv run ruff check scripts/mcp_launcher.py --fix`.

### Method

Reflection-based discovery over direct hand-maintained registry, matching the plan's explicit design decision (6.3): avoids a second, drift-prone source of truth alongside each server's own class definition and `config/agent.toml`'s `[mcp_servers.*]` runtime SSOT.

### Details

- `sys.path` handling: since `scripts/mcp_launcher.py` lives at the `scripts/` top level (a sibling of the `mcp_servers` package, not inside it), it must be invoked as `uv run python scripts/mcp_launcher.py <key>` from the repo root so that `scripts/` is importable — verify at implementation time whether `sys.path.insert(0, ...)` bootstrapping is needed, or whether the project's existing `PYTHONPATH=scripts` convention (used throughout `rules/toolchain.md`) is sufficient without extra code.
- The port-collision guard intentionally treats "any HTTP response, even non-2xx" as "already running" — a 503 from `/health` still indicates the port is bound by *some* process, which is the condition being guarded against (starting a second instance on the same port).
- Per-module exception isolation during discovery directly addresses UNK-02 from the plan: if `mcp_servers.cicd.server` or `mcp_servers.rag_pipeline.server` (both `startup_mode="none"`, dependency-sensitive) raise on import due to missing environment configuration, the exception is caught, logged as a warning, and discovery continues for the remaining 9 servers.

## Validation plan

```bash
uv run ruff check scripts/mcp_launcher.py
uv run mypy scripts/mcp_launcher.py
uv run python scripts/mcp_launcher.py --list                    # expect all 10 server keys printed
uv run python scripts/mcp_launcher.py git                        # expect no ModuleNotFoundError; /health returns 200
curl -s http://127.0.0.1:<git-mcp-port>/health
# With the agent already running (same server active):
uv run python scripts/mcp_launcher.py git                        # expect port-collision warning + exit 1
uv run python scripts/mcp_launcher.py git --force                # expect it proceeds and attempts to bind (may itself fail on the OS bind, which is acceptable/expected)
```

Expected outcome: `--list` shows all 10 servers; a standalone launch of any one server succeeds without the historical `ModuleNotFoundError`; the port-collision guard correctly detects and blocks (or, with `--force`, allows) launching against an already-bound port.
