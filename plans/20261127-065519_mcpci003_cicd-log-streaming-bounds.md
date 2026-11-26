# Plan: Stream, bound, and structure CI/CD workflow log retrieval

## Goal
- Make `get_workflow_logs` download through the shared bounded streaming helper under independent raw and decompressed limits, enforce one exact final-output byte budget, and return a structured per-job result with an explicit `partial_success`.

## Priority
High

## Scope
- **In-Scope**: the bounded streaming call for job logs; the trusted-GitHub-host policy and the maximum redirect count; the independent raw and decompressed byte limits; the exact final-output byte budget including headers and truncation markers; UTF-8-safe truncation; the per-job status model with `partial_success`; the totals; the tool error when every job fails; the affected tests; the CI/CD documentation record.
- **Out-of-Scope**: dispatch reconciliation (mcpci002); error mapping and audit coverage (mcpci004); changes to the shared helper itself, which is already implemented by mcpws001.
- **Dependencies**: mcpci001 (must be implemented first); mcpws001 is closed and its helper is implemented. mcpci002 can run in parallel.
  - **Depends on**: `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` | phase all | this Plan builds its response model on mcpci001's strict request models and its hard maximum values, and uses the lifespan-owned client mcpci001 injects for the jobs API call.
  - **Depends on**: `plans/done/20261126-114539_mcpws001_websearch-fetch-network-boundary.md` | phase 2 | the shared bounded streaming helper this Plan calls; already implemented, so the dependency is satisfied.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 7).

Evidence (`Explicit in code`, verified in Step 2 against `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`): the log request uses `follow_redirects=True` (line 85), reads `log_resp.text` in full (line 89), and records a failure as the string `(log fetch failed: HTTP {status})` inside the output (line 91). Raw transport exception text is also embedded as `(log fetch error: {e})` (line 102). Truncation decodes with `errors="replace"` (line 121), so replacement characters can appear. Test expectations that allow overrun are from the backlog and `Needs confirmation`; two existing tests pin that behavior (see `Tests`).

The shared bounded streaming helper named by the Issue exists: `scripts/mcp_servers/bounded_fetch.py` (`fetch_bounded`, `FetchLimits`, `BoundedFetchResult`), created by mcpws001 and used by `scripts/mcp_servers/web_search/search_provider.py`.

## Problem
The output limit applies only after full download and assembly, so it does not bound network, decompressed size, or memory; redirects are unrestricted; per-job failures are embedded as text while the overall result stays successful. The header of a job is appended even when it no longer fits, so the final output can exceed `max_log_size_kb`.

## Reason for Change
Resource control and result-contract correctness for a High-priority CI/CD feature; follows the credential and client lifecycle work.

## Implementation Intent
Stream with raw-download and decompressed limits, restrict redirects to documented GitHub-controlled hosts, enforce one exact final byte budget including headers and markers, keep UTF-8 boundaries, and return job-level status with an explicit `partial_success`.

## Requirements
- `REQ-001`: job log retrieval calls the shared bounded streaming helper (`scripts/mcp_servers/bounded_fetch.py`) with a trusted-GitHub-host policy and a maximum redirect count; the CI/CD-specific part is the per-job log byte budget.
- `REQ-002`: raw bytes read from the network and bytes produced by content decoding are bounded independently, before any full buffering of the response.
- `REQ-003`: one exact final-output byte budget including job headers and truncation markers; a job is not added when its header does not fit; truncation preserves complete UTF-8 characters.
- `REQ-004`: the result carries per-job status, included bytes, error code, and truncation state, plus `partial_success`; a tool error is returned when every job fails; raw transport exception text never appears in the result.
- `REQ-005`: the result carries totals — jobs, included jobs, failed jobs, downloaded bytes, visible bytes, truncation reason.
- `REQ-006`: the final output never exceeds `max_log_size_kb` in bytes, and tokens and raw upstream text never appear in results.
- `REQ-007`: documentation records the download, decompressed, selected-job, and returned-output limits, the redirect policy and trusted hosts, and the complete, partial, and error result contract.

