# Enforce loopback-only HTTP connectivity and remove all external-publication paths

## Priority
High

## Summary
Restrict every Agent-internal HTTP service to same-host loopback connectivity and remove every
supported mechanism that can publish those services externally (CLI overrides, environment
variables, Docker port mappings, systemd overrides, reverse proxies, orchestration manifests).

## Background
Event Bus has no complete production authentication/authorization model, so loopback binding
is currently its effective security boundary. The same network boundary should be enforced
consistently for MCP, LLM, embedding, RAG, Agent, and other internal HTTP services. This has
not been investigated or filed as a narrower issue previously — no related Known Issue or ADR
entry was found addressing bind-address enforcement.

## Problem
Limiting only the default configuration to `127.0.0.1` is insufficient if another
configuration key, startup argument, container mapping, or proxy can restore external
exposure. Binding to a private LAN address is also outside the requirement because it permits
access from another host.

## Reason for Change
The target architecture does not allow external HTTP access to Agent-internal services.

## Implementation Intent
Bind every internal HTTP server to `127.0.0.1` (permit `::1` only if IPv6 loopback support is
intentionally retained and tested); reject wildcard, private-LAN, public, and non-loopback
hostname bindings; apply the rule to the Agent HTTP endpoint, LLM, embedding service, all MCP
servers, RAG Pipeline service, Event Bus, and any other same-host-only service; normalize
Agent-side internal URLs to loopback; validate endpoint hosts after all TOML,
environment-variable, and CLI overrides are applied; remove `allow_public_bind` and equivalent
public-bind overrides, treating retired keys as configuration errors; remove Docker
host-port publication, wildcard Uvicorn/Gunicorn bindings, reverse-proxy routes, Kubernetes
Services/Ingresses, and systemd overrides that expose internal endpoints; add post-start
verification of actual listening sockets and an external-namespace connection test.

## Target Files or Areas
- `scripts/mcp_servers/server.py`
- `scripts/shared/mcp_config.py`
- `scripts/shared/production_config_validator.py`
- `scripts/agent/config_builders.py`
- `scripts/eventbus/config.py`
- `scripts/eventbus/app.py`
- `config/agent.toml`
- `config/eventbus.toml`
- `config/*_mcp_server.toml`
- `deploy/`, `docker-compose*.yml`, `Dockerfile*`, `systemd/`, `nginx/`, `caddy/`, `k8s/` — only modify paths that actually exist
- Startup and run scripts
- Network, startup, Event Bus, and MCP integration tests

## Required Changes
- Search for `allow_public_bind`, `0.0.0.0`, `::`, `--host`, `http_host`, `bind`, `listen`, `ports:`, `expose:`, `Ingress`, `127.0.0.1`, `localhost` before editing; inspect each `::`/`localhost` match manually to avoid unrelated replacements.
- Bind every internal HTTP server to `127.0.0.1` (and `::1` only if intentionally retained).
- Reject wildcard, private-LAN, public, and non-loopback hostname bindings; account for IPv4-mapped IPv6 and alternate textual IP forms.
- Remove `allow_public_bind` and equivalent overrides from Event Bus and MCP configuration models; treat retired keys as configuration errors.
- Remove Docker host-port publication, wildcard bindings, reverse-proxy routes, Kubernetes Ingresses/Services, and systemd overrides that expose internal endpoints.
- Add post-start verification of actual listening sockets and detection of duplicate internal endpoint/port assignments where the architecture supports it.

## Constraints
- Do not enable external access through authentication, TLS, a reverse proxy, SSH tunnel, firewall exception, or container network publication.
- Do not replace `allow_public_bind` with another escape hatch.
- Do not change service responsibilities, HTTP API contracts, or replace HTTP with stdio.
- Keep remote third-party endpoints (external LLM, web-search providers) out of scope unless explicitly classified as Agent-internal same-host services.
- Preserve service ports unless a verified collision requires a separate decision.

## Acceptance Criteria
- Internal servers accept only `127.0.0.1` and, if intentionally supported, `::1`.
- Wildcard, LAN, public, and non-loopback hostname bindings fail validation and startup.
- `allow_public_bind` and equivalent escape hatches no longer exist; a retired public-bind key fails clearly.
- Agent-side internal service URLs resolve only to loopback.
- No Docker, reverse-proxy, systemd, or orchestration definition publishes internal endpoints externally.
- Actual listening sockets are verified after startup; a connection attempt from another host or isolated network namespace fails.
- Event Bus always binds to loopback.

## Testing Expectations
Add unit tests accepting `127.0.0.1`/supported IPv6 loopback and rejecting wildcard/private/
public/non-loopback hostnames, across TOML, environment-variable, and CLI override paths. Add
integration tests inspecting actual sockets, and deployment tests that fail on host-port
publication or reverse-proxy exposure. Verify both server bind settings and Agent-side client
URLs.

## Documentation Impact
Update security boundaries, MCP and Event Bus configuration references, deployment
instructions, port inventories, and operations checklists. Remove any guidance implying
internal services may be publicly exposed.

## Out of Scope
- Removal of Local runtime policy (`localremoval`).
- Implementing Event Bus authentication.
- Changing external provider connectivity or replacing HTTP transport.
- Changing service ports without a separately verified collision.

## Dependencies
N/A: none — independently actionable regardless of `localremoval`'s outcome.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read all existing bind, URL, startup, and deployment logic before editing. Validate the
effective address after overrides, not only static TOML values. Make application-level
loopback binding the authoritative control, then remove deployment publication paths and add
runtime socket verification. Treat any discovered external publication path as part of this
issue only when it exposes an Agent-internal service.
