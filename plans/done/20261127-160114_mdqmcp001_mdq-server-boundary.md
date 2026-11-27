# Unify the MDQ server boundary: availability, dispatch, errors, audit, health, and startup configuration

## Goal
- Give `mdq-mcp` one fail-closed boundary in which discovery, execution, health, stats, error rendering, and audit all read the same validated configuration and availability result, so a tool shown as disabled cannot execute, public responses expose only authorized non-sensitive state, and every authenticated call emits exactly one redacted audit record.

## Priority
High

## Scope
- **In-Scope**:
  - One availability function used by both `/v1/tools` and `/v1/call_tool`, evaluated per tool name at call time; path-dependent tools disabled when no roots are authorized, `grep_docs` additionally when grep is configured off; disabled tools rejected before the handler with code `tool_disabled`.
  - Corrected `config_dependent` metadata for the MDQ tool entries.
  - Stats restricted to counts scoped to the currently authorized roots, with the raw `index_state` metadata dict removed and stats refused when no roots are authorized.
  - Health reporting limited to non-sensitive state codes: no absolute database path, no database-wide counts or timestamps, no configuration path in dependency text.
  - A closed MDQ domain error-code vocabulary with one documented transport policy and per-code retry guidance; no raw exception text, SQLite detail, or path in a client response.
  - Exactly one audit record per authenticated call, emitted from a single boundary; exception handlers render transport only.
  - Audit target and detail carry hashed query and regex values, root-relative path identifiers or hashes, and persisted path counts and root identities only.
  - Configuration loaded and validated once at startup and shared by service construction, authentication, health, and the posture gate; missing production configuration fails before bind; strict booleans; no paths or secrets in startup errors.
  - Documentation of the resulting contract.
- **Out-of-Scope**:
  - Search SQL construction and query cancellation (handled by the search-query-boundary issue).
  - File-processing outcome semantics (handled by the file-processing-outcomes issue).
  - FTS5 schema identity and readiness (handled by the schema-identity issue).
  - Authentication and malformed-HTTP behavior, which stay separate from domain-tool failures.
  - Approval-display data, which stays separate from persistent audit data.
  - Any change to the audit output of other MCP servers.
- **Dependencies**:
  - Blocks the search-query-boundary, file-processing-outcomes, and schema-scope-consistency issues; those plans must wait for this Plan's error-code and audit contract.
  - Depends on the completed web-search configuration and audit-redaction work for the shared audit-emission contract and redaction helper.
  - Depends on the completed GitHub read-security-boundary work for the shared strict configuration parsing primitives.
  - Depends on the completed CI/CD credential and configuration contract for the load-and-validate-once pattern before bind.
  - Reuses the HTTP-level test fixture of the completed GitHub HTTP contract-tests work.
  - The MDQ server contract is documented in the MCP domain docs named by `docs/00_index.md` "Document References by Task".
  - **Depends on**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md — phase all — the shared `AuditEmission` and redaction helper this Plan consumes are defined there.
  - **Depends on**: issues/20261119-140509_mcpai002_github-read-security-boundary.md — phase all — the strict configuration type primitives (`RULE_BOOL`, `ConfigFieldTypeError`) this Plan applies to `MdqConfig` are defined there.
  - **Depends on**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md — phase all — the pre-bind load-and-validate-once configuration pattern this Plan adopts is established there.
  - **Depends on**: issues/20261119-140517_mcpai010_github-http-contract-tests.md — phase all — the HTTP-level test fixture reused by the boundary tests is defined there.

## Background
The MDQ server answers the same question — "is this tool available, and what may this caller see?" — from four independent places: the tool list, the dispatch path, the health probe, and the stats tool. Each place reads configuration separately (`_load_auth_token()`, `MdqService.__init__()`, `health_check._collect_dependencies()`), and each applies a different rule. The issue this plan implements is the consolidated MDQ backlog item that defines the single boundary the later search, indexing, and schema work reuse.

Archived work already closed parts of this: the pre-bind security-posture gate (`issues/done/20261018-191517_mcp002_...`), the config-loader exception mismatch (`issues/done/20261029-012525_ebrev001_...`), and the import-time auth-token validation (`issues/done/20261026-220730_mcp003_...`). Re-verification against current source confirms those fixes are still in place: `require_auth_token()` runs before `attach_auth_middleware()`, and `_enforce_posture_gate()` refuses bind when the posture is not validated. The remaining gaps are the ones listed in Problem below.

## Problem
Verified against current source:

- `_mdq_tool_availability()` in `scripts/mcp_servers/mdq/mdq_server.py` takes `tool_name` but ignores it; it returns only the empty-`allowed_dirs` result. `/v1/tools` calls it with an empty name, and `/v1/call_tool` performs no availability check at all, so a tool reported as disabled can still execute.
- `grep_docs` is disabled only at execution time (`MdqService.grep_docs()` raises when `enable_grep` is false), while discovery reports it enabled — discovery and execution disagree.
- `MdqService.stats()` prints the whole `index_state` metadata dict built from `SELECT key, value FROM index_state`, with no filtering to the authorized roots.
- `health_check._collect_dependencies()` puts the absolute database path into `details["database"]` and into the `deps["db_file"]` text, reports database-wide counts through `details.update(index_stats)`, and writes the configuration exception message — which embeds the config path — into `deps["config"]`.
- `scripts/mcp_servers/mdq/mdq_tools.py` declares `config_dependent: False` for every tool, including the path-dependent ones.
- Audit is emitted from two places: `_mdq_error_handler()` and `call_tool()`. A call that fails in `extract_execution_context()` returns `CallToolResponse` with no audit record at all, so the exactly-one-record rule is violated on that path (not by double emission on the normal error paths, where only one site runs).
- `extract_audit_target()` persists raw query text, raw regex patterns, and raw absolute paths, truncated to 80 characters.
- `MdqService.__init__()` swallows configuration failures (`except (FileNotFoundError, KeyError, TypeError): mdq_cfg = {}`) and falls back to `MdqConfig` pydantic defaults plus `DEFAULT_DB_PATH`, so a missing production configuration still produces a running server with implicit values.
- `MdqConfig` accepts truthy strings for `enable_grep` rather than a strict boolean.

## Reason for Change
Information-disclosure and audit-integrity risk in a security-sensitive boundary. The corrected error-code, availability, and audit contract is the base the search, indexing, and schema work build on, so it must be settled before those plans are generated.