## Implementation Target Files
**Freeze status**: Frozen (Step 8's Implementation Target Files Validation passed:
`tools/audit_plan_target_paths.py` 0 findings, `tools/check_plan_target_overlaps.py`
compatible overlap with the open mcpci001 plan and the frozen mcpci002 plan,
`tools/check_workitem_structure.py` no findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as the modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | Modify | Fetch each job log through `fetch_bounded` with the raw and decompressed limits, the trusted-host policy, and the maximum redirect count; enforce the exact final byte budget including headers and markers; truncate at UTF-8 character boundaries; record per-job status, included bytes, error code, and truncation state instead of embedded failure text | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, AC-1, AC-2, AC-3, AC-4 | Lines 82-104 use `follow_redirects=True` and read `log_resp.text` in full, and append `(log fetch failed: HTTP {status})` and `(log fetch error: {e})` as output text; lines 117-127 truncate with `errors="replace"`; lines 169-181 append the header before checking the budget (checked in Step 2) | `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Add the log response model: per-job status, included bytes, error code, truncation state, `partial_success`, and the totals; add the raw and decompressed limit constants | REQ-002, REQ-003, REQ-004, REQ-005, AC-4 | Lines 133-140 define only `GetWorkflowLogsRequest`; the module has no response model and no byte-limit constants beyond `max_log_size_kb` in `CicdConfig` (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | Modify | The `CiBackend` Protocol declares `get_workflow_logs` returning the structured result instead of `str` | REQ-004, AC-4 | Line 63 declares `async def get_workflow_logs(...) -> str` in the Protocol that the composite backend and the handler are typed against (checked in Step 3) | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (reference) | Verified |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Modify | The delegation carries the structured result instead of a string | REQ-004, AC-4 | Lines 74-76 delegate to the job backend and return its value unchanged (checked in Step 3) | `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | `handle_get_workflow_logs` returns the serialized structured result and returns a tool error when every job failed | REQ-004, AC-4 | Lines 120-132 return the backend string unchanged; there is no all-failed branch (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Verified |
| `config/cicd_mcp_server.toml` | Modify | Document the raw-download and decompressed byte limits, the maximum redirect count, and the trusted GitHub log hosts the code enforces | REQ-001, REQ-002, REQ-007 | The file has `max_log_size_kb = 256` with no stated maximum and no download, decompressed, or redirect keys (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Modify | Write the byte-budget and untrusted-redirect tests first, and replace the tests that pin string-embedded failures and an overrun-allowing budget | REQ-001, REQ-002, REQ-003, REQ-004, AC-1, AC-2, AC-3, AC-4 | Lines 48 and 72 pin the embedded `(log fetch failed: HTTP 404)` and `(log fetch error:` strings; line 103 pins `result_bytes >= max_bytes`, which allows the output to exceed the budget (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Replace the overrun-allowing assertion with the exact byte budget, and add the UTF-8-boundary, mixed-failure, and all-failed cases | REQ-003, REQ-004, AC-2, AC-4 | Line 525 asserts `len(result.encode()) <= 1024 + 100`, which permits exceeding the limit (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Add the response-model shape tests for the per-job fields, `partial_success`, and the totals | REQ-004, REQ-005, AC-4 | Lines 35-54 pin the request schema shape only; no response model is pinned (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Modify | The delegation test returns the structured result instead of the header string | REQ-004, AC-4 | Lines 146-151 pin `composite._job.get_workflow_logs.return_value = "=== Job: build ==="` and the returned string (checked in Step 3) | this file | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Record the four limits, the redirect policy and trusted hosts, and the complete, partial, and error result contract | REQ-007 | Line 63 states only that log retrieval is bounded by a job count limit and a total size limit (`max_log_size_kb`) (checked in Step 3) | `uv run python tools/check_docs_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure): one row per file; test, configuration, and
documentation files carry their own rows; `Validation Status` is `Verified` for every row.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob pattern, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/bounded_fetch.py` | `fetch_bounded`, `FetchLimits`, `BoundedFetchResult`, and the decoder and redirect errors the job backend calls; `FetchLimits.returned_bytes` is carried, not enforced, so the exact output budget stays the caller's responsibility | REQ-001, REQ-002, REQ-003 |
| `scripts/mcp_servers/address_policy.py` | `resolve_public_addresses` and `AddressRejectedError`, the host and address policy `fetch_bounded` applies on every hop | REQ-001, AC-3 |
| `scripts/mcp_servers/web_search/search_provider.py` | The existing production caller of `fetch_bounded`, the pattern for the host policy and allowed content types | REQ-001 |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | `_GITHUB_API_BASE`, `_MAX_JOBS_FOR_LOGS`, and `build_auth_headers` reused by the log call | REQ-001 |
| `scripts/mcp_servers/cicd/exception_handlers.py` | The existing error-to-HTTP mapping that the all-failed tool error must not change | REQ-004 |
| `scripts/mcp_servers/dispatch.py` | The handler contract `Callable[[ToolArgs], Awaitable[str]]` the serialized result is returned through | REQ-004 |
| `tests/mcp_servers/test_bounded_fetch.py` | The helper's existing pinned behavior; the log tests must not re-implement it | REQ-001, REQ-002 |
| `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Pins the cicd tool inventory and request schema shape, both unchanged by this Plan | REQ-004 |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Pins the dispatch-table wiring for `get_workflow_logs` | REQ-004 |
| `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Also pins the non-2xx fail-fast behavior on the jobs path, which this Plan must not alter | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-002): network and decompressed data are bounded before full buffering.
- `AC-2` (REQ-003, REQ-006): final output never exceeds the byte limit; UTF-8 truncation introduces no replacement characters.
- `AC-3` (REQ-001): redirects outside trusted GitHub hosts are rejected.
- `AC-4` (REQ-004, REQ-005): complete, partial, and total failure are machine-distinguishable, and raw exception strings are absent.
- `AC-5` (REQ-007): the CI/CD documentation records the four limits, the redirect policy and trusted hosts, and the complete, partial, and error result contract.

## Tests
- `REQ-001`/`REQ-002`/`REQ-003`: huge single-job log, many jobs, header-only budget exhaustion, trusted and untrusted redirects, compressed and chunked responses, UTF-8 boundary truncation — written first in `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`.
- `REQ-004`/`REQ-005`: mixed and all-failed cases and the totals, in `tests/mcp_servers/cicd/test_cicd_mcp_service.py` and `tests/mcp_servers/cicd/test_cicd_models.py`.
- `REQ-004`: delegation returns the structured result, in `tests/mcp_servers/cicd/test_service_github_actions_composite.py`.
- Replace the tests that allow overrun or pin string-embedded exceptions: `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` lines 48, 72, 103 and `tests/mcp_servers/cicd/test_cicd_mcp_service.py` line 525.
- Full validation sequence per `rules/toolchain.md`: ruff, mypy, bandit, lint-imports, the full test suite, diff-cover, pre-commit.

## Documentation Impact
Yes. Per `docs/00_index.md`'s "Document References by Task" (MCP server spec domain), the
per-server document `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` is the target row: the
download, decompressed, selected-job, and returned-output limits; the redirect policy and
trusted hosts; the complete, partial, and error result contract (REQ-007).

## Assumptions
- The raw-download and decompressed byte limits and the maximum redirect count are module constants in `scripts/mcp_servers/cicd/cicd_models.py`; `config/cicd_mcp_server.toml` documents them. If the owner makes them configuration, the Plan is amended with the config row already present.
- The handler contract stays `-> str` (the structured result is JSON-serialized), so `dispatch_tool` and the audit `outcome` mapping are unchanged.
- The log path calls `fetch_bounded` directly; the helper owns its own short-lived client per call, while the jobs API call keeps the injected client. The shared client's private transport is not reached.
- `text/plain` is the only allowed content type for the job log endpoint.
- Compatible overlap with mcpci001 on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `config/cicd_mcp_server.toml`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci001 owns the strict request models, hard maximums, and the lifespan-owned client; this Plan owns the log response model, the streaming bounds, and the result contract.
- Compatible overlap with mcpci002 on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci002 owns the dispatch response contract, this Plan owns the log response contract; the two touch different functions in the same files.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The list of trusted GitHub log hosts and the redirect maximum | No host list exists in the repository; the log endpoint redirects to storage hosts outside `api.github.com` | Decide from GitHub documentation or observed behavior; stop and report if the list cannot be determined (per the Issue's AI Implementation Instruction) | False |
| UNK-02 | The raw and decompressed byte limit values | No existing bound in `scripts/mcp_servers/cicd/` or `config/cicd_mcp_server.toml` | Decide at implementation; recorded as constants unless the owner makes them configuration | False |
| UNK-03 | mcpci001 is open: its plan has no `Completed` row | `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` is `Frozen` with all steps `Pending` | Complete mcpci001 before this Plan is implemented; this Plan's response model and its client seam depend on it | True |
| UNK-04 | Test expectations that allow overrun are from the backlog and `Needs confirmation` | The two existing assertions pin the current overrun behavior | Treat them as the characterization baseline to be replaced; the Issue's Acceptance Criteria are the target contract | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | Modify | Medium — imported by the composite facade and three test modules | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Medium — imported by six cicd modules and five test modules, and by the `agent-mcp-config-models` import-linter contract | 1 | 2 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | Modify | Medium — the `CiBackend` Protocol read by the service, the composite facade, and the init factory | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Modify | Low — the composite facade and one test module | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | Medium — the dispatch handler reached through the dispatch table and the server endpoint | 0 | 1 | not applicable (rsynced) |
| `config/cicd_mcp_server.toml` | Modify | Low — documentation-only row; read by `CicdConfig.load` and the shipped-config test | 3 | 2 | not applicable (already listed in deploy.sh:164) |
| `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Modify | Low | 0 | 2 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Low | 0 | 2 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Modify | Low | 0 | 1 | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Low | 3 | 2 | not applicable (rsynced) |

## Design
Path B analysis (four dimensions, `workflow-path-b.md`):

- **Architecture**: the import-linter contracts keep `shared` a leaf and forbid `agent` from
  importing `mcp_servers.cicd.cicd_models` (`agent-mcp-config-models`). `mcp_servers.cicd`
  calling `mcp_servers.bounded_fetch` and `mcp_servers.address_policy` stays inside the
  `mcp_servers` root package, so no contract is affected. No shared vocabulary module is
  changed, and the helper itself is not modified.
- **Dependency graphing**: `cicd_models.py` is the hub (six cicd importers, five test importers);
  `cicd_service_github_actions_job.py` has one production importer (the composite facade) and
  three test importers; `cicd_service_defs.py` is read by the service, the facade, and the init
  factory; `cicd_service_business.py` is reached only through the dispatch table. Blast radius is
  Medium for the hub, the Protocol, and the handler, Low for the facade and tests.
- **Historical**: churn over 30 days is 0-3 commits per target file; bus factor 1-2. The log path
  has not changed recently, so the result-contract change is a fresh contract, not a contested one.
- **Operational dependency inspection**: `uv run pip-audit` reports no finding for `httpx` or
  `zlib`-backed decoding, the packages the streaming path uses. Port 8012 has no listener at the
  time of the check.

Consumer scan (`tools/scan_change_consumers.py --seed get_workflow_logs`, candidates only):
- `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`, `cicd_models.py`,
  `cicd_service_defs.py`, `cicd_service_github_actions_composite.py`, `cicd_service_business.py`:
  target rows.
- `scripts/mcp_servers/cicd/cicd_tools.py`, `scripts/shared/tool_constants.py`: `not affected` —
  they pin the tool name and the read-tool inventory, which this Plan does not change.
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `test_mcp_cicd_edge_cases.py`,
  `test_cicd_models.py`, `test_service_github_actions_composite.py`: target rows.
- `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`,
  `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/shared/test_route_resolver.py`,
  `tests/mcp_servers/file/test_mcp_tools_validation.py`: `not affected` — they pin the tool
  inventory, the routing entry, or the request schema, none of which this Plan changes.
- `docs/22_mcp/mcp_01_tool_ownership_matrix.md`: `not affected` — it lists the tool and its tier,
  not the result contract. ADR citations in `docs/10_adr/adr_01_index.md` and
  `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`: `not affected` —
  they cite routing tests, not the log result contract.

Predictable fallout check:
- Module size: every target file is below the 24576 B gate (largest 28860 B is
  `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, a test file; the largest production target is
  6726 B, `cicd_service_github_actions_job.py`); `not affected: no split row required`.
- Pinned counts: `tests/mcp_servers/cicd/test_cicd_models.py` pins the request schema shape and is
  a target row; `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` pins the tool
  inventory, which is unchanged.
- Tool inventory: no tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected.
- Generated blocks: no generated-reference domain is touched.

Design decisions (Path B):
- **Byte-budget ownership**: `FetchLimits.returned_bytes` is carried by the helper and not enforced
  there, so the exact final-output budget — headers, log bytes, and the truncation marker — is
  enforced by the job backend. Alternative rejected: relying on the helper's limit, which would
  leave the header and marker outside the budget and keep the current overrun.
- **Client seam**: the log path calls `fetch_bounded` directly, which owns a short-lived client per
  call, while the jobs API call keeps the injected client. Alternative rejected: passing the shared
  client's private transport to the helper, which reaches an internal attribute and would couple the
  log path to mcpci001's client internals.
- **Error carrier**: per-job failure is reported as an error code in the response model, not as text
  appended to the output. Alternative rejected: keeping the string form, which cannot be
  distinguished from log content and leaks raw transport exception text.
- **UTF-8 boundary**: truncation cuts at a character boundary of the bounded decoder output rather
  than slicing bytes and decoding with `errors="replace"`. Alternative rejected: byte slicing with
  replacement decoding, which produces the replacement characters AC-2 forbids.

## Implementation steps

1. **Phase 1: Characterization tests first**
   - [ ] Write the byte-budget, header-only exhaustion, untrusted-redirect, compressed and chunked, and UTF-8-boundary tests before any code change (REQ-001, REQ-002, REQ-003; `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`)
   - [ ] Stop and report if the trusted-host list cannot be determined from GitHub documentation or observed behavior (UNK-01; per the Issue's AI Implementation Instruction)
2. **Phase 2: Log response model and limits**
   - [ ] Add the per-job response model, `partial_success`, the totals, and the raw and decompressed limit constants (REQ-002, REQ-004, REQ-005; `scripts/mcp_servers/cicd/cicd_models.py`)
   - [ ] Add the response-model shape tests (REQ-004, REQ-005; `tests/mcp_servers/cicd/test_cicd_models.py`)
3. **Phase 3: Bounded streaming and exact byte budget**
   - [ ] Fetch each job log through `fetch_bounded` with the host policy, the redirect maximum, and the independent limits; enforce the exact final budget including headers and markers; truncate at UTF-8 boundaries; record per-job status, included bytes, error code, and truncation state (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006; `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`)
4. **Phase 4: Handler and delegation contract**
   - [ ] Change the `CiBackend` Protocol to the structured result (REQ-004; `scripts/mcp_servers/cicd/cicd_service_defs.py`)
   - [ ] The composite delegation carries the structured result (REQ-004; `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`)
   - [ ] `handle_get_workflow_logs` returns the serialized result and a tool error when every job failed (REQ-004; `scripts/mcp_servers/cicd/cicd_service_business.py`)
   - [ ] Replace the overrun-allowing and string-embedded-failure tests and add the mixed and all-failed cases (REQ-003, REQ-004; `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`)
5. **Phase 5: Configuration record**
   - [ ] Document the raw, decompressed, selected-job, and returned-output limits, the redirect maximum, and the trusted hosts (REQ-002, REQ-007; `config/cicd_mcp_server.toml`)
6. **Phase 6: Documentation**
   - [ ] Record the four limits, the redirect policy and trusted hosts, and the complete, partial, and error result contract (REQ-007; `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`)
7. **Phase 7: Deployment & Verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md` and hand off to `skills/deploy/SKILL.md`; the prerequisite is that the change is committed and pushed first, and deploying is the user's decision (REQ-001..REQ-007; all target files)

### Release units
**Unit**: structured log result contract | **Phases**: 3, 4 | **Reason**: the backend, Protocol, facade, and handler return-contract change breaks the pinned string assertions in `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`, and `tests/mcp_servers/cicd/test_service_github_actions_composite.py` until those tests are replaced in the same commit, so neither phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Unit — response-model shape and limit constants | `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` | Per-job fields, `partial_success`, and the totals are pinned |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | Unit — fake transport and resolver, no live GitHub call | `uv run pytest tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Raw and decompressed bytes are bounded before buffering; the final output never exceeds the budget; no replacement characters; untrusted redirects rejected |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | Unit — Protocol contract | `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | The Protocol signature matches the backend and the tool inventory is unchanged |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Unit — delegation | `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_composite.py` | The structured result passes through unchanged |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Unit — handler, mixed and all-failed cases | `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Complete, partial, and total failure are machine-distinguishable; no raw exception text |
| `config/cicd_mcp_server.toml` | Unit — shipped-config test | `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py` | The config still parses and the documented values match the constants |
| All target files | Full sequence | `uv run python tools/run_validation_gates.py` | ruff, mypy, bandit, lint-imports, the full suite, diff-cover ≥ 90%, pre-commit pass |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Structure check | `uv run python tools/check_docs_structure.py` | No findings |

## Risks
- **Risk**: the trusted GitHub log host list is not documented in the repository, so the redirect policy cannot be enforced → **Mitigation**: decide from GitHub documentation or observed behavior and stop and report if it cannot be determined (Phase 1, UNK-01).
- **Risk**: the exact byte budget including headers and markers changes the output shape that existing tests pin → **Mitigation**: the tests are replaced in the same release unit (Phases 3 and 4), and the characterization tests are written first.
- **Risk**: streaming with a decompressed limit can fail on a chunked or compressed response that the current full-buffer path handled → **Mitigation**: the compressed and chunked cases are tested in Phase 1; the helper's decoder errors are mapped to per-job error codes, not raw text.
- **Risk**: the helper creates its own short-lived client per call, so the log path does not reuse the lifespan-owned client mcpci001 introduces → **Mitigation**: recorded as a design decision; only the jobs API call uses the injected client, and the helper's per-call client is its documented behavior.
- **Risk**: UTF-8 boundary truncation can leave a partial character at the budget edge and change the byte count → **Mitigation**: the budget is counted in bytes after decoding, and the marker is included in the budget (REQ-003, AC-2).
- **Risk**: mcpci001 may not be implemented when this Plan is consumed, so the strict models and hard maximum values it provides are absent → **Mitigation**: recorded as the blocking dependency UNK-03; implementation stops until it completes.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Characterization tests first (`tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`) | Pending | — | — | — |
| 2 | Log response model and limits (`scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`) | Pending | — | — | — |
| 3 | Bounded streaming and exact byte budget (`scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`) | Pending | — | — | — |
| 4 | Handler and delegation contract (`scripts/mcp_servers/cicd/cicd_service_defs.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`) | Pending | — | — | — |
| 5 | Configuration record (`config/cicd_mcp_server.toml`) | Pending | — | — | — |
| 6 | Documentation (`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`) | Pending | — | — | — |
| 7 | Deployment & Verification | Pending | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-065519
- **Evidence revision**: 30c08e72260ab00936fc442cd1646cb12aebb896
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`, `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_service_defs.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `config/cicd_mcp_server.toml`, `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Unresolved Questions (UNK-01) | `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | 3 | AC-3 | `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; Unresolved Questions (UNK-02) | `scripts/mcp_servers/cicd/cicd_models.py` | 2 | AC-1 | `tests/mcp_servers/cicd/test_cicd_models.py` | Needs confirmation |
| REQ-002 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | 3 | AC-1 | `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; Documentation Impact | `config/cicd_mcp_server.toml` | 5 | AC-1 | `uv run pytest tests/mcp_servers/test_shipped_dedup_config.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | 3 | AC-2 | `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/cicd_models.py` | 2 | AC-4 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_defs.py` | 4 | AC-4 | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (reference) | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | 4 | AC-4 | `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_business.py` | 4 | AC-4 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-004 | Problem; Testing Expectations | `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | 1 | AC-4 | this file | Confirmed by repository evidence |
| REQ-005 | Required Changes | `scripts/mcp_servers/cicd/cicd_models.py` | 2 | AC-4 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-006 | Constraints | `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | 3 | AC-2 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | 6 | AC-5 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |