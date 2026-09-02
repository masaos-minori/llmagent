# Add end-to-end Production-only, authentication, and network-isolation regression coverage

## Priority
Medium

## Summary
Create an integrated regression suite proving the system operates with one Production-grade
policy, requires MCP authentication, and exposes Agent-internal HTTP services only through
loopback.

## Background
This issue depends on `localremoval`, `loopbackonly`, and `mcpauth` for the behaviors it tests
— it can be drafted in parallel but its tests will not pass until those land.

## Problem
Configuration-only tests cannot prove actual process behavior: a value may be correct in TOML
while a startup argument, environment override, deployment definition, or framework default
causes a wildcard listener. The migration needs tests at unit, startup-integration, HTTP,
process, and deployment levels.

## Reason for Change
Synthetic policy tests may pass while the shipped configuration or actual startup path behaves
differently; only layered, process-level tests catch that gap.

## Implementation Intent
Add tests rejecting Local mode and retired profile/public-bind keys; strict configuration
tests for tool safety tiers, allowed tools, ownership, routing, workflow definitions, database
schemas, requiredness, and security controls; loopback validator tests (accepted `127.0.0.1`,
accepted `::1` only if supported, rejected `0.0.0.0`/`::`/RFC1918-private/public/non-loopback
hostnames, IPv4-mapped IPv6 and alternate textual forms) across TOML/environment/CLI override
paths; required/optional MCP startup-failure tests; tests proving disabled optional tools carry
a concrete `disabled_reason` and are excluded from LLM visibility; MCP authentication tests for
missing/invalid/valid Bearer tokens; secret-redaction tests; process-level tests inspecting
actual listening sockets; an isolated-network (or equivalent) test proving internal services
are unreachable externally; deployment lint/validation detecting Docker host-port mappings,
wildcard host arguments, proxy exposure, and ingress/service publication.

## Target Files or Areas
- `tests/agent/`
- `tests/mcp_servers/`
- `tests/integration/`
- Event Bus tests
- Configuration-validation tests
- Deployment validation scripts and CI workflows

## Required Changes
- Add tests rejecting Local mode and retired profile/public-bind keys.
- Add strict configuration tests (tool tiers, ownership, routing, workflow definitions, database schemas, requiredness, security controls) exercised through the real startup path.
- Add loopback validator tests across TOML/environment/CLI override paths, covering both accepted and rejected address forms.
- Add required/optional MCP startup-failure tests and disabled-tool-visibility tests.
- Add MCP authentication tests (missing/invalid/valid tokens) and secret-redaction tests.
- Add process-level socket-inspection tests and an isolated-network (or equivalent) external-unreachability test.
- Add deployment validation detecting host-port publication, wildcard bindings, and internal-endpoint publication.
- Load and test the actual shipped configuration where practical, not only synthetic config objects.

## Constraints
- Do not replace focused unit tests with only a large end-to-end test.
- Avoid tests that depend on external internet access; use disposable ports, temporary directories, and temporary credentials.
- Verify actual runtime behavior, not only static configuration text.
- Keep unrelated existing test semantics unchanged.

## Acceptance Criteria
- Retired Local and public-bind settings are rejected by tests.
- Strict Production-grade validation is exercised through the real startup path.
- Required MCP failure aborts startup; optional availability failure disables only affected tools.
- Authentication success/failure paths and secret-redaction behavior are covered.
- IPv4 and IPv6 loopback behavior is covered; non-loopback bindings and URLs are rejected.
- Tests inspect actual listening sockets; an external-namespace (or equivalent) connectivity test fails as expected.
- Deployment validation rejects publication of internal endpoints.
- The shipped configuration is exercised where feasible.

## Testing Expectations
Implement and run tests in layers: address/configuration unit tests, startup-policy and
requiredness tests, MCP authentication and tool-visibility tests, process/socket integration
tests, deployment exposure checks, then full affected regression suites.

## Documentation Impact
Document how the test suite proves loopback-only behavior, which tests require platform
capabilities, and how to run equivalent manual socket checks when a network-namespace test is
unavailable.

## Out of Scope
- Implementing runtime changes covered by `localremoval`, `loopbackonly`, and `mcpauth`.
- Tests requiring public cloud resources or external internet access.
- General test-suite restructuring unrelated to the migration.

## Dependencies
Depends on `localremoval`, `loopbackonly`, and `mcpauth` for the behaviors under test; the test
suite itself can be scaffolded in parallel but will not pass until those land.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Inspect existing startup, MCP, Event Bus, authentication, and configuration tests before
adding new fixtures. Reuse established subprocess and temporary-repository patterns. Ensure
failures explain whether the problem is configuration acceptance, process binding,
authentication, discovery, routing, or external reachability.