## Implementation Intent
One validated configuration result is produced once at startup and read by service construction, authentication, health, and the posture gate. One availability function, parameterized by tool name, answers both discovery and dispatch, and dispatch re-evaluates it at call time before the handler runs. Every authenticated call runs inside one `try/except/finally` boundary that emits exactly one audit record through the shared `AuditEmission` contract; exception handlers only render the transport response and never audit. Domain failures carry stable codes from a closed vocabulary and never expose raw exception text, SQLite detail, or paths. Public health and stats expose only authorized, non-sensitive state; administrator diagnostics stay on the existing runtime-availability diagnostics surface rather than a new one.

## Requirements
- `REQ-001`: One availability function shared by `/v1/tools` and `/v1/call_tool`, evaluated per tool name at call time; path-dependent tools are disabled when no roots are authorized and `grep_docs` additionally when grep is configured off; a disabled tool is refused before the handler with code `tool_disabled`; the `config_dependent` metadata is corrected for the MDQ tool entries.
- `REQ-002`: Stats reports only counts scoped to the currently authorized roots, omits the raw `index_state` metadata dict, and refuses the call when no roots are authorized.
- `REQ-003`: Health reports only non-sensitive state codes; the absolute database path, database-wide counts, database-wide timestamps, and the configuration path in dependency text are removed from the ordinary health body.
- `REQ-004`: A closed MDQ domain error-code vocabulary (validation, authorization, disabled tool, not found, database unavailable, consistency, timeout, unexpected) with one documented transport policy and per-code retry guidance; no raw exception text, SQLite detail, or path reaches a client response.
- `REQ-005`: Every authenticated call emits exactly one audit record from a single emission boundary; exception handlers render transport only and do not emit.
- `REQ-006`: Audit target and detail carry hashed query and regex values, root-relative path identifiers or hashes, and persisted path counts and root identities; raw absolute paths are never persisted.
- `REQ-007`: Production configuration is loaded and validated once and shared across service, authentication, health, and posture; missing production configuration is a pre-bind failure; defaults exist only in an explicit development or test path; booleans are strict; startup errors contain no paths or secrets.
- `REQ-008`: The resulting contract — availability and execution, public health and authorized stats, the error-code table, audit redaction and exactly-one-record behavior — is documented, and the contradictory statements about disabled tools and exception handling are removed.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Make `/v1/tools` and `/v1/call_tool` use one per-tool availability function, refuse a disabled tool before the handler with code `tool_disabled`, move audit to one `AuditEmission` boundary in `call_tool`, stop the exception handlers from emitting audit, render domain failures as stable codes, and read the shared startup configuration result | REQ-001, REQ-004, REQ-005, REQ-007, AC-1, AC-3, AC-4, AC-5 | `_mdq_tool_availability()` takes `tool_name` and ignores it; `/v1/tools` calls it with `""`; `call_tool()` has no availability check; the `ExecutionContextError` branch returns `CallToolResponse` with no audit record; `_mdq_error_handler()` calls `_audit_log()`; `call_tool()` calls `_audit_log()` again; `_enforce_posture_gate()` runs only under `__main__` | `tests/mcp_servers/mdq/test_mdq_server.py`, `tests/mcp_servers/mdq/test_mdq_disabled_tools.py`, `tests/mcp_servers/mdq/test_mdq_exception_audit.py`, `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Scope `stats()` counts to the currently authorized roots, drop the raw `index_state` metadata dict, refuse stats when no roots are authorized, and stop swallowing configuration failures in `__init__` in favor of the shared validated result | REQ-002, REQ-007, AC-2, AC-6 | `stats()` builds `index_metadata` from `SELECT key, value FROM index_state` and prints it; `__init__()` catches `(FileNotFoundError, KeyError, TypeError)` and falls back to `MdqConfig` defaults and the literal database path; `grep_docs()` gates on `enable_grep` at execution only | `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_read_authorization.py`, `tests/mcp_servers/mdq/test_mdq_config.py` | Verified |
| `scripts/mcp_servers/mdq/audit_target.py` | Modify | Replace raw query, regex, and absolute-path targets with hashed values and root-relative path identifiers, and carry persisted path counts and root identities instead of raw paths | REQ-006, AC-4 | `extract_audit_target()` returns `str(args.get("query"))`, `str(args.get("pattern"))`, and `str(paths[0])` truncated to 80 characters | `tests/mcp_servers/mdq/test_audit_target.py`, `tests/mcp_servers/test_mdq_audit.py` | Verified |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | Remove the absolute database path from `details` and from the `deps["db_file"]` text, remove database-wide counts and timestamps from the ordinary health body, stop writing the configuration exception message (which embeds the config path) into `deps["config"]`, and report readiness through non-sensitive state codes | REQ-003, AC-2 | `_collect_dependencies()` sets `details["database"]`, `deps["db_file"] = f"not found: {db_path}"`, `details.update(index_stats)`, and `deps["config"] = f"check failed: {e}"`; `DEFAULT_DB_PATH` supplies an implicit path | `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | Build the posture view from the shared validated startup-configuration result instead of re-reading configuration, and keep the posture checks reading only non-sensitive state | REQ-007, AC-6 | `build_mdq_posture()` and `configured_allowed_dirs()` take a config dict produced by `_collect_dependencies()`, which loads configuration independently | `tests/mcp_servers/mdq/test_mdq_security_validation.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Apply the strict configuration type primitives to `MdqConfig` (strict booleans, no value echo on failure) and remove the implicit production defaults so an explicit development or test path is the only source of defaults | REQ-007, AC-6 | `MdqConfig` declares pydantic field defaults for every key, including `enable_grep: bool = True`; `tests/mcp_servers/mdq/test_mdq_config.py::test_recognized_boolean_tokens_coerce` shows non-boolean values are accepted today | `tests/mcp_servers/mdq/test_mdq_config.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Set `config_dependent` to `True` for the tools whose availability depends on configuration | REQ-001, AC-1 | Every entry in `TOOL_LIST` declares `"config_dependent": False` | `tests/mcp_servers/test_tool_schema.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_error_codes.py` | Create | New file: the closed MDQ domain error-code vocabulary plus the mapping from the MDQ exception classes to codes; policy only, no I/O and no logging | REQ-004, AC-5 | Does not exist; `scripts/mcp_servers/mdq/` holds 18 files and none owns the error vocabulary (checked in Step 3); `CONTROL_ERROR_CODES` in `scripts/shared/mcp_call_state_contract.py` is closed to the control API and cannot carry domain codes | `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` | Verified |
| `scripts/mcp_servers/mdq/startup_config.py` | Create | New file: loads and validates the production configuration once and exposes the immutable result shared by service, authentication, health, and posture; startup errors name field paths only, never values, paths, or secrets | REQ-007, AC-6 | Does not exist; today three independent loads read configuration at import (`_load_auth_token()`, `MdqService.__init__()`, `health_check._collect_dependencies()`) (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` | Verified |
| `scripts/mcp_servers/audit.py` | Modify | Add the path-identifier helper MDQ needs (root-relative identifier or hash), because `mcp_servers` cannot import `agent.secrets_masker.redact_path()` under the import-linter contract; existing behavior for other servers stays unchanged | REQ-006, AC-4 | `scripts/mcp_servers/audit.py` exposes `hash_query_value()`, `redact_url()`, and `AuditEmission` but has no path helper; `redact_path()` exists only in `scripts/agent/secrets_masker.py`; `.importlinter` contract `mcp_servers-no-agent` forbids `mcp_servers → agent` (re-verified 20261127) | `tests/mcp_servers/test_audit_redaction.py` | Verified |
| `config/mdq_mcp_server.toml` | Modify | State explicitly the keys that `MdqConfig` currently supplies as defaults (`context_before`, `context_after`, `max_chars_per_match`, `max_outline_depth`, `sqlite_busy_timeout`) so production construction has no implicit default | REQ-007, AC-6 | The file lists 13 `MdqConfig` keys plus `auth_token` and `db_path` (re-verified 20261127); the five named above are absent and are supplied today by pydantic defaults | `tests/mcp_servers/mdq/test_mdq_config.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_server.py` | Create | New file: boundary tests for one availability function used by discovery and dispatch, per-tool evaluation, and re-evaluation at call time | REQ-001, AC-1 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none covers the discovery/dispatch availability agreement (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` | Create | New file: disabled-tool and stale-discovery tests through HTTP and programmatic dispatch, including `grep_docs` configured off | REQ-001, AC-1 | Does not exist; `grep_docs` is gated only inside `MdqService.grep_docs()` today, so no test can currently show discovery and execution agreeing (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_exception_audit.py` | Create | New file: exactly-one-audit tests for success and every error class, including the `ExecutionContextError` path that emits nothing today | REQ-005, AC-3 | Does not exist; `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` asserts `_audit_log` is called from the handler, which is the behavior being replaced (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/test_mdq_audit.py` | Modify | Add redaction tests with customer names, secrets, regexes, and absolute paths against the single emission boundary | REQ-005, REQ-006, AC-3, AC-4 | The file currently asserts audit `detail`/`error_type` are sourced from service metadata; it has no redaction assertions | itself | Verified |
| `tests/mcp_servers/mdq/test_audit_target.py` | Modify | Replace the raw-value target assertions with hashed and root-relative expectations | REQ-006, AC-4 | `test_query_only`, `test_returns_path`, `test_returns_pattern` assert the raw argument value is returned | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health.py` | Modify | Replace the database-path and global-count assertions with non-sensitive state-code expectations | REQ-003, AC-2 | `test_deny_all_reports_zero_count_and_true` and `test_non_empty_allowed_dirs_reports_count_and_false` assert the global counts that are being removed | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Modify | Update the body assertions that pin `details["database"]` and the schema-error text carrying the path | REQ-003, AC-2 | `test_mdq_health_endpoint.py` line 335 asserts `"database" in details`; the fixture classes assert `deps` messages | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Modify | Point the gate test at the shared startup-configuration result | REQ-007, AC-6 | The test builds the posture from a hand-made `schema_error` tuple, which `startup_config.py` replaces | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_service.py` | Modify | Update the stats assertions for root-scoped counts and the removed metadata dict | REQ-002, AC-2 | `test_mdq_service.py` asserts the FTS row count and stale count that stats currently reports database-wide | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_schema_migration.py` | Modify | Update the stats count tests to the authorized-root scope | REQ-002, AC-2 | `test_chunk_count_in_stats` and `test_document_count_in_stats` assert database-wide counts | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_read_authorization.py` | Modify | Add the stats-refusal test for the no-authorized-roots case and the shrink-the-allowlist behavior | REQ-002, AC-2 | `test_deny_all_returns_no_matches_not_unfiltered_scan` covers search only; no stats refusal test exists | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_config.py` | Modify | Replace the defaults-construction and boolean-coercion tests with strict-boolean and explicit-mode expectations | REQ-007, AC-6 | `test_all_defaults_construct_successfully` and `test_recognized_boolean_tokens_coerce` assert the behavior being removed | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` | Modify | Replace the degradation expectations with the pre-bind failure expectations | REQ-007, AC-6 | `test_load_auth_token_returns_empty_on_config_missing_error` asserts the fallback that must become a pre-bind failure | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` | Modify | Assert handlers render transport only and no longer emit audit; assert the stable codes in tool responses | REQ-004, REQ-005, AC-5 | Line 66 asserts `error_type == "database_error"` from the handler's `_audit_log` call | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` | Modify | Assert the closed code vocabulary and the exception-to-code mapping | REQ-004, AC-5 | The file asserts the exception hierarchy only, not codes | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Document the availability and execution contract, public health and authorized stats, the administrator diagnostics surface, the MDQ error-code table, and audit redaction with exactly-one-record behavior | REQ-008, AC-5, AC-6 | The doc states `call_tool` writes one record per call with `target` truncated to 80 characters and describes exception handlers as the audit site | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` | Modify | Remove the statement that `config_dependent` is `false` for the MDQ tools | REQ-008, AC-1 | The doc states `config_dependent` is `false` for the file servers, `mdq`, and `rag_pipeline` tools | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Record MDQ under the single lowercase-snake code vocabulary, and remove the statement that audit log functions are implemented within each server's dispatch handler, which contradicts the single-emission boundary | REQ-008, AC-5, AC-7 | Re-verified 20261127: the doc has no Error Type Vocabulary section and does not name MDQ as using exception-class names; that statement is in `docs/22_mcp/mcp_04_04_mdq.md` line 96 (its own row). The contradicting statement here is line 64: "Audit log functions are implemented within each server's dispatch handler." | `uv run python tools/check_docs_content_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/config_field_types.py` | Supplies `RULE_BOOL` and `ConfigFieldTypeError`, whose error text never echoes the configured value; `MdqConfig` must adopt them | REQ-007 |
| `scripts/shared/config_loader.py` | Defines `ConfigMissingError`, `ConfigParseError`, `ConfigReadError`, and the strict `load_all()` behavior the startup result must propagate | REQ-007 |
| `scripts/shared/config_errors.py` | Defines the config exception types whose messages embed the configuration path and must not reach startup output | REQ-007 |
| `scripts/shared/mcp_health_contract.py` | Owns the closed capability-state and degraded-reason vocabularies that health state codes must use | REQ-003 |
| `scripts/mcp_servers/health_response.py` | Owns the health body shape and the `ready` derivation; the health changes must stay inside its contract | REQ-003 |
| `scripts/mcp_servers/dispatch.py` | Defines `DispatchResult` and the rule that `ValueError` from handlers becomes an error result while other exceptions propagate to the transport layer | REQ-004 |
| `scripts/mcp_servers/web_search/web_search_server.py` | The reference implementation of the single-`AuditEmission` boundary and the `tool_disabled` rejection before the handler | REQ-001, REQ-005 |
| `scripts/mcp_servers/mdq/search.py` | Shows which MDQ exception classes the search path raises, so the code mapping covers them without changing search SQL (out of scope) | REQ-004 |
| `scripts/mcp_servers/mdq/db_schema.py` | Defines the `documents.source_path` column that root-scoped stats counts must filter on | REQ-002 |
| `scripts/shared/tool_constants.py` | `MDQ_TOOLS` is the pinned tool inventory that must stay identical to `TOOL_LIST` | REQ-001 |
| `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Pins `MDQ_TOOLS == TOOL_LIST` names; must keep passing after the metadata change | REQ-001 |
| `tests/mcp_servers/test_tool_schema.py` | Asserts `config_dependent` is present as a boolean for every tool module; the value change must stay compatible | REQ-001 |
| `tests/mcp_servers/_auth_headers.py` | The HTTP-level test fixture reused by the boundary tests | REQ-001, REQ-005 |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | States the transport policy: tool-level errors keep HTTP 200 with `is_error=true`; 4xx/5xx are transport-level | REQ-004 |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | States the status classification and retry classification the per-code retry guidance must match | REQ-004 |
| `deploy/deploy.sh` | Confirms `config/mdq_mcp_server.toml` is already copied to the deployed config directory, so no deploy change is needed | REQ-007 |

## Acceptance Criteria
- `AC-1` (REQ-001): A tool reported as disabled cannot be executed through HTTP or programmatic dispatch; `grep_docs` is disabled consistently when configured off; the `config_dependent` value matches the tool's actual dependency on configuration.
- `AC-2` (REQ-002, REQ-003): Normal stats and health expose no absolute source path, database path, or unauthorized-root count; shrinking the allowlist immediately removes prior-root information from both.
- `AC-3` (REQ-005): Every authenticated call emits exactly one audit record, including the malformed-execution-context path that emits none today.
- `AC-4` (REQ-006): Queries, regex patterns, absolute paths, and raw exception text are absent from persistent logs and client responses.
- `AC-5` (REQ-004): Every domain failure has a stable code from the closed vocabulary and documented retry semantics; no raw exception text, SQLite detail, or path appears in a response.
- `AC-6` (REQ-007): Missing production configuration fails before bind through one shared result; strict booleans reject non-boolean values; startup errors name field paths only.
- `AC-7` (REQ-008): The documentation names the availability and execution contract, the public health and authorized stats surface, the administrator diagnostics surface, the error-code table, and the exactly-one-record audit behavior, and no doc still claims MDQ uses exception-class names or that MDQ tools are configuration-independent.

## Tests
- `REQ-001`: `tests/mcp_servers/mdq/test_mdq_server.py` and `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` — direct disabled-tool and stale-discovery calls through HTTP and programmatic dispatch; the same availability result from both paths; `grep_docs` off.
- `REQ-002`: `tests/mcp_servers/mdq/test_mdq_read_authorization.py` — shared-database tests with authorized and unauthorized roots, stats refusal with no roots, and the shrink-allowlist case; `tests/mcp_servers/mdq/test_mdq_service.py` and `tests/mcp_servers/mdq/test_mdq_schema_migration.py` updated for root-scoped counts.
- `REQ-003`: `tests/mcp_servers/mdq/test_mdq_health.py` and `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` — leakage tests for the database path, global counts, global timestamps, and the configuration path in dependency text.
- `REQ-004`: `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` and `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` — closed vocabulary, exception-to-code mapping, and the no-raw-text assertion on every response.
- `REQ-005`: `tests/mcp_servers/mdq/test_mdq_exception_audit.py` — exactly one record for success and for every error class, including the `ExecutionContextError` path; `tests/mcp_servers/test_mdq_audit.py` — redaction tests with customer names, secrets, regexes, and absolute paths.
- `REQ-006`: `tests/mcp_servers/mdq/test_audit_target.py` — hashed query and pattern values, root-relative path identifiers, persisted counts and root identities.
- `REQ-007`: `tests/mcp_servers/mdq/test_mdq_config.py` and `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` — configuration precedence, missing configuration as a pre-bind failure, strict booleans.
- Full-suite validation: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest`, `uv run diff-cover coverage.xml --compare-branch=master` at or above 90% on changed lines, `uv run pre-commit run --all-files`.

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (MCP server spec row), the MCP domain docs must be updated:
- `REQ-008` drives the MDQ server contract doc: availability and execution, public health, authorized stats, the administrator diagnostics surface, the MDQ error-code table, and audit redaction with exactly-one-record behavior.
- `REQ-001` drives the tool-runtime availability metadata doc, which currently states that MDQ tools are `config_dependent: false`.
- `REQ-004` and `REQ-005` drive the audit-logging and errors doc: record MDQ under the single lowercase-snake code vocabulary and remove the statement that audit log functions are implemented within each server's dispatch handler. Re-verified 20261127: that doc has no Error Type Vocabulary section; the exception-class-name statement is in the MDQ server contract doc.
Contradictory statements about disabled tools and exception handling are removed. Doc content policy applies: the error-code table is a closed vocabulary (retain), while per-exception handling tables and implementation-location statements must not be added (`skills/DESIGN.md` Docs content policy). Run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- The single transport policy already documented for MCP servers is the one MDQ adopts: tool-domain failures return HTTP 200 with `is_error=true` and a structured code; exception handlers render only transport-level responses. No new transport behavior is introduced.
- The administrator diagnostic surface is the existing runtime-availability diagnostics (`RuntimeToolRegistry.diagnostics()`), which already carries `config_dependent`, `enabled`, and `disabled_reason`; no new surface is created.
- `mcp_servers` cannot import `agent`, so the path-identifier helper must live in `scripts/mcp_servers/audit.py`; adding it is additive and does not change any other server's audit output.
- Health body consumers read only the shared contract fields (`liveness`, `ready`, `degraded_reasons`, `capabilities`, `reason`); the removed `details` keys have no production consumer, only test assertions.
- "Defaults only in explicit development or test mode" is satisfied by removing implicit production defaults and making the test path supply explicit values; no new configuration key or mode flag is introduced.
- Cross-plan target overlaps recorded by `tools/check_plan_target_overlaps.py` (run 20261127): 20 findings name this plan. The earlier statement that the other plans "do not modify the files this plan owns" was wrong; they share target rows with it. All 20 are compatible section-level overlaps, not conflicts, and this plan executes first in the work order.
  - `scripts/mcp_servers/mdq/mdq_models.py` (7 plans): this plan removes the `MdqConfig` field defaults and applies the strict boolean primitive; the others add or rename DTO fields in different sections.
  - `config/mdq_mcp_server.toml` (mdqmcp003): this plan adds the five keys the defaults supply today; that plan renames `max_file_chars` to its byte unit. Different keys, and that plan states the rename must not be read as a strict-type change.
  - `scripts/mcp_servers/mdq/mdq_service.py` (5 plans): this plan owns the stats scope and the configuration source; mdqmcp003 owns context resolution and the size-limit attribute, mdqmcp004, mdqmcp007, mdqmcp008 their own behavior.
  - `scripts/mcp_servers/mdq/health_check.py` (mdqmcp004, mdqmcp006): this plan removes the non-sensitive `details` keys; those plans add stale and schema-scope reporting.
  - `scripts/mcp_servers/mdq/mdq_server.py` (mdqmcp007, mdqmcp008): this plan owns the availability and audit emission boundary.
  - `scripts/mcp_servers/mdq/mdq_security_validation.py` (mdqmcp003, mdqmcp006): this plan changes the input source only; mdqmcp003 renames one key in `_MDQ_SCALAR_SETTINGS`.
  - `scripts/mcp_servers/mdq/mdq_tools.py` (5 plans): this plan changes only the `config_dependent` values.
  - `docs/22_mcp/mcp_04_04_mdq.md` (9 plans): this plan owns the availability, health, stats, error-code, and audit statements; the others add their own requirement statements.
  - `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` (mdqmcp010): this plan corrects the MDQ `config_dependent` sentence; that plan adds the status criteria and the status-change process.
  - Test modules shared with mdqmcp010 (`test_audit_target.py`, `test_mdq_config.py`, `test_mdq_config_error_degradation.py`, `test_mdq_error_taxonomy.py`, `test_mdq_exception_handlers.py`, `test_mdq_health.py`, `test_mdq_health_endpoint.py`, `test_mdq_health_posture.py`, `test_mdq_read_authorization.py`, `test_mdq_schema_migration.py`, `test_mdq_service.py`): that plan adds only a `pytestmark` line and a citation; this plan adds assertions.
- The overlap with the CI/CD error and audit-coverage plan on `scripts/mcp_servers/audit.py` and the audit-logging doc is compatible: that plan removes a duplicate `requested_target` assignment and records the CI/CD code vocabulary, while this plan adds a path-identifier helper and replaces the MDQ exception-class-name vocabulary entry. Neither changes the other's observable output.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the domain codes that today map to HTTP 503 (`database_unavailable`, `index_not_ready`) stay as transport-level statuses or move to the tool-level set, since the documented classification counts 5xx as transport failures and cools the health registry down | No owner decision recorded for MDQ; the documented tool-level set covers `400/403/404/409/422` only | Ask the transport-classification owner; the plan's default is the documented tool-level policy, so the implementation can proceed with tool-level codes and `is_error=true` | False |
| UNK-02 | Whether a separate administrator diagnostic surface is still required and how it is authenticated | No requirement names an admin surface beyond the existing runtime-availability diagnostics | Confirm with the MCP design-doc owner (`docs/00_index.md` MCP server spec row); the plan assumes the existing surface and creates none | False |
| UNK-03 | Existing consumers of the current health and stats fields | None remaining — resolved by the consumer scan | Resolved: `grimp` reports no production importer of any `mcp_servers.mdq` module, the agent reads only the shared health contract fields, and the only consumers of the removed fields are the tests listed in Implementation Target Files | False |
| UNK-04 | The mechanism for "explicit development or test mode" — no mode concept exists in `scripts/shared/config_loader.py` | No repository evidence of a mode flag or environment gate | Decide between the plan's default (no implicit defaults; tests supply explicit values) and a new config key; a new key would add a `deploy.sh` line and change the deployed config | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Highest: the only HTTP surface for MDQ; every tool call, every error response, and the audit record pass through it | 6 | 3 | N/A: no deploy.sh change; the module is copied by the scripts sync |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Medium: stats output and the configuration fallback; no external importer | 1 | 3 | N/A |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | Medium: the `/health` body read by the agent lifecycle layer through the shared contract | 1 | 3 | N/A |
| `scripts/mcp_servers/mdq/audit_target.py` | Modify | Low: audit record content only | 0 | 3 | N/A |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Medium: `MdqConfig` is the construction gate for the service | 0 | 2 | N/A |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Medium: the published tool metadata consumed by the runtime tool registry and the ownership matrix | 1 | 3 | N/A |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | Low: the startup posture view; the gate outcome is unchanged | 1 | 1 | N/A |
| `scripts/mcp_servers/mdq/mdq_error_codes.py` | Create | Medium: new closed vocabulary that the search, file-processing, and schema plans reuse | 0 | N/A: new file | N/A |
| `scripts/mcp_servers/mdq/startup_config.py` | Create | Medium: new single configuration source for service, auth, health, and posture | 0 | N/A: new file | N/A |
| `scripts/mcp_servers/audit.py` | Modify | High: shared by six MCP servers; the change is additive only | 5 | 3 | N/A |
| `config/mdq_mcp_server.toml` | Modify | Medium: deployed configuration; the added keys carry the values the defaults supply today | 3 | 2 | Yes — the file is copied by `deploy/deploy.sh`'s config section; no new `cp` line is needed |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Low | 2 | 2 | N/A |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Low | 5 | 2 | N/A |

## Design
**Single configuration source.** `scripts/mcp_servers/mdq/startup_config.py` loads and validates `mdq_mcp_server.toml` once and returns an immutable result consumed by service construction, `_load_auth_token()`, `_collect_dependencies()`, and `build_mdq_posture()`. Today three independent loads read the file at import, and each applies its own fallback. The new module is policy-only: no I/O beyond the loader call, no logging of values, and errors that name field paths only (`scripts/shared/config_field_types.py` already guarantees no value echo).

**Closed error vocabulary.** `scripts/mcp_servers/mdq/mdq_error_codes.py` owns the domain codes as a frozenset plus the mapping from the MDQ exception classes to codes. It stays separate from `CONTROL_ERROR_CODES` in `scripts/shared/mcp_call_state_contract.py`, which is closed to the control API. Codes use the lowercase-snake style the shared audit helper recommends. The transport policy is the documented one: tool-domain failures return HTTP 200 with `is_error=true` and the code; exception handlers render transport-level responses only. Retry guidance follows `docs/22_mcp/mcp_03_03_transport-and-health.md`: tool-level codes are not retried by the transport layer, and only the transport statuses `429/502/503/504` remain retryable. The `timeout` code is defined here but its behavior lands in the search plan.

**Single audit boundary.** `call_tool()` creates one `AuditEmission` and emits from its single `finally`, matching `scripts/mcp_servers/web_search/web_search_server.py`. Exception handlers stop calling `_audit_log()`. The `ExecutionContextError` branch, which emits nothing today, is covered by the same boundary.

**Path redaction.** `scripts/mcp_servers/audit.py` gains a path-identifier helper because `mcp_servers` cannot import `agent.secrets_masker.redact_path()` under the import-linter contract. It returns a root-relative identifier for a path inside an authorized root and a hash otherwise; `audit_target.py` uses it together with `hash_query_value()` for query and regex values.

**Consumer scan (Step 3).** `grimp` over `mcp_servers` reports 18 MDQ modules with no external importers: nothing outside `mcp_servers.mdq` imports `extract_audit_target`, `check_health`, `_mdq_tool_availability`, `stats`, or the tool metadata. The only consumers are the tests named in Implementation Target Files. `mcp_servers.audit` is imported by nine servers plus five test modules (re-verified 20261127), so its change is additive. No strong import cycle involves an MDQ module. `PYTHONPATH=scripts uv run lint-imports` passes today (6 contracts kept, 552 files).

**Predictable fallout check (Step 3).**
- Module size gate (24576 B): `mdq_server.py` 20547 B, `mdq_service.py` 15897 B, `scripts/mcp_servers/audit.py` 10267 B — all below the gate, so the plan's additions must keep them under it; the error-code and configuration vocabularies are placed in new modules to protect `mdq_server.py` headroom.
- Pinned inventory: `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` pins `MDQ_TOOLS == TOOL_LIST` names — unaffected by a metadata value change. `docs/22_mcp/mcp_01_tool_ownership_matrix.md` lists the 7 MDQ tools — unaffected.
- Tool inventory: `tests/mcp_servers/test_tool_schema.py` asserts `config_dependent` is present as a boolean for every tool module; changing the value from `False` to `True` stays compatible.
- Generated blocks: `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` carries a prose statement about MDQ's `config_dependent` value that must be corrected.

**Health shape.** Health keeps the shared contract shape (`make_health_response()` plus the capability block) and reports readiness through the closed capability-state vocabulary. The removed `details` keys are not part of the contract, so no consumer outside the tests breaks.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Write the failing leakage and exactly-one-audit tests before any production change (REQ-003, REQ-005, REQ-006; `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_exception_audit.py`, `tests/mcp_servers/test_mdq_audit.py`, `tests/mcp_servers/mdq/test_audit_target.py`)
   - [ ] Add the disabled-tool and stale-discovery tests that pin the current disagreement between discovery and dispatch (REQ-001; `tests/mcp_servers/mdq/test_mdq_server.py`, `tests/mcp_servers/mdq/test_mdq_disabled_tools.py`)
   - [ ] Add the stats scoping and stats-refusal tests (REQ-002; `tests/mcp_servers/mdq/test_mdq_read_authorization.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`)
2. **Phase 2: Shared vocabulary modules**
   - [ ] Create the closed domain error-code vocabulary and the exception-to-code mapping (REQ-004; `scripts/mcp_servers/mdq/mdq_error_codes.py`)
   - [ ] Create the single validated startup-configuration result (REQ-007; `scripts/mcp_servers/mdq/startup_config.py`)
   - [ ] Add the path-identifier helper to the shared audit module without changing existing behavior (REQ-006; `scripts/mcp_servers/audit.py`)
3. **Phase 3: Availability and dispatch boundary**
   - [ ] Make the availability function per-tool and shared by `/v1/tools` and `/v1/call_tool`, re-evaluated at call time, and refuse a disabled tool before the handler with code `tool_disabled` (REQ-001; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Correct `config_dependent` for the MDQ tool entries (REQ-001; `scripts/mcp_servers/mdq/mdq_tools.py`)
4. **Phase 4: Error rendering and single audit boundary**
   - [ ] Render domain failures through the code vocabulary and stop the exception handlers from emitting audit (REQ-004, REQ-005; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Move `call_tool()` audit to one `AuditEmission` emitted from a single `finally` (REQ-005; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Redact the audit target and detail (REQ-006; `scripts/mcp_servers/mdq/audit_target.py`)
5. **Phase 5: Authorized stats and non-sensitive health**
   - [ ] Scope stats counts to the current authorized roots, remove the raw `index_state` dict, and refuse stats with no roots (REQ-002; `scripts/mcp_servers/mdq/mdq_service.py`)
   - [ ] Remove the absolute database path, global counts, global timestamps, and the config path from health, and report readiness by state codes (REQ-003; `scripts/mcp_servers/mdq/health_check.py`)
6. **Phase 6: Configuration startup contract**
   - [ ] Make service construction consume the shared validated result and stop swallowing configuration failures (REQ-007; `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`)
   - [ ] Apply strict booleans and remove implicit production defaults from `MdqConfig` (REQ-007; `scripts/mcp_servers/mdq/mdq_models.py`)
   - [ ] State the currently-implicit keys explicitly in the configuration file (REQ-007; `config/mdq_mcp_server.toml`)
7. **Phase 7: Documentation and deployment verification**
   - [ ] Update the MCP domain docs named by `docs/00_index.md` "Document References by Task" for the availability contract, health and stats surfaces, the error-code table, and audit redaction (REQ-008; `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`)
   - [ ] Deployment verification: confirm `deploy/deploy.sh` already copies `config/mdq_mcp_server.toml` and that the deployed config matches the repository file after the added keys; no deploy.sh change is expected (REQ-007; `deploy/deploy.sh`)
   - [ ] Run the full validation sequence in `rules/toolchain.md` including `uv run python tools/check_module_size.py` and `uv run python tools/check_docs_content_policy.py`

### Release units
**Unit**: boundary-characterization-tests | **Phases**: 1, 3, 4, 5, 6 | **Reason**: the tests written in Phase 1 assert behavior that only lands in Phases 3 through 6, so Phase 1 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Integration (HTTP boundary) plus unit for the availability function | `uv run pytest tests/mcp_servers/mdq/test_mdq_server.py tests/mcp_servers/mdq/test_mdq_disabled_tools.py` | Discovery and dispatch report the same availability; a disabled tool is refused before the handler with code `tool_disabled` |
| `scripts/mcp_servers/mdq/mdq_service.py` | Unit with a shared database and mixed roots | `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_schema_migration.py tests/mcp_servers/mdq/test_mdq_read_authorization.py` | Counts are root-scoped; stats refused with no authorized roots; no raw metadata dict |
| `scripts/mcp_servers/mdq/health_check.py` | Unit plus HTTP endpoint integration | `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py tests/mcp_servers/mdq/test_mdq_health_posture.py` | No absolute path, global count, global timestamp, or config path in the body |
| `scripts/mcp_servers/mdq/mdq_error_codes.py` | Unit for the closed vocabulary and the mapping | `uv run pytest tests/mcp_servers/mdq/test_mdq_error_taxonomy.py tests/mcp_servers/mdq/test_mdq_exception_handlers.py` | Every domain failure resolves to a code in the closed set; responses carry no raw exception text |
| `scripts/mcp_servers/mdq/audit_target.py`, `scripts/mcp_servers/audit.py` | Unit for redaction plus exactly-one-record integration | `uv run pytest tests/mcp_servers/mdq/test_audit_target.py tests/mcp_servers/test_mdq_audit.py tests/mcp_servers/test_audit_redaction.py tests/mcp_servers/mdq/test_mdq_exception_audit.py` | Exactly one record per authenticated call; hashed values and root-relative identifiers only |
| `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/startup_config.py` | Unit for strict types and pre-bind failure | `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` | Non-boolean rejected; missing configuration fails before bind; no path or secret in the message |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Unit against the pinned inventory | `uv run pytest tests/mcp_servers/test_tool_schema.py tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | `config_dependent` boolean preserved; tool names still match `MDQ_TOOLS` |
| Architecture boundary | Contract check | `PYTHONPATH=scripts uv run lint-imports` | Passes; no `mcp_servers → agent` import introduced |
| Module size gate | Gate check | `uv run python tools/check_module_size.py` | No module crosses 24576 B |
| Static analysis | CI parity | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new errors; no high/medium unaddressed |
| Coverage | Diff coverage | `uv run diff-cover coverage.xml --compare-branch=master` | At or above 90% on changed lines |
| Documentation | Content policy | `uv run python tools/check_docs_content_policy.py` | No implementation-detail content introduced |

## Risks
- **Risk**: adding a path helper to `scripts/mcp_servers/audit.py` could change the audit output of the other eight servers that import it (re-verified 20261127; the previously recorded five was stale). → **Mitigation**: the change is additive (a new function only); `tests/mcp_servers/test_audit_redaction.py` is run unchanged, and the issue's instruction is to stop and report if another server's output changes.
- **Risk**: removing health `details` keys and changing stats output shape breaks consumers outside the tests. → **Mitigation**: the consumer scan found no production consumer of those fields; the agent reads only the shared health contract fields. If a consumer is found later, the change is scoped to the tests listed in Implementation Target Files.
- **Risk**: making `MdqConfig` reject implicit defaults breaks startup for a deployed configuration that relies on them. → **Mitigation**: Phase 6 adds the currently-implicit keys to `config/mdq_mcp_server.toml` with the same values, so production behavior is unchanged while the default path is removed.
- **Risk**: `mdq_server.py` is already near the module size gate and this plan adds the dispatch, error-rendering, and audit boundary to it. → **Mitigation**: the error-code and configuration vocabularies are placed in new modules; `uv run python tools/check_module_size.py` is run before commit, and `tools/module_nodes.py measure` identifies a split if the gate is crossed.
- **Risk**: moving the 503 domain codes to the tool-level set changes health-registry failure counts. → **Mitigation**: recorded as UNK-01; the plan adopts the documented tool-level policy and the change is validated by the health-posture tests before commit.
- **Risk**: the error-code contract is consumed by three later plans, so a late change here propagates. → **Mitigation**: the vocabulary is a closed frozenset in one module, and the later plans are sequenced after this one.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | In Progress | — | — | Tests written before production changes per the issue's instruction |
| 2 | Phase 2: shared vocabulary modules | In Progress | — | — | Error codes, startup config, audit path helper |
| 3 | Phase 3: availability and dispatch boundary | In Progress | — | — | Depends on Phase 2 codes |
| 4 | Phase 4: error rendering and single audit boundary | In Progress | — | — | Handlers render transport only |
| 5 | Phase 5: authorized stats and non-sensitive health | In Progress | — | — | Root-scoped counts |
| 6 | Phase 6: configuration startup contract | In Progress | — | — | Pre-bind failure |
| 7 | Phase 7: documentation and deployment verification | In Progress | — | — | Docs gates and deploy config check |

Plan Gap: no `Implementation steps` entry modifies `tests/mcp_servers/mdq/test_mdq_health_posture.py`, `tests/mcp_servers/mdq/test_mdq_config.py`, `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`, `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`, `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`. Each is covered by this cycle as a companion of the code row that cites it, except `test_mdq_config.py`, which keeps its own document because two code rows cite it.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-213547_01_scripts_mcp_servers_mdq_mdq_server.py.md` | 3, 4 | Procedure | Pending | — | — |
| `implementations/20261127-213547_02_scripts_mcp_servers_mdq_mdq_service.py.md` | 5, 6 | Procedure | Pending | — | — |
| `implementations/20261127-213547_03_scripts_mcp_servers_mdq_audit_target.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-213547_04_scripts_mcp_servers_mdq_health_check.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261127-213547_05_scripts_mcp_servers_mdq_mdq_security_validation.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261127-213547_06_scripts_mcp_servers_mdq_mdq_models.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261127-213547_07_scripts_mcp_servers_mdq_mdq_tools.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261127-213547_08_scripts_mcp_servers_mdq_mdq_error_codes.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-213547_09_scripts_mcp_servers_mdq_startup_config.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-213547_10_scripts_mcp_servers_audit.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-213547_11_config_mdq_mcp_server.toml.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261127-213547_12_tests_mcp_servers_mdq_test_mdq_server.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-213547_13_tests_mcp_servers_mdq_test_mdq_disabled_tools.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-213547_14_tests_mcp_servers_mdq_test_mdq_exception_audit.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-213547_15_tests_mcp_servers_test_mdq_audit.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-213547_23_tests_mcp_servers_mdq_test_mdq_config.py.md` | — (Plan Gap: no Implementation step modifies this path) | Procedure | Pending | — | — |
| `implementations/20261127-213547_27_docs_22_mcp_mcp_04_04_mdq.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261127-213547_28_docs_22_mcp_mcp_03_06_tool-runtime-availability-metadata.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261127-213547_29_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md.md` | 7 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md` (moved from `issues/` by commit `41b423e73`; corrected 20261127 by this pass's Step 3a)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-160114
- **Evidence revision**: 1ea69ed7f1415545ca2c75f531e8a9376939ddad
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/audit_target.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_error_codes.py`, `scripts/mcp_servers/mdq/startup_config.py`, `scripts/mcp_servers/audit.py`, `config/mdq_mcp_server.toml`, `tests/mcp_servers/mdq/test_mdq_server.py`, `tests/mcp_servers/mdq/test_mdq_disabled_tools.py`, `tests/mcp_servers/mdq/test_mdq_exception_audit.py`, `tests/mcp_servers/test_mdq_audit.py`, `tests/mcp_servers/mdq/test_audit_target.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_read_authorization.py`, `tests/mcp_servers/mdq/test_mdq_config.py`, `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`, `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`, `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `_mdq_tool_availability()` ignores `tool_name` in `scripts/mcp_servers/mdq/mdq_server.py` | `scripts/mcp_servers/mdq/mdq_server.py` | Phase 3 | AC-1 | `tests/mcp_servers/mdq/test_mdq_server.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; `grep_docs` gated only at execution in `scripts/mcp_servers/mdq/mdq_service.py` | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 3 | AC-1 | `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; `config_dependent: False` on every entry in `scripts/mcp_servers/mdq/mdq_tools.py` | `scripts/mcp_servers/mdq/mdq_tools.py` | Phase 3 | AC-1 | `tests/mcp_servers/test_tool_schema.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; direct disabled-tool and stale-discovery calls | `tests/mcp_servers/mdq/test_mdq_server.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; disabled tool through HTTP and programmatic dispatch | `tests/mcp_servers/mdq/test_mdq_disabled_tools.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Required Changes; raw `index_state` dict in `stats()` in `scripts/mcp_servers/mdq/mdq_service.py` | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 5 | AC-2 | `tests/mcp_servers/mdq/test_mdq_service.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; stats restricted to canonical paths inside current `allowed_dirs` | `tests/mcp_servers/mdq/test_mdq_read_authorization.py` | Phase 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria; counts must be root-scoped | `tests/mcp_servers/mdq/test_mdq_schema_migration.py` | Phase 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-003 | Required Changes; absolute database path in `details` and `deps["db_file"]` in `scripts/mcp_servers/mdq/health_check.py` | `scripts/mcp_servers/mdq/health_check.py` | Phase 5 | AC-2 | `tests/mcp_servers/mdq/test_mdq_health.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; global counts and timestamps removed from ordinary health | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Phase 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-004 | Required Changes; stable error codes and one documented transport policy | `scripts/mcp_servers/mdq/mdq_error_codes.py` | Phase 2 | AC-5 | `tests/mcp_servers/mdq/test_mdq_error_taxonomy.py` | Confirmed by repository evidence |
| REQ-004 | Problem; raw exception text via `JSONResponse({"detail": str(exc)})` and `CallToolResponse(result=str(exc))` | `scripts/mcp_servers/mdq/mdq_server.py` | Phase 4 | AC-5 | `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; central emission, exception handlers only render transport | `scripts/mcp_servers/mdq/mdq_server.py` | Phase 4 | AC-3 | `tests/mcp_servers/mdq/test_mdq_exception_audit.py` | Confirmed by repository evidence |
| REQ-005 | Correction to the issue: the `ExecutionContextError` path emits no record today | `tests/mcp_servers/mdq/test_mdq_exception_audit.py` | Phase 1 | AC-3 | itself | Confirmed by repository evidence |
| REQ-005 | Required Changes; use the shared audit-emission contract | `scripts/mcp_servers/audit.py` | Phase 2 | AC-3 | `tests/mcp_servers/test_audit_redaction.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; hashing queries and regex patterns, removing previews | `scripts/mcp_servers/mdq/audit_target.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_audit_target.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; root-relative identifiers or hashes for paths | `scripts/mcp_servers/audit.py` | Phase 2 | AC-4 | `tests/mcp_servers/test_mdq_audit.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; load and validate production configuration once and share the result | `scripts/mcp_servers/mdq/startup_config.py` | Phase 2 | AC-6 | `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` | Confirmed by repository evidence |
| REQ-007 | Problem; `MdqService.__init__()` swallows configuration failures | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 6 | AC-6 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; strict booleans | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 6 | AC-6 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; no paths or secrets in startup errors | `scripts/mcp_servers/mdq/mdq_security_validation.py` | Phase 6 | AC-6 | `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Confirmed by repository evidence |
| REQ-007 | Target Files or Areas; `config/mdq_mcp_server.toml` | `config/mdq_mcp_server.toml` | Phase 6 | AC-6 | `tests/mcp_servers/mdq/test_mdq_config.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; availability and execution contract | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 7 | AC-7 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; the `config_dependent` statement for MDQ tools | `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` | Phase 7 | AC-7 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; remove the exception-class-name audit vocabulary for MDQ | `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Phase 7 | AC-7 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-213547 -->