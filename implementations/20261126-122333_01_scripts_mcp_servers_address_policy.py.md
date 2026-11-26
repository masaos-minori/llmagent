## Goal
- Create the reusable address policy for outbound fetches: resolve every A and AAAA answer of a host and accept it only when all answers are public (REQ-001, fail-closed resolution and mixed-answer rejection; REQ-008, reusable without a web search import).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module `scripts/mcp_servers/address_policy.py` and its test companion.
- Out of scope: connecting, pinning, redirects, and limits (the bounded fetch procedure, seq 02), and mapping the errors to web search exceptions (the search provider procedure, seq 03).

## Assumptions
- Plan Assumptions carried over: no new dependency is needed; the module may import only the standard library (`mcp_servers` may import `db` and `shared`, never `agent` or `rag`, `.importlinter`).
- Overlap judgment (Plan overlap check): this new file overlaps no other Frozen Plan.
- Evidence checked in Step 3a: no resolver exists in the web search package (`rg getaddrinfo scripts/mcp_servers` found no match); the RAG crawler predicate (`scripts/rag/ingestion/crawler_utils.py:140-190`) is the reference for the prohibited set but cannot be imported.

## Design decisions
- Two failure kinds, one exception class: `AddressRejectedError` (new) carries `kind` (prohibited_address or resolution_failed), so a caller can map the first to an authorization error and the second to a network error. The module defines no web search type.
- The resolver is injectable (`resolver` parameter, default the running loop's `getaddrinfo`) so tests and the bounded fetch helper never touch DNS.

## Alternatives considered
- Reuse the RAG crawler predicate: rejected, `mcp_servers` must not import `rag`.
- Filter mixed answers to public addresses: rejected by Plan decision D-1 (reject all, fail closed).

## Implementation
### Target file
`scripts/mcp_servers/address_policy.py` (new)

### Procedure
1. Create the module with the module docstring format the repository uses (path line, one-sentence purpose, `Dependency direction:` line).
2. Add `AddressRejectedError(RuntimeError)` with a `kind` attribute and a message that names the host and the kind but never the resolved address list.
3. Add `is_public_address(address: str) -> bool` and `resolve_public_addresses(host, port, *, resolver=None) -> tuple[str, ...]`.
4. Keep the module standard-library only and below the module size gate.

### Method
- `is_public_address` (new): parse with `ipaddress.ip_address` (after removing a `%scope` suffix); an unparseable value is not public. Unwrap an IPv4-mapped IPv6 address (ipv4_mapped) and judge the IPv4 address. Public means is_global is true and the address is not multicast, loopback, link-local, private, reserved, or unspecified.
- `resolve_public_addresses` (new): if `host` is an IP literal, validate it directly and return it (no lookup). Otherwise call the resolver for A and AAAA answers (`socket.SOCK_STREAM`), keep the unique addresses in answer order, raise `AddressRejectedError(kind="resolution_failed")` on a resolver error or an empty answer, and raise `AddressRejectedError(kind="prohibited_address")` when any answer is not public (mixed answers are rejected as a whole). Return the tuple of validated addresses.
- The default resolver awaits `asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)` and maps `socket.gaierror` and `OSError` to resolution_failed.

### Details
- Public function names and the `kind` values are the contract that `bounded_fetch.py` (seq 02) and the search provider (seq 03) rely on.
- The address list returned to the caller is the one the connection must use; callers must not resolve again for the same hop.

### Companion test files
- `tests/mcp_servers/test_address_policy.py` (new)
  - Procedure: with a fake resolver, cover IPv4 loopback, private (10/8, 172.16/12, 192.168/16), link-local metadata (169.254.169.254), shared space (100.64/10), reserved, multicast, unspecified, IPv6 loopback and unique-local, IPv4-mapped prohibited and public forms, a public answer, a mixed public and prohibited answer, an empty answer, a resolver exception, and an IP-literal host. Write these tests first and confirm they fail before the module exists.
  - Validation: `uv run pytest tests/mcp_servers/test_address_policy.py`.

## Compatibility considerations
- New module; no existing caller. Behavior of the existing `_check_domain` IP-literal check is unchanged by this document.

## Security considerations
- Fail-closed on every ambiguous input (unparseable, empty, failed resolution, mixed answers). Messages do not echo the resolved address list. The module performs only a name lookup and no outbound connection.

## Rollback considerations
- N/A: revert the commit; nothing else imports the module until seq 02 lands.

## Validation plan
- `uv run pytest tests/mcp_servers/test_address_policy.py`; `uv run ruff format scripts/mcp_servers/address_policy.py tests/mcp_servers/test_address_policy.py`, `uv run ruff check` on both, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/mcp_servers/address_policy.py -c pyproject.toml`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Every prohibited class, mapped form, mixed answer, empty answer, and failed resolution raises the expected `kind`; a public answer returns the validated tuple; the module imports only the standard library; all validation commands pass.

## Out of Scope
- Connection pinning, redirects, status and content handling, limits, web search error mapping, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the module described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion tests first, then confirm they pass | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (resolve all answers and fail closed), `REQ-008` (reusable module)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/address_policy.py`, `tests/mcp_servers/test_address_policy.py`
